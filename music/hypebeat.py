"""hypebeat: MusicGen bed, conformed to an exact BPM grid, ready for numpy hits on top.

    kinetix music gen "hard phonk, cowbell, distorted 808" --bpm 150 --seconds 60 -o bed.wav

Writes bed.wav (44.1 kHz mono) and bed.json ({bpm, seconds, beats[]}); beat 0 is at t=0, so beat k
lands at k * 60/bpm and the numpy layer in hits.py can place drops, risers and stutters on the same grid.
"""
import argparse
import json
import sys
import time

import librosa
import numpy as np
import soundfile as sf

SR = 44100
CHUNK = 28.0      # MusicGen is trained on 30 s windows
OVERLAP = 6.0     # seconds of the previous chunk fed back as the continuation prompt


def load_model(name):
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    proc = AutoProcessor.from_pretrained(name)
    model = MusicgenForConditionalGeneration.from_pretrained(name, torch_dtype=torch.float16, low_cpu_mem_usage=True).to("cuda")
    return proc, model


def generate(proc, model, prompt, seconds, seed, prompt_audio=None):
    import torch
    torch.manual_seed(seed)
    sr = model.config.audio_encoder.sampling_rate
    rate = model.config.audio_encoder.frame_rate
    kw = dict(text=[prompt], padding=True, return_tensors="pt")
    if prompt_audio is not None:
        kw.update(audio=[prompt_audio], sampling_rate=sr)
    inputs = proc(**kw).to("cuda")
    if "input_values" in inputs:
        inputs["input_values"] = inputs["input_values"].half()
    with torch.no_grad():
        out = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=int(seconds * rate))
    y = out[0, 0].float().cpu().numpy()
    if prompt_audio is not None:
        y = y[len(prompt_audio):]  # the output repeats the prompt before continuing it
    return y, sr


MAX_STRETCH = 0.12  # beyond this the phase vocoder smears transients; keep the native tempo instead


def tempo_of(y, sr, target):
    """Tempo from onset autocorrelation peaks. librosa's beat_track misreads long phonk/club takes
    (it called a 150 bpm take ~199), while the autocorrelation peak lands on 150 or its half."""
    hop = 512
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    ac = librosa.autocorrelate(oenv - oenv.mean())
    lags = np.arange(1, len(ac))
    bpms = 60 * sr / (lags * hop)
    ok = (bpms > 55) & (bpms < 230)
    lags, bpms, w = lags[ok], bpms[ok], ac[1:][ok]
    best, best_w = 0.0, -np.inf
    for i in np.argsort(w)[-6:]:                       # strongest periodicities
        # refine the integer lag with a parabola through its neighbours
        j = lags[i]
        a, b, c = ac[j - 1], ac[j], ac[j + 1] if j + 1 < len(ac) else ac[j]
        off = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) else 0.0
        bpm = 60 * sr / ((j + off) * hop)
        cand = min((bpm * k for k in (0.5, 1, 2)), key=lambda x: abs(x - target))
        if abs(cand - target) / target <= MAX_STRETCH and w[i] > best_w:
            best, best_w = cand, w[i]
    if best == 0.0:  # nothing near the target: report the strongest periodicity honestly
        j = lags[np.argmax(w)]
        best = min((60 * sr / (j * hop) * k for k in (0.5, 1, 2)), key=lambda x: abs(x - target))
    return float(best)


def conform(y, sr, bpm):
    """Time-stretch to exactly `bpm` (within MAX_STRETCH) and trim so a beat sits at t=0.
    Returns (audio, measured_tempo, grid_bpm); grid_bpm is the native tempo when it was too far to stretch."""
    t = tempo_of(y, sr, bpm)
    if t > 0 and abs(t - bpm) / bpm <= MAX_STRETCH:
        y = librosa.effects.time_stretch(y, rate=bpm / t)
    elif t > 0:
        print(f"take is ~{t:.1f} bpm, too far from {bpm} to stretch cleanly; keeping its own tempo", file=sys.stderr)
        bpm = t
    period = 60.0 / bpm
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(onset, sr=sr)
    # pick the phase whose beat grid collects the most onset energy
    phases = np.linspace(0, period, 64, endpoint=False)
    score = [onset[np.searchsorted(times, np.arange(p, times[-1], period)).clip(0, len(onset) - 1)].sum() for p in phases]
    phase = phases[int(np.argmax(score))]
    return y[int(phase * sr):], t, bpm


def cmd_gen(a):
    proc, model = load_model(a.model)
    prompt = f"{a.prompt}, {a.bpm} bpm"
    # audition short takes and keep the seed whose natural tempo is nearest the target
    best = None
    for seed in range(a.seed, a.seed + a.candidates):
        y, sr = generate(proc, model, prompt, 8.0, seed)
        t = tempo_of(y, sr, a.bpm)
        err = abs(t - a.bpm) / a.bpm
        print(f"seed {seed}: ~{t:.1f} bpm ({err:+.1%} off)", file=sys.stderr)
        if best is None or err < best[1]:
            best = (seed, err)
    seed = best[0]
    print(f"using seed {seed}", file=sys.stderr)

    # the stretch shortens or lengthens the track, so generate enough raw audio to cover it
    need = a.seconds * (1 + best[1]) + 2
    t0 = time.time()
    y, sr = generate(proc, model, prompt, min(CHUNK, need), seed)
    while len(y) / sr < need:
        tail = y[-int(OVERLAP * sr):]
        more, _ = generate(proc, model, prompt, min(CHUNK, need - len(y) / sr + OVERLAP) , seed + 1000 + len(y), prompt_audio=tail)
        y = np.concatenate([y, more])
    print(f"generated {len(y) / sr:.1f}s in {time.time() - t0:.0f}s", file=sys.stderr)

    y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    y, raw_tempo, grid_bpm = conform(y, SR, a.bpm)
    y = y[: int(a.seconds * SR)]
    y = y / (np.abs(y).max() + 1e-9) * 0.9
    sf.write(a.out, y, SR)
    period = 60.0 / grid_bpm
    meta = {"prompt": prompt, "model": a.model, "seed": seed, "raw_bpm": round(raw_tempo, 2), "bpm": round(grid_bpm, 3), "asked_bpm": a.bpm,
            "seconds": round(len(y) / SR, 3), "beats": [round(k * period, 4) for k in range(int(len(y) / SR / period) + 1)]}
    with open(a.out.rsplit(".", 1)[0] + ".json", "w") as f:
        json.dump(meta, f, indent=1)
    print(f"wrote {a.out}: {meta['seconds']}s at {meta['bpm']} bpm (raw ~{raw_tempo:.1f})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen", help="generate a beat-locked music bed")
    g.add_argument("prompt")
    g.add_argument("--bpm", type=float, default=150)
    g.add_argument("--seconds", type=float, default=30)
    g.add_argument("--model", default="facebook/musicgen-small")
    g.add_argument("--candidates", type=int, default=4, help="seeds to audition for tempo")
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("-o", "--out", default="bed.wav")
    a = ap.parse_args()
    if a.cmd == "gen":
        cmd_gen(a)


if __name__ == "__main__":
    main()

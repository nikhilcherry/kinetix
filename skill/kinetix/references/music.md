# Kinetix music (`music/`)

## `kinetix music gen`: a bed locked to the grid

```bash
kinetix music gen "dark cyberpunk drift phonk, distorted 808, cowbell" --bpm 150 --seconds 60 [--seed 0 --candidates 4 --model facebook/musicgen-small] -o assets/bed.wav
```

1. **Audition:** generates short takes at several seeds and keeps the one whose tempo is nearest the target. MusicGen follows the bpm written in the prompt closely.
2. **Generate:** extends past MusicGen's ~30 s window by continuing chunk by chunk, feeding the last 6 s back as an audio prompt.
3. **Measure:** tempo comes from onset-autocorrelation peaks.
4. **Conform:** time-stretches to the exact bpm (capped at ±12%) and shifts so a beat sits at t = 0.
5. **Write:** `bed.wav` (44.1 kHz mono) plus `bed.json` (`bpm`, `beats[]`, seed, prompt, raw tempo).

**Cost:** about 30 s of GPU time for 60 s of music with musicgen-small (1.5 GB VRAM). CPU works, just slower. Output is CC-BY-NC.

## `hits.py`: production on the same grid

```python
import hits as h
from hits import Mix
m = Mix("assets/bed.wav", bed_gain=1.2, seconds=51.2)   # or Mix(bpm=150, seconds=19.2) for pure synth
B, BAR = m.period, 4 * m.period
```

| call | effect |
|---|---|
| `m.add(t, x, gain)` | sound effect layer (ducks a little under voice) |
| `m.drums(t, x, gain)` | music layer (ducks under voice) |
| `m.say(t, x, gain)` | voice layer; everything else ducks under it |
| `m.stutter(x, start, end, step)` | vocal chop: retrigger the head of `x` |
| `m.lowpass([(t, hz), ...])` | filter sweep over the bed, log-interpolated (muffled intro, opening build, underwater half-time) |
| `m.bed_level(a, b, level)` | bed volume per section |
| `m.gap(a, b)` | near-silence right before a drop; this is what makes drops hit |
| `m.write("assets/mix.wav")` | duck, soft-clip, normalise, fade out |
| `m.beat(k)`, `m.bar(k)` | grid times |

**Synth voices** (numpy, deterministic): `kick`, `clap`, `hat`, `bass808(freq, d)`, `horn(freq)` (car horn), `cowbell`, `riser(d)`, `impact()`, `whoosh`, `screech` (tyres), `vine_boom`, `notif`, `tone(freq, d, kind, decay)`.

**Recorded CC0 sounds:** `h.sfx("impact/impactSoft_medium_001")`, `h.sfx("keyboard/keypress-007")`, `h.sfx("casino/card-slide-1")`, `h.sfx("interface/click_003")`… See `music/sfx/sfx-analysis.md` for which are safe to repeat.

## Recipes

- **Drop punch on a bed:** one kick on every bar downbeat plus claps on beats 2 and 4, at about 0.9 gain, on top of the bed.
- **Jersey club:** kicks on 16ths `[0, 3, 6, 8, 10, 12, 14]`, a "bed squeak" on 7 and 15, claps on beats 2 and 4.
- **Typing:** `keyboard/keypress-0NN` every ~64 ms, cycling the files so it doesn't sound robotic.
- **Data / "sound link":** short random FSK tone bursts between 1.5 and 3.2 kHz.

## Verify (you can't listen)

```python
import wave, numpy as np
w = wave.open("assets/mix.wav"); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
for a, b, name in SECTIONS: print(name, np.sqrt((x[int(a*44100):int(b*44100)]**2).mean()))
```

- **Loudness:** drops should be the loudest sections and the build lower; the gap should be about zero.
- **Spectrogram:** `ffmpeg -i assets/mix.wav -lavfi showspectrumpic=s=1500x260:legend=0:scale=log:stop=8000 spec.png`. Look for the risers, the gap, and the filter sweeps.
- **Voices:** cut the segment and run faster-whisper on it.

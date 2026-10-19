"""Word-timed captions for reel voice lines, in Remotion's Caption format.

    kinetix captions <reel-dir>          (or: python captions.py lines.json assets/captions.js)

lines.json: [{"clip": "assets/kiski.wav", "at": 1.62, "text": "Arre! Yeh kiski gaadi hai yaar?!", "y": 560}, ...]
  at   = where the mix places the clip (music.py trims the clip's leading silence first, so do we)
  text = the script; Whisper (English mode, script as prompt) aligns these exact words, so Hinglish stays
         romanised instead of coming back as misspelt Devanagari
  y    = optional caption position for this line

Output (.json, or .js that sets window.CAPTIONS): {"captions": [Caption...], "zones": [{"startMs", "endMs", "y"}]} where Caption is
{text, startMs, endMs, timestampMs, confidence} with a leading space per word, as
@remotion/captions createTikTokStyleCaptions() expects.
"""
import json
import re
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel


def lead_in(path):
    """Seconds of near-silence music.py's load() trims from the front of a clip."""
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    i = np.flatnonzero(np.abs(x) > 0.02)
    return max(0, i[0] - 200) / sr if len(i) else 0.0


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def main(lines_path, out_path):
    lines = json.load(open(lines_path))
    model = WhisperModel("small", device="cpu", compute_type="int8")
    caps, zones = [], []
    for ln in lines:
        segs, _ = model.transcribe(ln["clip"], language="en", word_timestamps=True, initial_prompt=ln["text"])
        words = [w for s in segs for w in s.words]
        script = ln["text"].split()
        heard = [w.word.strip() for w in words]
        if [norm(w) for w in heard] != [norm(w) for w in script]:
            print(f"warning: {ln['clip']}: heard {heard!r}, script {script!r}; using script words on heard timing", file=sys.stderr)
            # spread the script across the heard span, weighted by word length
            a, b = (words[0].start, words[-1].end) if words else (0.0, 0.3 * len(script))
            lens = np.array([len(w) + 1 for w in script], float)
            edges = a + (b - a) * np.concatenate([[0], np.cumsum(lens) / lens.sum()])
            timed = list(zip(script, edges[:-1], edges[1:], [0.5] * len(script)))
        else:
            timed = [(s, w.start, w.end, w.probability) for s, w in zip(script, words)]
        off = ln["at"] - lead_in(ln["clip"])
        for i, (text, s, e, p) in enumerate(timed):
            start = round(max(off + s, ln["at"]) * 1000)  # Whisper puts the first word at t=0 of the file
            caps.append({"text": (" " if i else "") + text, "startMs": start, "endMs": round((off + e) * 1000),
                         "timestampMs": start, "confidence": round(float(p), 3)})
        zones.append({"startMs": caps[-len(timed)]["startMs"], "endMs": caps[-1]["endMs"] + 600, "y": ln.get("y")})
    data = json.dumps({"captions": caps, "zones": zones}, indent=1, ensure_ascii=False)
    # a .js target loads in file:// pages, which can't fetch JSON
    open(out_path, "w").write(f"window.CAPTIONS = {data};\n" if out_path.endswith(".js") else data)
    print(f"{out_path}: {len(caps)} words in {len(zones)} lines")


if __name__ == "__main__":
    main(*sys.argv[1:3])

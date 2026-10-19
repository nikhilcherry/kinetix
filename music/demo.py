"""Demo: a MusicGen bed with numpy production on top, every hit placed by beat number.

    venv/bin/python hypebeat.py gen "hard phonk, cowbell melody, distorted 808 bass" --bpm 150 --seconds 40 -o out/bed.wav
    venv/bin/python demo.py out/bed.wav out/demo-mix.wav
"""
import sys

import hits as h
from hits import Mix

bed, out = sys.argv[1], sys.argv[2]
m = Mix(bed)
DROP = 32                                   # beat 32 = bar 8

# intro: bed pulled down to a murmur, then horns announce the build
m.bed_level(0, m.beat(16), 0.25)
for k in (0, 2, 3):
    m.add(m.beat(k), h.horn(392, 0.16, 0.2))

# build: kicks every beat get denser, riser into the drop
m.bed_level(m.beat(16), m.beat(DROP), 0.55)
for k in range(16, DROP):
    m.drums(m.beat(k), h.kick(0.7))
    if k >= DROP - 4:
        m.drums(m.beat(k) + m.period / 2, h.kick(0.6))
m.add(m.beat(DROP - 8), h.riser(8 * m.period), 0.9)

# the "unless…" gap, then everything hits
m.gap(m.beat(DROP) - 0.35, m.beat(DROP))
m.bed_level(m.beat(DROP), m.beat(DROP + 64), 1.0)
m.add(m.beat(DROP), h.impact(), 1.0)
m.add(m.beat(DROP) + 0.25, h.horn(392, 0.12, 0.2))
m.add(m.beat(DROP) + 0.42, h.horn(392, 0.2, 0.2))

# mid-drop accents
m.add(m.beat(DROP + 16), h.vine_boom(), 0.6)
m.add(m.beat(DROP + 30), h.screech(), 0.8)
for k in range(4):
    m.add(m.beat(DROP + 24) + k * m.period / 2, h.notif(), 0.6)

print(m.write(out), f"{m.bpm} bpm, drop at {m.beat(DROP):.2f}s")

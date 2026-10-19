"""Template soundtrack: pure synth on the reel's 150 bpm grid. `kinetix mix .` writes assets/mix.wav.

Swap in a MusicGen bed when you have one:
    kinetix music gen "dark phonk, cowbell, distorted 808" --bpm 150 --seconds 20 -o assets/bed.wav
    m = Mix("assets/bed.wav", seconds=DUR)      # instead of Mix(bpm=..., seconds=...)
"""
import hits as h
from hits import Mix

DUR = 19.2
m = Mix(bpm=150, seconds=DUR)
B, BAR = m.period, 4 * m.period
BUILD, GAP, DROP, OUTRO = 3.2, 9.2, 9.6, 16.0
ROOT = [43.65, 43.65, 51.91, 38.89]  # 808 roots per bar (F, F, Ab, Eb)

# hook: a sub drone and three hits on the words
m.drums(0, h.bass808(43.65, 3.0) * 0.5)
for t in (0.1, 0.4, 1.2):
    m.add(t, h.impact()[: int(0.4 * h.SR)], 0.5)

# build: kicks thicken, a hit on each list item, riser into the gap
for k in range(int((GAP - BUILD) / B)):
    t = BUILD + k * B
    m.drums(t, h.kick(0.7))
    if t > GAP - BAR:
        m.drums(t + B / 2, h.kick(0.6))
    for s in range(2 if t < GAP - BAR else 4):
        m.drums(t + s * B / (2 if t < GAP - BAR else 4), h.hat())
for i in range(4):
    m.add(BUILD + 0.8 + i * 1.2, h.sfx("casino/card-slide-1"), 0.5)
m.add(GAP - 2 * BAR, h.riser(2 * BAR), 0.9)
m.gap(GAP, DROP)

# drop: jersey-club kick pattern, claps, hats, 808, a horn riff
KICKS, RIFF = [0, 3, 6, 8, 10, 12, 14], [(0, 349), (3, 349), (6, 415), (8, 523), (10, 415), (12, 622), (14, 523)]
for b in range(int((OUTRO - DROP) / BAR)):
    bt = DROP + b * BAR
    for s in KICKS:
        m.drums(bt + s * B / 4, h.kick(1.0 if s in (0, 8) else 0.8))
    m.drums(bt + B, h.clap()); m.drums(bt + 3 * B, h.clap())
    for s in range(1, 16, 2):
        m.drums(bt + s * B / 4, h.hat(open_=(s == 15)))
    m.drums(bt, h.bass808(ROOT[b % 4], 0.7))
    for s, f in RIFF:
        m.drums(bt + s * B / 4, h.horn(f, 0.13, 0.07))
m.add(DROP, h.impact(), 1.0)
for i in range(4):
    m.add(12.8 + i * 0.8, h.impact()[: int(0.5 * h.SR)], 0.6)

# outro
m.drums(OUTRO, h.bass808(43.65, 1.6) * 0.5)
m.add(OUTRO + 0.05, h.sfx("impact/impactBell_heavy_000"), 0.6)

print(m.write("assets/mix.wav"))

"""Jersey-club beat + car-horn lead + SFX + voices for the Connect reel. 150 BPM: beat 0.4 s, bar 1.6 s. Writes assets/mix.wav."""
import sys
import wave
import numpy as np

SR = 44100
B = 0.4
BAR = 4 * B
S16 = B / 4
DUR = 58.4
N = int(DUR * SR)
rng = np.random.default_rng(11)

BUILD, GAP, DROP1, HALF, DROP2, OUTRO = 4.8, 15.6, 16.0, 28.8, 36.8, 52.8

music = np.zeros(N)
sfx = np.zeros(N)
voice = np.zeros(N)


def t_(d):
    return np.arange(int(d * SR)) / SR


def put(buf, at, x, gain=1.0):
    i = int(round(at * SR))
    if i >= N or i < 0:
        return
    x = x[: N - i]
    buf[i:i + len(x)] += gain * x


def env(d, attack=0.002, decay=0.2):
    t = t_(d)
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def hp(x):
    return np.diff(x, prepend=0)


def lp(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode="same")


def kick(gain=1.0, d=0.32):
    t = t_(d)
    f = 48 + 120 * np.exp(-t * 34)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    x[:50] += rng.normal(0, 0.5, 50)
    return np.tanh(2.6 * x) * gain


def bass808(freq, d):
    t = t_(d)
    f = freq * (1 + 0.5 * np.exp(-t * 40))
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d * 0.6))) * 0.5


def clap(g=0.38):
    x = hp(rng.normal(0, 1, int(0.22 * SR))) * env(0.22, 0.001, 0.07)
    for o in (0.009, 0.019):
        x[int(o * SR):] += 0.6 * x[: len(x) - int(o * SR)]
    return x * g


def hat(open_=False):
    d = 0.18 if open_ else 0.035
    return hp(hp(rng.normal(0, 1, int(d * SR)))) * env(d, 0.001, d / 3) * 0.11


def squeak():                                   # jersey "bed squeak"
    t = t_(0.12)
    f = 1900 + 900 * np.sin(np.pi * t / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.12) ** 2 * 0.07


def horn(freq, d=0.22, g=0.12):                 # two-tone car horn
    t = t_(d)
    x = np.sign(np.sin(2 * np.pi * freq * t)) + 0.8 * np.sign(np.sin(2 * np.pi * freq * 1.26 * t + 0.4))
    x = lp(lp(x, 6), 4) * (1 + 0.15 * np.sin(2 * np.pi * 28 * t))
    e = np.minimum(1, t / 0.006) * np.minimum(1, (d - t) / 0.02)
    return x * e * g


def riser(d):
    t = t_(d)
    n = hp(rng.normal(0, 1, len(t))) * (t / d) ** 2 * 0.25
    s = np.sin(2 * np.pi * np.cumsum(220 + 1500 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.12
    return n + s


def impact(d=1.6):
    t = t_(d)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t / 0.5)
    crash = hp(rng.normal(0, 1, len(t))) * np.exp(-t / 0.35) * 0.25
    return np.tanh(1.8 * boom) * 0.9 + crash


def tone(freq, d, kind="sine", decay=None, gain=0.3):
    t = t_(d)
    w = np.sin(2 * np.pi * freq * t)
    if kind == "square":
        w = np.sign(w) * 0.6
    e = np.exp(-t / decay) if decay else np.minimum(1, (d - t) / 0.01)
    return w * e * np.minimum(1, t / 0.003) * gain


def pad(freqs, d, gain=0.05):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.004 * t) for f in freqs)
    return x * np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.6) * gain


def whoosh(d=0.5):
    t = t_(d)
    return lp(rng.normal(0, 1, len(t)), 3) * np.sin(np.pi * t / d) ** 2 * 0.2


def screech(d=0.7):                             # tyre screech instead of a record scratch
    t = t_(d)
    f = 2300 + 500 * np.sin(2 * np.pi * 7 * t) - 600 * t / d
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * rng.normal(0, 1, len(t))
    return lp(x, 3) * np.minimum(1, t / 0.02) * np.exp(-t / 0.35) * 0.22


def lock_chirp():                               # car remote "bleep-bleep"
    one = tone(2700, 0.07, gain=0.18) + tone(3400, 0.07, gain=0.08)
    return np.concatenate([one, np.zeros(int(0.06 * SR)), one])


def fsk_burst(d, seed):                         # audible-band data frame, like Connect's fallback band
    r = np.random.default_rng(seed)
    sym = 0.025
    out = []
    for _ in range(int(d / sym)):
        f = r.uniform(1500, 3200)
        tt = t_(sym)
        out.append(np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / sym) ** 0.3)
    return np.concatenate(out) * 0.09


def vine_boom():
    t = t_(1.4)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.5) + 35) / SR) * np.exp(-t / 0.6))


def load(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    i = np.flatnonzero(np.abs(x) > 0.02)
    return x[max(0, i[0] - 200): i[-1] + 2000] if len(i) else x


KISKI = load("assets/kiski.wav")
GUARD = load("assets/guard.wav")
TAG = load("assets/tag.wav")
# vocal chop: the last ~0.42 s of "...yaar?!"
YAAR = KISKI[-int(0.5 * SR):-int(0.05 * SR)] * np.minimum(1, np.linspace(0, 40, int(0.45 * SR)))

# --------------------------------------------------------------- cold open: street + honks
put(music, 0, pad([87.3, 130.8], BUILD, 0.05))                 # street drone
put(music, 0, lp(rng.normal(0, 1, int(BUILD * SR)), 40) * 0.06)  # traffic rumble
for at, d in [(0.15, 0.55), (0.85, 0.12), (1.02, 0.12), (1.19, 0.3)]:
    put(sfx, at, horn(392, d, 0.22))
put(voice, 1.62, KISKI, 1.0)
put(sfx, 4.35, horn(392, 0.12, 0.2)); put(sfx, 4.52, horn(392, 0.12, 0.2))

# --------------------------------------------------------------- build (4.8 .. 15.6)
for i in range(int((GAP - BUILD) / B)):
    t = BUILD + i * B
    put(music, t, kick(0.75) if (i % 2 == 0 or t > GAP - 2 * BAR) else np.zeros(1))
    sub = 2 if t < GAP - 2 * BAR else 4
    for s in range(sub):
        put(music, t + s * B / sub, hat())
    if i % 4 == 2:
        put(music, t, clap(0.3))
for k in range(int((GAP - BUILD) / BAR) + 1):
    if BUILD + k * BAR < GAP - 0.1:
        put(sfx, BUILD + k * BAR, impact()[: int(0.5 * SR)], 0.35)
        put(sfx, BUILD + k * BAR - 0.25, whoosh(0.3), 0.6)
put(music, BUILD, pad([174.6, 207.7, 261.6], GAP - BUILD, 0.025))
# card 1 "honk for 20 minutes": horns on every beat
for k in range(4):
    put(sfx, 4.8 + k * B, horn(392 if k % 2 == 0 else 349, 0.16, 0.16))
# card 2 "note under the wiper"... (it rained): rain hiss
put(sfx, 7.2, lp(rng.normal(0, 1, int(0.8 * SR)), 2) * np.linspace(0.12, 0, int(0.8 * SR)))
put(voice, 8.55, GUARD, 1.0)                                     # card 3 the guard
put(sfx, 11.2, screech(), 1.0)                                   # card 4 freeze
for k in range(6):                                               # spam calls ringing
    put(sfx, 11.3 + k * 0.17, tone(1400 if k % 2 else 1100, 0.12, gain=0.1))
put(sfx, GAP - 2 * BAR, riser(2 * BAR), 0.9)
for at in (14.4, 14.6, 14.8, 15.0, 15.1, 15.2, 15.3, 15.4):     # yaar chop stutter into the gap
    put(voice, at, YAAR[: int(S16 * SR * 0.9)], 0.55)

# --------------------------------------------------------------- jersey club drops
ROOT = [43.65, 43.65, 51.91, 38.89]
KICKS = [0, 3, 6, 8, 10, 12, 14]                                 # bouncy jersey pattern (16ths)
RIFF = [(0, 349), (3, 349), (6, 415), (8, 523), (10, 415), (12, 622), (14, 523)]


def drop(start, end, horns=True, chops=True):
    nbar = int(round((end - start) / BAR))
    for b in range(nbar):
        bt = start + b * BAR
        for s in KICKS:
            put(music, bt + s * S16, kick(1.0 if s in (0, 8) else 0.8))
        put(music, bt + 4 * S16, clap()); put(music, bt + 12 * S16, clap())
        for s in range(16):
            if s % 2:
                put(music, bt + s * S16, hat(open_=(s == 15)))
        put(music, bt + 7 * S16, squeak()); put(music, bt + 15 * S16, squeak() * 0.7)
        put(music, bt, bass808(ROOT[b % 4], 0.7))
        put(music, bt + 8 * S16, bass808(ROOT[b % 4], 0.45))
        if horns:
            for s, f in RIFF:
                put(music, bt + s * S16, horn(f * (1 if b % 4 < 2 else 0.89), 0.13, 0.07))
        if chops and b % 2 == 1:
            for s in (12, 14, 15):
                put(voice, bt + s * S16, YAAR[: int(S16 * SR * (1.7 if s == 12 else 0.9))], 0.35)


drop(DROP1, HALF)
drop(DROP2, OUTRO, chops=False)
put(sfx, DROP1, impact(), 1.0)
put(sfx, DROP2, impact(), 1.0)
put(sfx, DROP1 + 0.25, lock_chirp(), 1.0)                       # car-lock bleep on the logo
for k in range(4):                                               # plate typing ticks on the beat
    put(sfx, 22.4 + k * B, tone(2200, 0.04, gain=0.18))
put(sfx, 24.0, np.concatenate([tone(1320, 0.07, gain=0.2), tone(1760, 0.14, decay=0.07, gain=0.2)]))  # ping
put(sfx, 25.6, np.concatenate([tone(1568, 0.07, gain=0.18), tone(2093, 0.14, decay=0.07, gain=0.18)]))
put(sfx, 27.2, impact()[: int(0.8 * SR)], 0.8)                  # "0" slam

# --------------------------------------------------------------- half-time: no signal, sound link
for b in range(5):
    bt = HALF + b * BAR
    put(music, bt, kick(0.7)); put(music, bt + 2 * B, clap(0.22))
    put(music, bt, bass808(ROOT[b % 4], 1.4) * 0.55)
    for s in range(8):
        put(music, bt + s * B / 2, hat() * 0.5)
put(music, HALF, pad([349, 415, 523], DROP2 - HALF, 0.02))
for k, at in enumerate([28.95, 29.25, 29.55, 29.85]):          # signal bars dropping
    put(sfx, at, tone(880 / (1.2 ** k), 0.12, decay=0.05, gain=0.15))
for k, at in enumerate([30.5, 31.0, 31.5, 32.1, 32.6]):         # data chirps
    put(sfx, at, fsk_burst(0.3, k), 1.0)
put(sfx, 33.2, vine_boom(), 0.65)
put(sfx, 33.7, fsk_burst(0.25, 9), 0.8); put(sfx, 34.3, fsk_burst(0.25, 10), 0.6)
put(sfx, 35.2, np.concatenate([tone(1320, 0.07, gain=0.2), tone(1760, 0.14, decay=0.07, gain=0.2)]))
put(sfx, DROP2 - BAR, riser(BAR), 0.85)

# --------------------------------------------------------------- drop 2 sfx
put(sfx, 38.4, whoosh(0.4), 0.8)
for k in range(3):                                               # scan locks
    put(sfx, 38.6 + k * 0.8, tone(2637, 0.06, gain=0.12))
put(sfx, 41.6, whoosh(0.4), 0.8); put(sfx, 44.8, whoosh(0.4), 0.8)
put(sfx, 46.4, impact()[: int(0.6 * SR)], 0.6)
for k in range(4):                                               # language flips / feature flips
    put(sfx, 48.0 + k * B, tone(1046 * (1.12 ** k), 0.1, decay=0.05, gain=0.12))
    put(sfx, 49.6 + k * B, impact()[: int(0.25 * SR)], 0.35)
for t in (51.2, 51.73, 52.27):
    put(sfx, t, impact()[: int(0.5 * SR)], 0.55)

# --------------------------------------------------------------- outro
put(music, OUTRO, pad([174.6, 261.6, 349, 415], DUR - OUTRO, 0.05))
put(music, OUTRO, bass808(43.65, 1.6) * 0.5)
for b in range(3):
    bt = OUTRO + b * BAR
    put(music, bt, kick(0.6)); put(music, bt + 2 * B, clap(0.18))
put(sfx, 54.4, impact(), 0.9)
put(sfx, 54.65, lock_chirp(), 0.9)
put(voice, 54.5, TAG, 1.0)
put(sfx, 57.6, horn(392, 0.12, 0.16)); put(sfx, 57.78, horn(392, 0.2, 0.16))

# --------------------------------------------------------------- optional MusicGen bed (hypebeat)
# `kinetix mix examples/connect --bed assets/bed.wav` swaps the synth drums for a MusicGen bed on the same 150 bpm grid
# (make one with: kinetix music gen "<assets/bed.json prompt>" --bpm 150 --seconds 60 --seed 2 -o assets/bed.wav),
# arranged with a moving low-pass: muffled cold open, opening build, full drops, underwater half-time.
OUT = "assets/mix.wav"
if "--bed" in sys.argv:
    with wave.open(sys.argv[sys.argv.index("--bed") + 1]) as w:
        bed = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
        assert w.getframerate() == SR and w.getnchannels() == 1
    bed = np.pad(bed, (0, max(0, N - len(bed))))[:N]
    t = np.arange(N) / SR
    full = 16000.0
    cut = np.full(N, full)
    cut[t < BUILD] = 350
    b = (t >= BUILD) & (t < GAP)
    cut[b] = 350 * (full / 350) ** ((t[b] - BUILD) / (GAP - BUILD))           # filter opens through the build
    cut[(t >= HALF) & (t < DROP2)] = 500                                     # basement, 0 bars
    o = t >= OUTRO
    cut[o] = full * (300 / full) ** ((t[o] - OUTRO) / (DUR - OUTRO))         # closes on the logo
    cut = np.convolve(cut, np.ones(2205) / 2205, mode="same")               # no zipper steps at section edges
    a = 1 - np.exp(-2 * np.pi * cut / SR)
    for _ in range(2):                                                        # two one-pole stages, 12 dB/oct
        out, z = np.empty(N), 0.0
        for i in range(N):
            z += a[i] * (bed[i] - z)
            out[i] = z
        bed = out
    # bed level: quiet open, rising build, full drops, sunk half-time, fading outro
    level = np.ones(N)
    level[t < BUILD] = 0.3
    level[b] = 0.35 + 0.35 * (t[b] - BUILD) / (GAP - BUILD)
    level[(t >= HALF) & (t < DROP2)] = 0.45
    level[o] = 0.55 * (1 - (t[o] - OUTRO) / (DUR - OUTRO))
    # keep some of the synth drums on top for punch: they're on the same grid
    drums = np.zeros(N)
    drums[b] = 0.6
    drums[((t >= DROP1) & (t < HALF)) | ((t >= DROP2) & (t < OUTRO))] = 0.55
    drums[(t >= HALF) & (t < DROP2)] = 0.35
    drums[o] = 0.5
    smooth = lambda x: np.convolve(x, np.ones(2205) / 2205, mode="same")
    music = bed * smooth(level) * 1.6 + music * smooth(drums)
    OUT = "assets/mix.wav"

# --------------------------------------------------------------- mix
venv = np.convolve(np.abs(voice), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
duck = 1 - 0.6 * np.clip(venv * 12, 0, 1)
mix = music * duck + sfx * (0.6 + 0.4 * duck) + voice * 1.1
g0, g1 = int(GAP * SR), int(DROP1 * SR)
mix[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 6                   # the "unless…" gap
mix = np.tanh(1.3 * mix / np.abs(mix).max())
mix *= 0.89 / np.abs(mix).max()
fade = int(0.6 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
with wave.open(OUT, "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", DUR)

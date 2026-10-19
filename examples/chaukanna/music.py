"""Beat + SFX + voices for the Chaukanna reel. 150 BPM: beat 0.4 s, bar 1.6 s. Writes assets/mix.wav."""
import wave
import numpy as np

SR = 44100
B = 0.4                      # one beat
BAR = 4 * B
DUR = 60.8
N = int(DUR * SR)
rng = np.random.default_rng(7)

DROP1, HALF, DROP2, FLEX, OUTRO = 17.6, 28.8, 36.8, 48.0, 56.0
BUILD = 4.8

music = np.zeros(N)
sfx = np.zeros(N)
voice = np.zeros(N)


def t_(d):
    return np.arange(int(d * SR)) / SR


def put(buf, at, x, gain=1.0):
    i = int(at * SR)
    if i >= N:
        return
    x = x[: N - i]
    buf[i:i + len(x)] += gain * x


def env(d, attack=0.002, decay=0.2):
    t = t_(d)
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def hp(x):                   # crude high-pass
    return np.diff(x, prepend=0)


def lp(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode="same")


def kick(gain=1.0):
    t = t_(0.45)
    f = 45 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.16)
    x[:60] += rng.normal(0, 0.5, 60)
    return np.tanh(2.2 * x) * gain


def bass808(freq, d):
    t = t_(d)
    f = freq * (1 + 0.6 * np.exp(-t * 40))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(3 * np.sin(ph) * np.exp(-t / (d * 0.6))) * 0.55


def clap():
    x = hp(rng.normal(0, 1, int(0.2 * SR))) * env(0.2, 0.001, 0.06)
    for o in (0.008, 0.017):
        x[int(o * SR):] += 0.6 * x[: len(x) - int(o * SR)]
    return x * 0.35


def hat(open_=False):
    d = 0.18 if open_ else 0.04
    return hp(hp(rng.normal(0, 1, int(d * SR)))) * env(d, 0.001, d / 3) * 0.12


def cowbell(freq):
    t = t_(0.22)
    x = np.sign(np.sin(2 * np.pi * freq * t)) + 0.7 * np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    return lp(x, 4) * np.exp(-t / 0.07) * 0.09


def riser(d):
    t = t_(d)
    n = hp(rng.normal(0, 1, len(t))) * (t / d) ** 2 * 0.25
    s = np.sin(2 * np.pi * np.cumsum(200 + 1400 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.12
    return n + s


def impact():
    t = t_(1.6)
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


def pad(freqs, d, gain=0.06):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) for f in freqs)
    e = np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.8)
    return x * e * gain


def whoosh(d=0.5):
    t = t_(d)
    x = lp(rng.normal(0, 1, len(t)), 3) * np.sin(np.pi * t / d) ** 2
    return x * 0.2


# --------------------------------------------------------------- cold open: Nokia-style ringtone
nokia = [(659, .125), (587, .125), (370, .25), (415, .25), (554, .125), (494, .125), (294, .25), (330, .25),
         (494, .125), (440, .125), (277, .25), (330, .25), (440, .5)]
t0 = 0.1
for f, d in nokia:
    put(sfx, t0, tone(f * 1.0, d * 0.95, "square", gain=0.17))
    t0 += d * 0.9
put(sfx, 2.35, tone(1000, 0.06, gain=0.15))                    # answer click
put(music, 2.4, pad([46.25, 92.5], 2.4, 0.12))                 # dread drone
put(voice, 2.6, None) if False else None

# --------------------------------------------------------------- build (4.8 .. 17.6)
for i in range(int((DROP1 - BUILD) / B)):
    t = BUILD + i * B
    if t >= DROP1 - 0.4:
        break
    if i % 2 == 0 or t > DROP1 - 2 * BAR:
        put(music, t, kick(0.8))
    sub = 2 if t < DROP1 - 2 * BAR else 4
    for s in range(sub):
        put(music, t + s * B / sub, hat())
    if i % 4 == 2:
        put(music, t, clap())
for k in range(8):                                              # card hits
    put(sfx, BUILD + k * BAR, impact()[: int(0.5 * SR)], 0.35)
    put(sfx, BUILD + k * BAR - 0.25, whoosh(0.3), 0.6)
put(music, BUILD, pad([92.5, 110, 138.6], DROP1 - 0.4 - BUILD, 0.03))
put(sfx, DROP1 - 2 * BAR - 0.4, riser(2 * BAR), 0.9)
# record scratch at "LIFE SAVINGS" (11.2)
t = t_(0.35)
put(sfx, 11.2, hp(rng.normal(0, 1, len(t))) * np.sin(2 * np.pi * 9 * t) ** 2 * np.exp(-t / 0.2) * 0.5)

# --------------------------------------------------------------- drops
ROOT = [46.25, 46.25, 55.0, 41.2]                               # F#1 F#1 A1 E1 per bar
BELL = [740, 0, 880, 740, 0, 659, 740, 0, 988, 0, 880, 740, 659, 0, 554, 0]


def drop(start, end, bell=True):
    nbar = int(round((end - start) / BAR))
    for b in range(nbar):
        bt = start + b * BAR
        root = ROOT[b % 4]
        for beat, (k, eighth) in enumerate([(1, 0), (0, 1), (1, 0), (0, 1)]):
            t = bt + beat * B
            if k or b % 2:
                put(music, t, kick(1.0))
            if beat in (1, 3):
                put(music, t, clap())
            for s in range(4):
                put(music, t + s * B / 4, hat(open_=(s == 2 and beat == 3)))
        put(music, bt, bass808(root, 0.75))
        put(music, bt + 1.2, bass808(root * 1.5, 0.35))
        if bell:
            for s, f in enumerate(BELL):
                if f:
                    put(music, bt + s * B / 4, cowbell(f * (1.0 if b % 4 < 2 else 0.89)))


drop(DROP1, HALF)
drop(DROP2, OUTRO)
put(sfx, DROP1, impact(), 1.0)
put(sfx, DROP2, impact(), 1.0)

# --------------------------------------------------------------- half-time sneaky (28.8 .. 36.8)
for b in range(5):
    bt = HALF + b * BAR
    put(music, bt, kick(0.7))
    put(music, bt + 2 * B, clap() * 0.6)
    put(music, bt, bass808(ROOT[b % 4] / 1.0, 1.4) * 0.6)
    for s in range(8):
        put(music, bt + s * B / 2, hat() * 0.6)
put(music, HALF, pad([185, 220, 277], DROP2 - HALF, 0.025))
put(sfx, DROP2 - BAR, riser(BAR), 0.8)
put(sfx, 33.2, (lambda t: np.tanh(3 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.5) + 35) / SR) * np.exp(-t / 0.6)))(t_(1.4)), 0.7)  # vine boom
for k in range(3):                                              # hang-up beeps
    put(sfx, 34.4 + k * 0.3, tone(425, 0.18, gain=0.18))
put(sfx, 35.4, tone(220, 0.5, decay=0.3, gain=0.0))

# --------------------------------------------------------------- drop 2 sfx
for k in range(5):                                              # notifications stacking
    put(sfx, DROP2 + 0.4 + k * B, np.concatenate([tone(1320, 0.07, gain=0.18), tone(1760, 0.12, decay=0.06, gain=0.18)]))
put(sfx, 39.2, whoosh(0.6), 0.8)
for k in range(3):                                              # checklist dings
    put(sfx, 42.4 + k * 2 * B, tone(1568, 0.5, decay=0.15, gain=0.22) + tone(2349, 0.5, decay=0.1, gain=0.1))
put(sfx, 45.6, tone(110, 0.45, "square", gain=0.18))            # buzzer
put(sfx, 46.4, impact()[: int(0.8 * SR)], 0.8)                  # DENIED stamp

# --------------------------------------------------------------- flex + outro
for k, t in enumerate([48.0, 49.6]):
    put(sfx, t + 0.4, tone(1046, 0.6, decay=0.25, gain=0.15) + tone(1318, 0.6, decay=0.25, gain=0.1))
for t in (51.2, 52.8, 54.4):
    put(sfx, t, impact()[: int(0.6 * SR)], 0.6)
put(music, OUTRO, pad([92.5, 138.6, 185, 220], DUR - OUTRO, 0.05))
put(music, OUTRO, bass808(46.25, 1.6) * 0.5)
put(sfx, 57.6, impact(), 1.0)
put(sfx, 59.2, tone(2637, 1.2, decay=0.4, gain=0.12) + tone(3951, 1.2, decay=0.3, gain=0.06))


# --------------------------------------------------------------- voices
def load(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    return x


def phone_fx(x):                                                # band-limited "phone line"
    return lp(hp(x), 5) * 2.2


VOICE = {"scam1": 2.6, "scam2": 13.0, "whisper": 29.4, "tag": 57.8}
put(voice, VOICE["scam1"], phone_fx(load("assets/scam1.wav")), 0.9)
put(voice, VOICE["scam2"], phone_fx(load("assets/scam2.wav")), 0.55)
w = load("assets/whisper.wav")
put(voice, VOICE["whisper"], w + 0.3 * np.concatenate([np.zeros(int(0.09 * SR)), w])[: len(w)], 1.0)
put(voice, VOICE["tag"], load("assets/tag.wav"), 1.0)

# duck the music under voices
venv = np.convolve(np.abs(voice), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
duck = 1 - 0.65 * np.clip(venv * 12, 0, 1)
mix = music * duck + sfx * (0.6 + 0.4 * duck) + voice
mix[int((DROP1 - 0.4) * SR):int(DROP1 * SR)] *= 0.0             # the "unless…" gap
mix = np.tanh(1.3 * mix / (np.abs(mix).max() / 1.0)) 
mix *= 0.89 / np.abs(mix).max()
fade = int(0.6 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
with wave.open("assets/mix.wav", "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", DUR)

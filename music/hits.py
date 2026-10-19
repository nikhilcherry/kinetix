"""Numpy sound kit for layering on a hypebeat bed: drops, risers, impacts, stutters, all on the beat grid.

    from hits import Mix
    import hits as h
    m = Mix("bed.wav")                       # reads bed.json for the bpm
    m.gap(m.beat(32) - 0.4, m.beat(32))      # silence right before the drop
    m.add(m.beat(32), h.impact())            # drop
    m.add(m.beat(28), h.riser(4 * m.period)) # 4-beat riser into it
    m.stutter("voice.wav", m.beat(30), m.beat(32), step=m.period / 4)
    m.write("mix.wav")

Part of Kinetix. Recorded sounds in sfx/ are CC0 (see sfx/LICENSE.md); load them with sfx("impact/impactSoft_medium_001").
"""
import json
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(d, attack=0.002, decay=0.2):
    t = t_(d)
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def hp(x):
    return np.diff(x, prepend=0)


def lp(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode="same")


def kick(gain=1.0, d=0.32):
    t = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-t * 34)) / SR) * np.exp(-t / 0.11)
    x[:50] += _rng.normal(0, 0.5, 50)
    return np.tanh(2.6 * x) * gain


def bass808(freq, d):
    t = t_(d)
    f = freq * (1 + 0.5 * np.exp(-t * 40))
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d * 0.6))) * 0.5


def clap(g=0.38):
    x = hp(_rng.normal(0, 1, int(0.22 * SR))) * env(0.22, 0.001, 0.07)
    for o in (0.009, 0.019):
        x[int(o * SR):] += 0.6 * x[: len(x) - int(o * SR)]
    return x * g


def hat(open_=False):
    d = 0.18 if open_ else 0.035
    return hp(hp(_rng.normal(0, 1, int(d * SR)))) * env(d, 0.001, d / 3) * 0.11


def horn(freq, d=0.22, g=0.12):
    t = t_(d)
    x = np.sign(np.sin(2 * np.pi * freq * t)) + 0.8 * np.sign(np.sin(2 * np.pi * freq * 1.26 * t + 0.4))
    x = lp(lp(x, 6), 4) * (1 + 0.15 * np.sin(2 * np.pi * 28 * t))
    return x * np.minimum(1, t / 0.006) * np.minimum(1, (d - t) / 0.02) * g


def cowbell(freq, g=0.09):
    t = t_(0.22)
    x = np.sign(np.sin(2 * np.pi * freq * t)) + 0.7 * np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    return lp(x, 4) * np.exp(-t / 0.07) * g


def riser(d):
    t = t_(d)
    n = hp(_rng.normal(0, 1, len(t))) * (t / d) ** 2 * 0.25
    s = np.sin(2 * np.pi * np.cumsum(220 + 1500 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.12
    return n + s


def impact(d=1.6):
    t = t_(d)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t / 0.5)
    crash = hp(_rng.normal(0, 1, len(t))) * np.exp(-t / 0.35) * 0.25
    return np.tanh(1.8 * boom) * 0.9 + crash


def tone(freq, d, kind="sine", decay=None, gain=0.3):
    t = t_(d)
    w = np.sin(2 * np.pi * freq * t)
    if kind == "square":
        w = np.sign(w) * 0.6
    e = np.exp(-t / decay) if decay else np.minimum(1, (d - t) / 0.01)
    return w * e * np.minimum(1, t / 0.003) * gain


def whoosh(d=0.5):
    t = t_(d)
    return lp(_rng.normal(0, 1, len(t)), 3) * np.sin(np.pi * t / d) ** 2 * 0.2


def screech(d=0.7):
    t = t_(d)
    f = 2300 + 500 * np.sin(2 * np.pi * 7 * t) - 600 * t / d
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * _rng.normal(0, 1, len(t))
    return lp(x, 3) * np.minimum(1, t / 0.02) * np.exp(-t / 0.35) * 0.22


def vine_boom():
    t = t_(1.4)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.5) + 35) / SR) * np.exp(-t / 0.6))


def notif():
    return np.concatenate([tone(1320, 0.07, gain=0.2), tone(1760, 0.14, decay=0.07, gain=0.2)])


def load(path):
    """Mono float audio at SR, trimmed of leading/trailing silence."""
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    i = np.flatnonzero(np.abs(x) > 0.02)
    return x[max(0, i[0] - 200): i[-1] + 2000] if len(i) else x


class Mix:
    """A bed plus layers. Music ducks under voice; gaps cut everything for the 'unless…' moment."""

    def __init__(self, bed_path=None, bed_gain=0.8, bpm=None, seconds=None):
        """bed_path: a hypebeat bed (its .json gives the bpm). Without one, pass bpm and seconds for a pure-synth mix."""
        if bed_path:
            meta = json.load(open(bed_path.rsplit(".", 1)[0] + ".json"))
            self.bpm = bpm or meta["bpm"]
            bed = load_raw(bed_path) * bed_gain
        else:
            if not (bpm and seconds):
                raise ValueError("Mix() without a bed needs bpm= and seconds=")
            self.bpm, bed = bpm, np.zeros(int(seconds * SR))
        if seconds:
            bed = np.pad(bed, (0, max(0, int(seconds * SR) - len(bed))))[: int(seconds * SR)]
        self.period = 60.0 / self.bpm
        self.bed = bed
        self.n = len(self.bed)
        self.sfx = np.zeros(self.n)
        self.voice = np.zeros(self.n)
        self.music = np.zeros(self.n)
        self.gaps = []
        self.bed_env = np.ones(self.n)

    def beat(self, k):
        return k * self.period

    def bar(self, k):
        return 4 * k * self.period

    def _put(self, buf, at, x, gain):
        i = int(round(at * SR))
        if 0 <= i < self.n:
            x = x[: self.n - i]
            buf[i:i + len(x)] += gain * x

    def add(self, at, x, gain=1.0):
        self._put(self.sfx, at, x, gain)

    def drums(self, at, x, gain=1.0):
        self._put(self.music, at, x, gain)

    def say(self, at, x, gain=1.0):
        self._put(self.voice, at, x, gain)

    def stutter(self, x, start, end, step):
        """Retrigger the head of clip x every `step` seconds from start to end (vocal chop)."""
        k = 0
        while start + k * step < end - 1e-6:
            self._put(self.voice, start + k * step, x[: int(step * SR * 0.9)], 0.55)
            k += 1

    def bed_level(self, start, end, level, ramp=0.05):
        """Pull the bed down (or up) between start and end, e.g. a breakdown or filtered intro."""
        a, b, r = int(start * SR), int(end * SR), int(ramp * SR)
        self.bed_env[a:b] = level
        if r and a - r > 0:
            self.bed_env[a - r:a] = np.linspace(self.bed_env[a - r], level, r)

    def lowpass(self, points):
        """Sweep a 12 dB/oct low-pass over the bed. points = [(t, hz), ...], interpolated in log-frequency,
        e.g. [(0, 350), (4.8, 350), (14, 16000)] = muffled intro, filter opening through the build."""
        t = np.arange(self.n) / SR
        ts, hz = zip(*points)
        cut = np.exp(np.interp(t, ts, np.log(hz)))
        a = 1 - np.exp(-2 * np.pi * cut / SR)
        x = self.bed
        for _ in range(2):
            out, z = np.empty(self.n), 0.0
            for i in range(self.n):
                z += a[i] * (x[i] - z)
                out[i] = z
            x = out
        self.bed = x

    def gap(self, start, end):
        self.gaps.append((start, end))

    def write(self, path, fade=0.6):
        venv = np.convolve(np.abs(self.voice), np.ones(int(0.15 * SR)) / int(0.15 * SR), mode="same")
        duck = 1 - 0.6 * np.clip(venv * 12, 0, 1)
        mix = (self.bed * self.bed_env + self.music) * duck + self.sfx * (0.6 + 0.4 * duck) + self.voice * 1.1
        for s, e in self.gaps:
            a, b = int(s * SR), int(e * SR)
            mix[a:b] *= np.linspace(1, 0, b - a) ** 6
        mix = np.tanh(1.3 * mix / (np.abs(mix).max() + 1e-9))
        mix *= 0.89 / np.abs(mix).max()
        f = int(fade * SR)
        mix[-f:] *= np.linspace(1, 0, f)
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((mix * 32767).astype(np.int16).tobytes())
        return path


def load_raw(path):
    """Like load() but keeps the bed's timing (no silence trim), since beat 0 sits at t=0."""
    import soundfile as sf
    x, sr = sf.read(path, dtype="float64")
    if x.ndim == 2:
        x = x.mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    return x


SFX_DIR = __import__("pathlib").Path(__file__).with_name("sfx")


def sfx(name, gain=1.0):
    """A recorded CC0 sound from sfx/, e.g. sfx("keyboard/keypress-007"), sfx("impact/impactSoft_medium_001")."""
    path = next(SFX_DIR.glob(name + ".*"))
    return load_raw(str(path)) * gain

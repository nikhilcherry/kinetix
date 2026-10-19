"""Music engine tests: tempo lock, beat phase, filter, pure-synth mix, recorded SFX."""
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "music"))
import hits as h  # noqa: E402
import hypebeat as hb  # noqa: E402

SR = h.SR


def click_track(bpm, seconds, offset=0.0):
    y = np.zeros(int(seconds * SR))
    period = 60 / bpm
    k = kick = h.kick(0.9)
    t = offset
    while t < seconds - 0.4:
        i = int(t * SR)
        y[i:i + len(k)] += kick[: len(y) - i]
        t += period
    return y


def test_tempo_of_finds_the_grid_tempo():
    for bpm in (120, 150):
        assert abs(hb.tempo_of(click_track(bpm, 12), SR, bpm) - bpm) < 1.5


def test_tempo_of_folds_half_and_double_time():
    # a 75 bpm pulse asked about at 150 should come back as 150, not 75
    assert abs(hb.tempo_of(click_track(75, 16), SR, 150) - 150) < 2


def test_conform_puts_a_beat_at_zero():
    y = click_track(150, 12, offset=0.13)
    out, raw, grid = hb.conform(y, SR, 150)
    assert abs(grid - 150) < 0.01
    first = np.flatnonzero(np.abs(out) > 0.3)[0] / SR
    period = 60 / 150
    assert min(first % period, period - first % period) < 0.03


def test_pure_synth_mix_writes_audio(tmp_path):
    m = h.Mix(bpm=150, seconds=4)
    for k in range(10):
        m.drums(m.beat(k), h.kick())
    m.add(1.6, h.impact())
    m.gap(2.0, 2.4)
    out = tmp_path / "mix.wav"
    m.write(str(out))
    with wave.open(str(out)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
        assert w.getframerate() == SR and abs(len(x) / SR - 4) < 0.01
    assert np.abs(x).max() > 0.5
    gap = x[int(2.25 * SR):int(2.4 * SR)]
    assert np.sqrt((gap ** 2).mean()) < 0.02, "the gap before a drop must be near-silent"


def test_lowpass_removes_highs():
    m = h.Mix(bpm=150, seconds=2)
    t = np.arange(m.n) / SR
    m.bed = np.sin(2 * np.pi * 6000 * t) * 0.5
    m.lowpass([(0, 300), (2, 300)])
    assert np.abs(m.bed[SR // 2:]).max() < 0.02


def test_recorded_sfx_load():
    for name in ("impact/impactSoft_medium_001", "keyboard/keypress-007", "interface/click_003"):
        x = h.sfx(name)
        assert len(x) > 100 and np.abs(x).max() > 0.05

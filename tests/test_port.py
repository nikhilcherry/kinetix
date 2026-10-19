"""tools/port.py turns a standalone seek(t) page into a HyperFrames composition."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import port  # noqa: E402

PAGE = """<!doctype html><html><head><title>R</title><style>
  html, body { width: 1080px; height: 1920px; overflow: hidden; }
</style></head><body>
<div id="stage"></div>
<div id="flash"></div>
<audio id="aud" src="assets/mix.wav" preload="auto"></audio>
<script>
function srcSet(img, src) { img.src = src; }
function seek(t) {}
if (!location.search.includes("render")) {
  loop();
}
</script>
</body></html>"""


def test_port_wraps_root_audio_and_registers():
    out = port.port(PAGE, 12.5, "assets/mix.wav", 1080, 1920)
    assert 'data-composition-id="main"' in out and 'data-duration="12.5"' in out
    assert '<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="12.5"' in out
    assert 'window.__timelines["main"] = timeline' in out, "literal registration so hyperframes lint sees it"
    assert "reelkit.stackSet(img, src)" in out
    assert "location.search" not in out
    assert 'local("Noto Color Emoji")' in out

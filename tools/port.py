"""Port a standalone seek(t) reel page into a HyperFrames composition (what `kinetix port` runs).

    python3 tools/port.py reel.html index.html --dur 60.8 [--mix assets/mix.wav] [--width 1080 --height 1920]

Expects the classic Kinetix page shape: <div id="stage">, overlay divs after it, an <audio id="aud">,
a global seek(t), loadFonts() and fitAll(), and an optional `if (!location.search.includes("render")) {...}`
preview block (replaced by bridge registration). Image swaps written as srcSet(img, src) become
pre-decoded stacks. Footage needs a hand edit: use <video data-start data-duration> instead of JPG sequences.
"""
import argparse
import re
from pathlib import Path


def port(src, dur, mix, w, h):
    def sub(old, new, required=True):
        nonlocal src
        if old not in src:
            if required:
                raise SystemExit(f"port: expected to find {old[:60]!r}")
            return
        src = src.replace(old, new, 1)

    # GSAP + bridge after <title>, emoji font declared for the renderer
    src = re.sub(r"(</title>)", r'\1\n<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>\n<script src="hf-bridge.js"></script>', src, count=1)
    src = re.sub(r"(<style>)", r'\1\n  @font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"); }', src, count=1)
    # one composition root around stage + overlays; the mix becomes a framework-owned track
    sub('<div id="stage"></div>', f'<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">\n<div id="stage"></div>')
    src = re.sub(r'<audio id="aud"[^>]*></audio>',
                 f'<audio id="mix" src="{mix}" data-start="0" data-duration="{dur}" data-track-index="10" data-volume="1"></audio>\n</div>', src, count=1)
    src = re.sub(r"(html, body \{[^}]*\})", r"\1\n  #root { position: relative; width: 100%; height: 100%; overflow: hidden; }", src, count=1)
    # image swaps toggle pre-decoded images instead of changing src at render time
    src = re.sub(r"function srcSet\(img, src\) \{.*?\n", "function srcSet(img, src) { reelkit.stackSet(img, src); }\n", src, count=1)
    # preview-mode audio loop -> bridge registration (literal __timelines so `hyperframes lint` sees it)
    reg = ('reelkit.register({ dur: %s, seek, before: async () => { await loadFonts(); fitAll(); } })\n'
           '  .then(({ timeline }) => { window.__timelines["main"] = timeline; });\n' % dur)
    new, n = re.subn(r'if \(!location\.search\.includes\("render"\)\) \{.*?\n\}\n', reg, src, count=1, flags=re.S)
    src = new if n else src.replace("</script>\n</body>", reg + "</script>\n</body>")
    return src


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--mix", default="assets/mix.wav")
    ap.add_argument("--width", type=int, default=1080); ap.add_argument("--height", type=int, default=1920)
    a = ap.parse_args()
    Path(a.out).write_text(port(Path(a.src).read_text(), a.dur, a.mix, a.width, a.height))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate a 40 s landscape kinetix demo for a project from a config.

    python3 gen.py strata|jitter|arvyo

Layout at 120 bpm (beat 0.5 s, bar 2 s):
  0-8    two hook scenes        8-12  brand slam
  12-28  four feature scenes    28-36 four stat slams       36-40 outro
Every claim comes from the project's own README; every image is a real one.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

HOME = Path.home()
HERE = Path(__file__).parent
P = Path(os.environ.get("PROJECTS", HOME / "Projects"))   # folder holding the strata, jitter and arvyo checkouts

THEMES = {
    "strata": dict(bg="#0d1117", accent="#f6a13c", ink="#0d1117", brand="#4ab5e8", hot="#ff5d5d", glow="246,161,60"),
    "jitter": dict(bg="#0d1117", accent="#a371f7", ink="#0d1117", brand="#4ab5e8", hot="#ff5d5d", glow="163,113,247"),
    "arvyo":  dict(bg="#0a1224", accent="#4ab5e8", ink="#0a1224", brand="#6B4FA8", hot="#f6a13c", glow="74,181,232"),
}

SRC = HERE / "src"
IMG = {
    "heat": (P / "strata/docs/images/report-heat.png", 1280, 840),
    "coupling": (P / "strata/docs/images/report-coupling.png", 1280, 840),
    "dig": (SRC / "dig.png", 1684, 1260),
    "hotspots": (SRC / "hotspots.png", 1652, 804),
    "knowledge": (P / "strata/docs/images/knowledge.png", 748, 330),
    "runtz": (P / "jitter/docs/images/run-tz.png", 876, 690),
    "study": (SRC / "study.png", 1484, 956),
    "freeze": (SRC / "freeze.png", 1484, 424),
    "four": (P / "arvyo/docs/images/pipeline-05_four_hypotheses.jpg", 1500, 1200),
    "tls": (P / "arvyo/docs/images/pipeline-03_tls_periodogram.jpg", 1500, 583),
    "wiz1": (P / "arvyo/docs/images/wiz-01-planet-transit.jpg", 1600, 731),
    "wiz2": (P / "arvyo/docs/images/wiz-02-eclipsing-binary.jpg", 1555, 790),
    "wiz3": (P / "arvyo/docs/images/wiz-03-blend-scenario.jpg", 1555, 790),
    "wiz4": (P / "arvyo/docs/images/wiz-04-starspot.jpg", 1555, 790),
}

KNOBS = ["order", "fsorder", "hashseed", "threads", "sleep", "gc", "tz", "clock", "locale", "env", "tmpdir", "load"]
knob_html = ("<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:18px;padding:34px;width:100%;height:100%;align-content:center'>"
             + "".join(f"<div class='kn' style='font:800 34px \"JetBrains Mono\",monospace;padding:20px 8px;border:3px solid var(--accent);"
                       f"border-radius:14px;text-align:center;color:var(--ink2)'>{k}</div>" for k in KNOBS) + "</div>")

numbers_html = ("<div style='display:flex;flex-direction:column;justify-content:center;gap:26px;width:100%;height:100%;padding:0 50px;font-family:\"JetBrains Mono\",monospace'>"
                "<div style='font-size:26px;color:#8b93c9;letter-spacing:.1em'>CHI-SQUARED, RAW</div>"
                "<div style='font-size:76px;font-weight:800;color:var(--ink2)'>planet <span style='color:var(--accent)'>19726.59</span></div>"
                "<div style='font-size:76px;font-weight:800;color:var(--ink2)'>blend&nbsp; <span style='color:var(--hot)'>19726.71</span></div>"
                "<div style='font-size:34px;color:#8b93c9'>difference 0.12 of ~19,700</div></div>")

CONFIGS = {
    "strata": dict(
        title="strata", bpm=120,
        hooks=[["EVERY TOOL SEES YOUR CODE", "<span class='hl acc'>RIGHT NOW</span>"],
               ["1,000 LINES UNTOUCHED SINCE 2019: <span class='acc'>FINE</span>", "200 LINES FOUR PEOPLE REWROTE LAST MONTH: <span class='hl hot'>RISK</span>"]],
        brand=("STRATA", "code archaeology", "git history × code shape → one HTML file"),
        features=[
            dict(tag="01 · HEAT", head=["WHERE THE", "RISK LIVES"], sub="complexity × recent change", chip="no server · no CDN · opens on a plane", img="heat", origin="68% 40%", zoom=.2),
            dict(tag="02 · HIDDEN COUPLING", head=["FILES THAT CHANGE", "TOGETHER"], sub="cli.py and test_cli.py: 53 commits, no import between them", chip="git shows coupling nobody wrote down", img="coupling", origin="55% 55%", zoom=.2),
            dict(tag="03 · THE RANKED LIST", head=["HOTTEST", "FILES FIRST"], sub="the longest file in Flask is not the hottest: almost nobody edits it", chip="one command: strata dig", img="hotspots", origin="30% 40%", zoom=.15),
            dict(tag="04 · WHO KNOWS WHAT", head=["THE BUS", "FACTOR"], sub="who owns what, and what only one person knows", chip="977 and 824 commits by two maintainers", img="knowledge", origin="0% 50%", zoom=.3),
        ],
        stats=[("129", "FILES", "Flask, analysed from a cold start"), ("3,816", "COMMITS", "sixteen years of history"),
               ("&lt;2", "SECONDS", "nothing installed but Python"), ("0", "DEPENDENCIES", "one HTML file out")],
        outro=("STRATA", "your repo already knows where it hurts", "github.com/nikhilcherry/strata"),
        music="minimal electronic pulse, warm analog synth pads, soft kick, calm and focused",
    ),
    "jitter": dict(
        title="jitter", bpm=120,
        hooks=[["YOUR CI ALREADY KNOWS", "THE TEST IS FLAKY", "<span class='hl acc'>IT NEVER SAID WHY</span>"],
               ["SO YOU RERUN IT.", "YOU ADD A <span class='hl hot'>SLEEP</span>.", "THEN IT FAILS ON A TUESDAY."]],
        brand=("JITTER", "find out why a test is flaky", "12 knobs · statistics · a repro that fails 10 of 10"),
        features=[
            dict(tag="01 · SHAKE", head=["TWELVE", "SOURCES OF CHAOS"], sub="pinned or shaken, and nothing else about the run changes", chip="order · hash seed · timezone · clock · threads", html=knob_html, w=900, h=620, zoom=0),
            dict(tag="02 · BLAME", head=["ONE KNOB OUT", "OF TWELVE"], sub="frozen: 0 of 12 trials fail. shaken: 6 of 12 fail.", chip="caused by tz", img="runtz", origin="0% 35%", zoom=.3),
            dict(tag="03 · REPRO", head=["A BUG WITH", "A REPRO"], sub="replay it, or export a standalone bash script", chip="verified: fails 8 of 8 replays", img="study", origin="0% 35%", zoom=.3),
            dict(tag="04 · CI GATE", head=["JITTER", "FREEZE"], sub="every knob pinned. non-zero exit if anything fails", chip="flakiness it cannot control gets said plainly", img="freeze", origin="0% 50%", zoom=.25),
        ],
        stats=[("12", "KNOBS", "isolated sources of nondeterminism"), ("0", "DEPENDENCIES", "and none coming"),
               ("10/10", "REPLAYS", "of the minimal repro"), ("263", "RUNS", "one minute to blame a timezone flake")],
        outro=("JITTER", "a flake that fails 10 of 10 is a bug", "github.com/nikhilcherry/jitter"),
        music="driving minimal techno, tight kick, tense arpeggio, dark and precise",
    ),
    "arvyo": dict(
        title="arvyo", bpm=120,
        hooks=[["A STAR DIMS.", "SOMETHING CROSSED IT.", "<span class='hl acc'>WHAT?</span>"],
               ["PLANET. ECLIPSING BINARY.", "BLEND. STARSPOT.", "ALL FOUR <span class='hl hot'>MAKE THE SAME DIP</span>"]],
        brand=("ARVYO", "works out what", "analysis by synthesis · TESS and Kepler"),
        features=[
            dict(tag="01 · FOUR HYPOTHESES", head=["REBUILD EACH", "FROM PHYSICS"], sub="fit all four to the same light curve, then rank them", chip="planet · eclipsing binary · blend · starspot", img="four", origin="50% 50%", zoom=.1),
            dict(tag="02 · PERIOD SEARCH", head=["ONE CLEAN PEAK"], sub="1.545 days, SDE 16.8 against a detection gate of 7.0", chip="within 0.013% of the recorded period", img="tls", origin="40% 50%", zoom=.3),
            dict(tag="03 · THE NEAR-TIE", head=["PLANET VS BLEND", "BY 0.12"], sub="a coin flip on raw chi-squared, so models are ranked by BIC", chip="found, explained and pinned in a test", html=numbers_html, w=900, h=560, zoom=0),
            dict(tag="04 · SEE IT", head=["BUILD ANY", "SCENARIO"], sub="arvyo-wiz: drag the physics, watch the light curve respond", chip="a 3D simulator for all four causes", imgs=["wiz1", "wiz2", "wiz3", "wiz4"], zoom=.06),
        ],
        stats=[("4", "HYPOTHESES", "fitted from physics, not pattern-matched"), ("0.013", "% ERROR", "period against the recorded value"),
               ("11", "REPOS", "standalone tools"), ("1", "CONTRACT", "one frozen data schema")],
        outro=("ARVYO", "Bharatiya Antariksh Hackathon 2026", "github.com/nikhilcherry/arvyo"),
        music="ambient electronic, slow evolving pads, soft pulse, spacious, cinematic and curious",
    ),
}

INDEX = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>__TITLE__ demo</title>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@500;700;800;900&family=JetBrains+Mono:wght@800&display=block" rel="stylesheet">
<link rel="stylesheet" href="kinetix.css">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="hf-bridge.js"></script>
<script src="vendor/remotion-noise.js"></script>
<script src="vendor/remotion-captions.js"></script>
<script src="vendor/remotion-layout-utils.js"></script>
<script src="kinetix.js"></script>
<style>
  @font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"); }
  html, body { width: 1920px; height: 1080px; }
  :root { --bg: __BG__; --accent: __ACCENT__; --accent-ink: __INK__; --brand: __BRAND__; --hot: __HOT__; --ink2: #e6edf3; --ca: 0; }
  .hl { transform: rotate(-1.5deg); }
  .sub { white-space: normal; width: 800px; font-weight: 700; font-size: 44px; line-height: 1.25; opacity: .9; }
  .chip { border-color: var(--accent); font-size: 34px; padding: 16px 26px; max-width: 800px; }
  .panel { box-shadow: 0 40px 120px rgba(__GLOW__, .28), 0 10px 40px rgba(0,0,0,.6); }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="40" data-width="1920" data-height="1080">
  <div id="stage"></div>
  <div id="caps"></div>
  <div id="glitch"></div><div id="vig"></div><div id="scan"></div><div id="grain"></div><div id="flash"></div>
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="40" data-track-index="10" data-volume="1"></audio>
</div>
<script>
const CFG = __CFG__;
const K = Kinetix.init({
  width: 1920, height: 1080, bpm: 120,
  build: [[4, 8]], drops: [[8, 12]], half: [[12, 28]], glitches: [8.0],
  fonts: ["100px Anton", "900 50px Inter", "700 50px Inter", "800 50px 'JetBrains Mono'"],
});
const { scene, slam, rise, tf, spring, clamp, lerp, easeOut, easeIO } = K;
const at = (x, y) => `left:${x}px;top:${y}px;`;
const fit = (w, h, mw, mh) => { const s = Math.min(mw / w, mh / h); return [Math.round(w * s), Math.round(h * s)]; };

// ---- hooks (0-8): two 4 s scenes, one line every second
CFG.hooks.forEach((lines, i) => {
  const gap = 170, y0 = 540 - (lines.length - 1) * gap / 2;
  scene(i * 4, i * 4 + 4,
    lines.map((l, j) => `<div class="c big l${j}" data-w="1760" style="${at(960, y0 + j * gap)}font-size:128px">${l}</div>`).join(""),
    (lt, q) => lines.forEach((_, j) => slam(q(".l" + j), lt, .25 + j * .9, { from: 1.7 })));
});

// ---- brand (8-12)
{
  const [name, tag, sub] = CFG.brand;
  scene(8, 12, `
    <div class="c glow" style="${at(960, 470)}width:1500px;height:1500px;border-radius:50%;background:radial-gradient(circle, rgba(__GLOW__,.45), transparent 60%)"></div>
    <div class="c ring" style="${at(960, 470)}width:520px;height:520px;border-radius:50%;border:12px solid var(--accent)"></div>
    <div class="c big name" data-w="1500" style="${at(960, 470)}font-size:300px">${name}</div>
    <div class="c mid s1" style="${at(960, 720)}">${tag}</div>
    <div class="c small mono s2" style="${at(960, 830)}font-size:34px;color:var(--accent)">${sub}</div>`,
    (lt, q) => {
      slam(q(".name"), lt, 0, { from: 3 });
      const sp = clamp(lt / .7); tf(q(".ring"), { s: lerp(.3, 4, easeOut(sp)), o: 1 - sp });
      tf(q(".glow"), { s: 1 + .06 * Math.exp(-((lt % K.B) / .12)) });
      rise(q(".s1"), lt, .7); rise(q(".s2"), lt, 1.3);
    });
}

// ---- features (12-28): copy left, real visual right
CFG.features.forEach((f, i) => {
  const t0 = 12 + i * 4, cx = 520, n = f.head.length;
  const subH = 112, tagH = 60, headGap = 135, chipH = 84;
  const total = tagH + 40 + n * headGap + 20 + subH + 36 + chipH;
  let y = 540 - total / 2;
  const yTag = y + tagH / 2; y += tagH + 40;
  const yHead = y + headGap / 2; y += n * headGap + 20;
  const ySub = y + subH / 2; y += subH + 36;
  const yChip = y + chipH / 2;
  const [iw, ih] = f.img ? [IMG[f.img][1], IMG[f.img][2]] : f.imgs ? [IMG[f.imgs[0]][1], IMG[f.imgs[0]][2]] : [f.w, f.h];
  const [pw, ph] = fit(iw, ih, 860, 640);
  const inner0 = f.html ? f.html : `<img class="im" src="${f.img ? IMG[f.img][0] : IMG[f.imgs[0]][0]}" style="position:absolute;left:0;top:0;width:100%;height:100%;object-fit:contain;display:block">`;
  const inner = `<div class="zm" style="position:relative;width:100%;height:100%;transform-origin:${f.origin || "50% 50%"}">${inner0}</div>`;
  scene(t0, t0 + 4, `
    <div class="c tag t0" style="${at(cx, yTag)}">${f.tag}</div>
    ${f.head.map((l, j) => `<div class="c big h${j}" data-w="800" style="${at(cx, yHead + j * headGap)}font-size:118px">${l}</div>`).join("")}
    <div class="c sub s" style="${at(cx, ySub)}">${f.sub}</div>
    <div class="chip ch" style="${at(cx, yChip)}">${f.chip}</div>
    <div class="pw" style="position:absolute;inset:0;perspective:2200px;pointer-events:none">
      <div class="panel" data-layout-allow-overflow style="position:absolute;left:${1420 - pw / 2}px;top:${540 - ph / 2}px;width:${pw}px;height:${ph}px;border-radius:18px;overflow:hidden;border:3px solid var(--accent);background:#0d1117;transform-origin:50% 50%">${inner}</div>
    </div>`,
    (lt, q) => {
      slam(q(".t0"), lt, .05, { from: 1.4 });
      f.head.forEach((_, j) => slam(q(".h" + j), lt, .25 + j * .25, { from: 1.5 }));
      rise(q(".s"), lt, .8, { dy: 40 }); rise(q(".ch"), lt, 1.4, { dy: 40 });
      const k = spring(lt - .3, 260, 26), p = q(".panel");
      p.style.opacity = clamp((lt - .25) / .2);
      p.style.transform = `translateX(${(1 - k) * 760}px) rotateY(${-11 * k}deg)`;
      q(".zm").style.transform = `scale(${1 + (f.zoom ?? .12) * easeOut(clamp((lt - .6) / 3.2))})`;
      if (f.imgs) KinetixBridge.stackSet(q(".im"), IMG[f.imgs[Math.min(f.imgs.length - 1, Math.floor(Math.max(0, lt - .6) / .85))]][0]);
    });
});

// ---- stats (28-36): one per bar
CFG.stats.forEach(([n, u, line], i) => scene(28 + i * 2, 30 + i * 2, `
  <div class="c big n" style="${at(960, 450)}font-size:380px">${n}<span class="acc" style="font-size:.34em;margin-left:18px">${u}</span></div>
  <div class="c mid l" style="${at(960, 760)}">${line}</div>`,
  (lt, q) => { slam(q(".n"), lt, 0, { from: 2.4, r: i % 2 ? 1.5 : -1.5 }); rise(q(".l"), lt, .15, { dur: .25 }); }));

// ---- outro (36-40)
{
  const [name, line, url] = CFG.outro;
  scene(36, 40, `
    <div class="c big name" data-w="1500" style="${at(960, 420)}font-size:280px">${name}</div>
    <div class="c mid b" style="${at(960, 650)}">${line}</div>
    <div class="c small mono u" style="${at(960, 790)}font-size:44px;color:var(--accent)">${url}</div>
    <div class="c small m" style="${at(960, 900)}font-size:30px;opacity:.6">open source · MIT</div>`,
    (lt, q) => {
      K.stage.style.background = "radial-gradient(circle at 50% 42%, rgba(__GLOW__,.22), var(--bg) 70%)";
      slam(q(".name"), lt, .05, { from: 2.6 }); rise(q(".b"), lt, .6); rise(q(".u"), lt, 1.1); rise(q(".m"), lt, 1.5);
      K.stage.style.opacity = 1 - clamp((lt - 3.3) / .6);
    });
}

K.start({ dur: 40 }).then(({ timeline }) => { window.__timelines["main"] = timeline; });
</script>
</body>
</html>
"""

MUSIC = r'''"""Soundtrack for the __TITLE__ demo: a MusicGen bed locked to 120 bpm, with hits on the same grid as the scenes."""
import hits as h
from hits import Mix
import os

DUR = 40.0
bed = "assets/bed.wav"
m = Mix(bed, bed_gain=1.0, seconds=DUR) if os.path.exists(bed) else Mix(bpm=120, seconds=DUR)
B = m.period; BAR = 4 * B
SR = h.SR

# hooks (0-8): filtered bed, an impact on each line, riser into a 0.4 s gap
m.lowpass([(0, 450), (7.4, 1100), (8.0, 14000)])
m.bed_level(0, 8, 0.55)
for base, nl in zip((0, 4), __HOOKN__):
    for j in range(nl):
        m.add(base + 0.25 + j * 0.9, h.impact()[: int(0.45 * SR)], 0.35)
m.add(5.6, h.riser(2.0), 0.8)
m.gap(7.6, 8.0)

# brand drop at 8.0
m.add(8.0, h.impact(), 0.95)
m.drums(8.0, h.kick(1.0)); m.drums(8.0, h.bass808(43.65, 3.2), 0.9)
m.bed_level(8, 36, 1.0)
for b in range(2, 14):           # bar downbeats from 12 onward: kick + clap on 2 and 4
    t = 8 + b * BAR
    if t >= 36: break
    m.drums(t, h.kick(0.8))
    m.drums(t + B, h.clap(), 0.8); m.drums(t + 3 * B, h.clap(), 0.8)
for i in range(4):               # a whoosh and a soft hit as each feature panel flies in
    t = 12 + i * 4
    m.add(t - 0.05, h.whoosh(0.5), 0.7); m.add(t + 0.3, h.impact()[: int(0.5 * SR)], 0.4)
    m.add(t + 1.4, h.sfx("interface/click_003"), 0.5)
m.lowpass([(28, 14000), (28.1, 14000)])
for i in range(4):               # stat slams
    t = 28 + i * 2
    m.add(t, h.impact()[: int(0.7 * SR)], 0.75); m.drums(t, h.kick(1.0))
m.add(34.0, h.riser(2.0), 0.6)

# outro: final hit, bed rings out under the fade
m.add(36.0, h.impact(), 0.9); m.drums(36.0, h.kick(1.0)); m.drums(36.0, h.bass808(43.65, 3.0), 0.8)
m.bed_level(36, 40, 0.6)
m.write("assets/mix.wav", fade=1.2)
print("mix written")
'''


def build(name):
    cfg = CONFIGS[name]
    th = THEMES[name]
    d = HERE / f"{name}-demo"
    if not d.exists():
        subprocess.run(["kinetix", "new", str(d), "--landscape"], check=True)
    (d / "assets").mkdir(exist_ok=True)
    for key in {f.get("img") for f in cfg["features"]} | {i for f in cfg["features"] for i in f.get("imgs", [])}:
        if key:
            shutil.copy(IMG[key][0], d / "assets" / IMG[key][0].name)
    # point image paths at assets/
    imgs_js = {k: [f"assets/{v[0].name}", v[1], v[2]] for k, v in IMG.items()}
    html = INDEX
    for k, v in dict(TITLE=name, BG=th["bg"], ACCENT=th["accent"], INK=th["ink"], BRAND=th["brand"], HOT=th["hot"], GLOW=th["glow"]).items():
        html = html.replace(f"__{k}__", v)
    html = html.replace("__CFG__", json.dumps(cfg, ensure_ascii=False))
    html = html.replace("const CFG =", "const IMG = " + json.dumps(imgs_js) + ";\nconst CFG =", 1)
    (d / "index.html").write_text(html)
    (d / "music.py").write_text(MUSIC.replace("__TITLE__", name).replace("__HOOKN__", str([len(x) for x in cfg["hooks"]])))
    print("built", d)


if __name__ == "__main__":
    build(sys.argv[1])

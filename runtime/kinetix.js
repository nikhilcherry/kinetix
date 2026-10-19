// Kinetix runtime: the scene engine for beat-synced reels.
//
// A reel is a list of scenes on a timeline. Every frame is a pure function of time t (seconds), so the
// same page previews in a browser and renders frame-exactly through HyperFrames (see bridge/hf-bridge.js).
//
//   const K = Kinetix.init({ width: 1080, height: 1920, bpm: 150, drops: [[16, 28.8]], half: [[28.8, 36.8]] });
//   K.scene(0, 3.2, `<div class="c big t" style="top:40%">HELLO</div>`, (lt, q) => K.slam(q(".t"), lt, 0));
//   K.start({ dur: 30 }).then(({ timeline }) => { window.__timelines["main"] = timeline; });
//
// Needs: gsap, hf-bridge.js, vendor/remotion-noise.js (smooth shake), optional vendor/remotion-captions.js
// and vendor/remotion-layout-utils.js. Markup: <div id="root" ...><div id="stage"></div> ... overlays ... </div>.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const easeOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const easeIO = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const hash = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  // damped spring 0 -> 1 with overshoot (closed form; k = stiffness, c = damping, mass 1)
  const spring = (t, k = 520, c = 22) => {
    if (t <= 0) return 0;
    const w0 = Math.sqrt(k), z = c / (2 * w0), wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + ((z * w0) / wd) * Math.sin(wd * t));
  };
  const noise = (key, x, y = 0) => (window.RemotionNoise ? RemotionNoise.noise2D(key, x, y) : (hash(x * 13.1 + y * 7.7 + key.length) - 0.5) * 2);

  function tf(el, { x = 0, y = 0, s = 1, r = 0, o = 1, blur = 0, center = true }) {
    el.style.opacity = o;
    el.style.transform = `${center ? "translate(-50%,-50%) " : ""}translate(${x}px,${y}px) scale(${s}) rotate(${r}deg)`;
    el.style.filter = blur > 0.3 ? `blur(${blur}px)` : "none";
  }
  // big punchy entrance: scales down from `from` on a spring, motion-blurred, optional exit at `out`
  function slam(el, lt, at, o = {}) {
    const { from = 1.9, dur = 0.16, out = null, outDur = 0.14, r = 0, center = true, x = 0, y = 0 } = o;
    const p = (lt - at) / dur;
    if (p < 0) { el.style.opacity = 0; return; }
    let op = clamp(p * 2.5), s = lerp(from, 1, spring(lt - at)), blur = (1 - clamp(p)) * 12;
    if (out != null && lt > out) { const k = clamp((lt - out) / outDur); op *= 1 - k; s *= 1 + 0.25 * k; blur += k * 10; }
    tf(el, { s, o: op, blur, r, center, x, y });
  }
  // softer entrance: rises into place
  function rise(el, lt, at, o = {}) {
    const { dur = 0.3, dy = 80, out = null, outDur = 0.2, center = true, x = 0 } = o;
    const p = easeOut((lt - at) / dur);
    let op = lt < at ? 0 : clamp(((lt - at) / dur) * 1.5);
    if (out != null && lt > out) op *= 1 - clamp((lt - out) / outDur);
    tf(el, { y: (1 - p) * dy, o: op, center, x });
  }
  // typewriter (grapheme-safe, so Devanagari/emoji don't split)
  const seg = typeof Intl !== "undefined" && Intl.Segmenter ? new Intl.Segmenter("en", { granularity: "grapheme" }) : null;
  function typeText(el, text, lt, at, dur) {
    const g = seg ? Array.from(seg.segment(text), (x) => x.segment) : Array.from(text);
    el.textContent = g.slice(0, Math.round(clamp((lt - at) / dur) * g.length)).join("");
    el.style.opacity = lt >= at ? 1 : 0;
  }

  function init(cfg) {
    const C = Object.assign({ width: 1080, height: 1920, bpm: 150, drops: [], half: [], build: [], flashes: [], glitches: [],
      shakeAt: [], fitWidth: null, fonts: [] }, cfg);
    const B = 60 / C.bpm, BAR = 4 * B;
    const stage = document.getElementById("stage");
    const $ = (id) => document.getElementById(id);
    const scenes = [];
    const glitchEl = $("glitch");
    if (glitchEl) glitchEl.innerHTML = "<i></i>".repeat(6);

    function scene(start, end, html, update) {
      const el = document.createElement("div");
      el.className = "scene";
      el.innerHTML = html;
      stage.appendChild(el);
      const q = (sel) => el.querySelector(sel), qa = (sel) => [...el.querySelectorAll(sel)];
      scenes.push({ start, end, el, update: (lt) => update(lt, q, qa) });
      return el;
    }

    // TikTok-style captions: @remotion/captions pages, paged per voice line (zone) so lines never merge
    let capPages = [];
    const capsEl = $("caps");
    if (window.CAPTIONS && window.RemotionCaptions && capsEl) {
      capPages = CAPTIONS.zones.flatMap((z) => RemotionCaptions.createTikTokStyleCaptions({
        captions: CAPTIONS.captions.filter((c) => c.startMs >= z.startMs && c.startMs < z.endMs),
        combineTokensWithinMilliseconds: C.captionPageMs || 1400 }).pages);
    }
    function renderCaps(t) {
      if (!capsEl) return;
      const ms = t * 1000;
      const zone = window.CAPTIONS && CAPTIONS.zones.find((z) => ms >= z.startMs && ms < z.endMs);
      const page = zone && capPages.filter((p) => p.startMs <= ms && p.startMs >= zone.startMs - 1).pop();
      if (!page) { capsEl.style.display = "none"; return; }
      capsEl.style.display = "block";
      capsEl.style.top = (zone.y ?? C.height * 0.78) + "px";
      const pop = spring((ms - page.startMs) / 1000, 380, 20);
      capsEl.style.transform = `translateY(-50%) scale(${0.55 + 0.45 * pop})`;
      capsEl.style.opacity = clamp((ms - page.startMs) / 60) * (1 - clamp((ms - (zone.endMs - 150)) / 150));
      capsEl.innerHTML = page.tokens.map((k) => {
        const on = ms >= k.fromMs && (ms < k.toMs || k === page.tokens[page.tokens.length - 1]);
        const cls = on ? "on" : ms < k.fromMs ? "next" : "";
        const bump = on ? 1 + 0.14 * (1 - spring((ms - k.fromMs) / 1000, 600, 26)) : 1;
        return `<span class="${cls}" style="transform:scale(${bump.toFixed(3)})">${k.text.trim()}</span>`;
      }).join("");
    }

    const inWin = (t, [a, b]) => t >= a && t < b;
    function seek(t) {
      stage.style.filter = "none"; stage.style.background = ""; stage.style.opacity = 1; stage.style.transform = "";
      if ($("vig")) $("vig").style.opacity = 0;
      renderCaps(t);
      for (const s of scenes) {
        const on = t >= s.start && t < s.end;
        s.el.style.display = on ? "block" : "none";
        if (on) s.update(t - s.start);
      }
      // beat camera: shake + zoom punch + chromatic aberration, strongest on bar downbeats inside drops
      let amp = 0, punch = 0, ca = 0, seedN = 0;
      const drop = C.drops.find((w) => inWin(t, w));
      const half = C.half.find((w) => inWin(t, w));
      const build = C.build.find((w) => inWin(t, w));
      if (drop) {
        const bi = Math.floor((t - drop[0]) / B), ph = (t - drop[0]) % B, bar = bi % 4 === 0;
        amp = (bar ? 15 : 6) * Math.exp(-ph / 0.07); punch = bar ? 0.03 * Math.exp(-ph / 0.12) : 0.01 * Math.exp(-ph / 0.08);
        ca = 2 + amp * 0.6; seedN = bi;
      } else if (half) {
        const ph = (t - half[0]) % BAR; amp = 5 * Math.exp(-ph / 0.1); ca = 1; seedN = Math.floor(t / BAR);
      } else if (build) {
        const ph = (t - build[0]) % BAR; amp = 10 * Math.exp(-ph / 0.08); punch = 0.02 * Math.exp(-ph / 0.1); ca = 1 + amp * 0.5; seedN = Math.floor(t / BAR);
      }
      for (const [at, strength = 1] of C.shakeAt) if (t >= at && t < at + 0.45) {
        const ph = t - at; amp += 24 * strength * Math.exp(-ph / 0.12); punch += 0.05 * strength * Math.exp(-ph / 0.15); ca += 8 * strength * Math.exp(-ph / 0.1);
      }
      const dx = amp * noise("sx", t * 11, seedN * 0.31) + 3 * noise("hx", t * 0.7);
      const dy = amp * noise("sy", t * 11, seedN * 0.31) + 3 * noise("hy", t * 0.7);
      stage.style.rotate = (0.25 * noise("hr", t * 0.5) + amp * 0.02 * noise("rr", t * 9, seedN)).toFixed(3) + "deg";
      stage.style.transform = `translate(${dx}px,${dy}px) scale(${1 + punch})`;
      document.documentElement.style.setProperty("--ca", ca.toFixed(2));
      // glitch slices on chosen cuts
      if (glitchEl) {
        let gl = 0;
        for (const at of C.glitches) if (t >= at && t < at + 0.25) gl = 1 - (t - at) / 0.25;
        [...glitchEl.children].forEach((g, i) => {
          const on = gl > 0 && hash(Math.floor(t * 30) + i) < 0.6;
          g.style.display = on ? "block" : "none";
          if (on) {
            g.style.top = hash(Math.floor(t * 30) * 7 + i) * C.height * 0.94 + "px";
            g.style.height = 18 + hash(i + Math.floor(t * 30)) * C.height * 0.06 + "px";
            g.style.transform = `translateX(${(hash(i * 3 + Math.floor(t * 30)) - 0.5) * 160 * gl}px)`;
          }
        });
      }
      // white flashes: drops by default, plus anything in cfg.flashes ([time, strength])
      let fl = 0;
      for (const [at, s] of [...C.drops.map((d) => [d[0], 1]), ...C.flashes]) if (t >= at) fl = Math.max(fl, s * Math.exp(-(t - at) / 0.12));
      for (const w of C.build) for (let k = 0; w[0] + k * BAR < w[1]; k++) { const at = w[0] + k * BAR; if (t >= at) fl = Math.max(fl, 0.2 * Math.exp(-(t - at) / 0.06)); }
      if ($("flash")) $("flash").style.opacity = fl.toFixed(3);
      if ($("scan")) $("scan").style.opacity = drop ? 0.45 : 0.22;
      if ($("grain")) $("grain").style.transform = `translate(${(hash(Math.floor(t * 24)) - 0.5) * 100}px,${(hash(Math.floor(t * 24) + 3) - 0.5) * 100}px)`;
      if (C.onFrame) C.onFrame(t);
    }

    // shrink one-line headlines that would overflow: @remotion/layout-utils fitText, shrink loop as backup
    function fitAll() {
      const maxDefault = C.fitWidth || C.width - 70;
      scenes.forEach((s) => (s.el.style.display = "block"));
      document.querySelectorAll(".c.big, .c.mid, .chip").forEach((el) => {
        const cs = getComputedStyle(el), max = parseFloat(el.dataset.w || maxDefault);
        let fs = parseFloat(cs.fontSize);
        if (el.scrollWidth > max && cs.whiteSpace === "nowrap" && window.RemotionLayoutUtils) {
          try {
            const fit = RemotionLayoutUtils.fitText({ text: el.textContent, withinWidth: max, fontFamily: cs.fontFamily,
              fontWeight: cs.fontWeight, textTransform: cs.textTransform, letterSpacing: cs.letterSpacing });
            fs = Math.min(fs, Math.floor(fit.fontSize)); el.style.fontSize = fs + "px";
          } catch (e) { /* fall through */ }
        }
        while (el.scrollWidth > max && fs > 24) { fs -= 4; el.style.fontSize = fs + "px"; }
      });
      scenes.forEach((s) => (s.el.style.display = "none"));
    }
    const loadFonts = () => Promise.all(C.fonts.map((f) => document.fonts.load(f, "AB"))).then(() => document.fonts.ready);

    function start({ dur }) {
      return reelkit.register({ dur, seek, before: async () => { await loadFonts(); fitAll(); } });
    }

    return { B, BAR, stage, scene, seek, start, fitAll, renderCaps,
      tf, slam, rise, typeText, spring, noise, clamp, lerp, easeOut, easeIO, hash };
  }

  window.Kinetix = { init, tf, slam, rise, typeText, spring, noise, clamp, lerp, easeOut, easeIO, hash };
})();

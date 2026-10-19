// Kinetix bridge: run a seek(t)-style reel page as a HyperFrames composition.
//
// A reel page draws every frame from time alone (window.seek(t)). HyperFrames seeks one paused
// GSAP timeline, so we register a single linear tween over a proxy whose onUpdate calls seek().
// That gets the reel `hyperframes check` (layout, overlap, contrast) and its parallel renderer
// without rewriting a single scene.
//
// Usage, after the page defines seek/DUR/loadFonts/fitAll:
//   <script src="gsap.min.js"></script> <script src="hf-bridge.js"></script>
//   reelkit.register({ dur: DUR, seek, before: async () => { await loadFonts(); fitAll(); } })
//     .then(({ timeline }) => { window.__timelines["main"] = timeline; });   // literal, so `hyperframes lint` sees it
(function () {
  // Image swaps (screen A -> screen B) must not change `src` at render time: the capture can land
  // before the new image decodes. stackSet keeps one <img> per source and toggles visibility.
  const stacks = new WeakMap();
  function stackSet(img, src) {
    let s = stacks.get(img);
    if (!s) {
      s = { [img.getAttribute("src")]: img };
      stacks.set(img, s);
    }
    if (!s[src]) {
      const c = img.cloneNode(false);
      c.removeAttribute("id");
      c.setAttribute("src", src);
      img.parentNode.insertBefore(c, img.nextSibling);
      s[src] = c;
    }
    for (const [k, el] of Object.entries(s)) el.style.visibility = k === src ? "visible" : "hidden";
  }

  async function register({ dur, seek, before, prewarmStep = 0.1 }) {
    if (before) await before();
    // walk the whole timeline once so every stacked image variant exists, then decode them all
    for (let t = 0; t < dur; t += prewarmStep) seek(t);
    await Promise.all([...document.images].map((i) => i.decode().catch(() => {})));
    seek(0);
    const proxy = { t: 0 };
    const tl = gsap.timeline({ paused: true });
    tl.to(proxy, { t: dur, duration: dur, ease: "none", onUpdate: () => seek(proxy.t) }, 0);
    // wrapped on purpose: a GSAP timeline is a thenable (its .then fires when it *finishes*), so returning
    // it bare from an async function would wait forever on a paused timeline
    return { timeline: tl };
  }

  window.KinetixBridge = window.reelkit = { register, stackSet };
})();

# Kinetix runtime API (`runtime/kinetix.js`)

A page loads, in order:
- GSAP
- `hf-bridge.js`
- `vendor/remotion-noise.js`
- (optional) `vendor/remotion-captions.js` and `vendor/remotion-layout-utils.js`
- `kinetix.js`
- `kinetix.css`

`kinetix new` and `kinetix sync` copy these into the reel folder.

## Page skeleton

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="19.2" data-width="1080" data-height="1920">
  <div id="stage"></div>                  <!-- scenes are appended here -->
  <div id="caps"></div>                   <!-- optional TikTok captions -->
  <div id="glitch"></div><div id="vig"></div><div id="scan"></div><div id="grain"></div><div id="flash"></div>
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="19.2" data-track-index="10" data-volume="1"></audio>
</div>
```

**HyperFrames rules that apply:**
- every `<audio>` needs an `id`
- the root carries `data-duration`
- the page must contain the literal `window.__timelines["main"] = …`

## `Kinetix.init(config)` → `K`

| key | meaning |
|---|---|
| `width`, `height` | canvas size, e.g. 1080×1920 or 1920×1080 |
| `bpm` | grid tempo. `K.B` = one beat in seconds, `K.BAR` = 4 beats |
| `build: [[a, b]]` | windows with a pulsing camera and a small flash every bar |
| `drops: [[a, b]]` | heavy beat camera (bar downbeats strongest) plus a white flash at `a` |
| `half: [[a, b]]` | gentle half-time pulse |
| `glitches: [t, ...]` | RGB slice glitch for 0.25 s at each time |
| `flashes: [[t, strength]]` | extra white flashes |
| `shakeAt: [[t, strength]]` | one-off hits (vine boom, buzzer) |
| `fonts: ["100px Anton", ...]` | loaded before layout, so fitting measures real glyphs |
| `fitWidth` | max one-line headline width (default `width - 70`); per element: `data-w="980"` |
| `captionPageMs` | words per caption page window (default 1400) |
| `onFrame(t)` | your own per-frame hook (moving backgrounds etc.) |

## Scenes

```js
K.scene(start, end, html, (lt, q, qa) => { ... })
```

- `lt` is scene-local time in seconds.
- `q(sel)` and `qa(sel)` query inside the scene.
- The scene is hidden outside `[start, end)`.
- The update must be a **pure function of `lt`**: no `Date.now`, no randomness (use `K.hash(n)`), no accumulated state.

## Motion helpers (all pure)

| helper | does |
|---|---|
| `K.slam(el, lt, at, {from=1.9, dur=.16, out, outDur, r, x, y})` | punchy scale-down entrance on a spring, motion blur, optional exit at `out` |
| `K.rise(el, lt, at, {dur=.3, dy=80, out})` | softer rise into place |
| `K.tf(el, {x, y, s, r, o, blur})` | set the transform directly (centred elements) |
| `K.typeText(el, text, lt, at, dur)` | grapheme-safe typewriter (Devanagari and emoji safe) |
| `K.spring(t, k=520, c=22)` | 0 → 1 with overshoot; `t` is seconds since start |
| `K.noise(key, x, y)` | smooth noise in −1..1 (`@remotion/noise`) |
| `K.clamp`, `K.lerp`, `K.easeOut`, `K.easeIO`, `K.hash(n)` | the usual |

**Centring:** `.c` elements are centred on their inline `left`/`top` px. Animate them with the helpers (they keep the `translate(-50%,-50%)`).

## CSS classes (`kinetix.css`)

| class | for |
|---|---|
| `.big` | display headline (Anton, uppercase, chromatic shadow driven by `--ca`) |
| `.mid` | 72px heavy sans |
| `.small` | 42px secondary |
| `.mono` | code / data text |
| `.hl` | highlight box. Variants: `.hl.acc` (accent), `.hl.hot` (pink) |
| `.tag` | pill label |
| `.chip` | bordered callout |
| `.phone` | device frame for screenshots and recordings |
| `#caps span.on` / `.next` | caption word states |

Theme with `:root { --bg; --ink; --accent; --accent-ink; --hot; --brand; --display; --ui; --mono }`.

## Captions

Set `window.CAPTIONS` by loading `assets/captions.js` (from `kinetix captions`) before `kinetix.js`, and include `<div id="caps">`. Each voice line is a zone with its own `y`. Its words show as pages, the spoken word is boxed in the accent colour, and upcoming words are dimmed.

## Bridge

`KinetixBridge.register({ dur, seek, before })` resolves to `{ timeline }`. `K.start({ dur })` wraps it.

`KinetixBridge.stackSet(img, src)` swaps an image without a decode race. Use it for screen A → B changes.

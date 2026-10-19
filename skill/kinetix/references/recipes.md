# Scene recipes

Lifted from the demo reels (`examples/connect`, `examples/chaukanna`). Times are scene-local (`lt`).

## Hook: POV words popping in

```js
K.scene(0, 3.2, `
  <div class="c tag t0" style="left:540px;top:520px">POV</div>
  <div class="c big t1" style="left:540px;top:760px;font-size:150px">YOU NEED A REEL</div>
  <div class="c big t2" style="left:540px;top:930px;font-size:170px"><span class="hl hot">BY TONIGHT</span> 💀</div>`,
  (lt, q) => { K.slam(q(".t0"), lt, .1, { from: 1.4 }); K.slam(q(".t1"), lt, .4); K.slam(q(".t2"), lt, 1.2, { from: 2.6, r: -2 }); });
```

## Logo drop with shockwave ring and a glow that pumps on the beat

```js
K.scene(16, 19.2, `
  <div class="c glow" style="left:540px;top:800px;width:1400px;height:1400px;border-radius:50%;background:radial-gradient(circle, rgba(90,69,201,.6), transparent 60%)"></div>
  <div class="c ring" style="left:540px;top:800px;width:420px;height:420px;border-radius:50%;border:14px solid var(--accent)"></div>
  <div class="c big name" style="left:540px;top:800px;font-size:230px">BRAND</div>`,
  (lt, q) => {
    K.slam(q(".name"), lt, 0, { from: 3 });
    const sp = K.clamp(lt / .6); K.tf(q(".ring"), { s: K.lerp(.3, 4, K.easeOut(sp)), o: 1 - sp });
    K.tf(q(".glow"), { s: 1 + .08 * Math.exp(-((lt % K.B) / .1)) });
  });
```

## Phone with a real screen, swapped on a tap

```js
`<div class="phone ph" style="top:1150px"><img class="scr" src="assets/screen-a.png"></div><div class="ripple"></div>`
// update:
KinetixBridge.stackSet(q(".scr"), lt > .8 ? "assets/screen-b.png" : "assets/screen-a.png");
```

For web screenshots, add a fake status bar strip so the phone's notch doesn't cover content (see `examples/connect`).

## Real footage on a tilted "hologram" panel, zooming into the action

```html
<div class="holo-wrap" style="position:absolute;left:0;right:0;top:720px;perspective:1500px;display:flex;justify-content:center">
  <div class="holo" data-layout-allow-overflow style="position:relative;width:1000px;height:640px;overflow:hidden;border:4px solid var(--accent);transform:rotateX(24deg)">
    <div class="pan" style="position:absolute;left:0;top:0;width:1360px;height:800px;transform-origin:0 0">
      <video src="assets/clip.mp4" muted playsinline data-start="24.0" data-duration="3.2" data-media-start="1.6" style="width:1360px;height:800px"></video>
    </div></div></div>
```

```js
// centre the source point (cx, cy) at scale s inside a w x h window
const panTo = (el, w, h, cx, cy, s) => el.style.transform = `translate(${w/2 - cx*s}px, ${h/2 - cy*s}px) scale(${s})`;
panTo(q(".pan"), 1000, 640, K.lerp(680, 430, z), K.lerp(400, 300, z), K.lerp(.74, 1.7, z));   // z = K.easeIO(lt / 3)
```

`data-start` on the video is in **reel time**. Animate the `.pan` wrapper, never the video element.

## Stat slam, one per bar

```js
STATS.forEach(([n, unit, line], i) => K.scene(36.8 + i * K.BAR, 36.8 + (i + 1) * K.BAR, `
  <div class="c big n" style="left:540px;top:760px;font-size:330px">${n}<span class="acc" style="font-size:.45em">${unit}</span></div>
  <div class="c mid l" style="left:540px;top:1040px">${line}</div>`,
  (lt, q) => { K.slam(q(".n"), lt, 0, { from: 2.6, r: i % 2 ? 2 : -2 }); K.rise(q(".l"), lt, .2); }));
```

Only real numbers from the product.

## Counter rolling down to the claim

```js
const v = Math.round(K.lerp(999, 50, K.easeOut((lt - .3) / 1.3)));
q(".n").innerHTML = lt > 1.6 ? "&lt;50" : String(v);
```

## Chat bubbles sliding in on a spring

```js
CHAT.forEach((m, i) => { const t0 = .4 + i * .6, k = K.spring(lt - t0, 380, 22), el = q(".b" + i);
  el.style.opacity = lt > t0 ? 1 : 0;
  el.style.transform = `translateX(${(1 - k) * (m.side === "r" ? 400 : -400)}px) scale(${.7 + .3 * k})`; });
```

## Typed hex / data stream

```js
let hx = ""; for (let k = 0; k < Math.floor(K.clamp((lt - .2) / .9) * 80); k++) hx += Math.floor(K.hash(k * 3.7 + 1) * 256).toString(16).padStart(2, "0") + " ";
q(".hex").textContent = hx + (Math.floor(lt * 8) % 2 ? "▍" : "");
```

## Live signal traces (SVG polyline from noise)

```js
for (let k = 0; k <= 100; k++) pts += `${k * 10},${140 - K.noise("s", lt * 6 + k * .09) * 60} `;
q(".wave").setAttribute("points", pts);
```

## Freeze-frame "beat"

In the scene update: `K.stage.style.filter = lt < .9 ? "grayscale(1) contrast(1.3)" : "none";`. Pair it with a screech in `music.py` and a near-silence on the bed.

## Landscape

Use split layouts: copy on the left (x ≈ 560), visuals on the right (x ≈ 1380). Footage panels get much bigger, and `rotateY` reads better than `rotateX`. Keep the same timeline and `mix.wav`, so the vertical and 16:9 cuts share a soundtrack.

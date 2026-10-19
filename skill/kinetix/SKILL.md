---
name: kinetix
description: Make beat-synced vertical (or 16:9) promo reels from code with the Kinetix pipeline — scenes as HTML/JS, a MusicGen or pure-synth soundtrack with drops placed by beat, word-timed captions, Remotion light leaks and stingers, a HyperFrames quality gate, and a render with a baked-in thumbnail. Use when someone asks for a reel, Short, TikTok, hype/launch/demo video, "make a video about my app/project", or wants to edit/re-cut one made with Kinetix.
---

# Kinetix: reels from code

Kinetix lives in a repo (find it: `kinetix` on PATH, `$KINETIX_HOME`, or a `kinetix/` checkout with `runtime/kinetix.js`).
All commands below are `kinetix <cmd>`; run `kinetix doctor` first and `./setup.sh` if pieces are missing.

The model: **every frame is a pure function of time.** A reel is `index.html` with scenes on a timeline; the
soundtrack is built by `music.py` on the *same* beat grid, so cuts, shakes and drops land together.

## 1. Gather real material first

- **The story comes from the product's own words.** Read its README, site copy, and app strings, and quote them. Never invent stats, users, awards or speeds.
- **Show the real thing.** Use app screenshots, screen recordings, or a live web page captured with Playwright at 2× DPI. If capturing would hit a live backend, mock the API in the browser (`page.route`) rather than creating real records. Label simulated or demo footage as such.
- **Pick numbers once.** If sources disagree (1.2 s vs 1.5 s), use one value consistently and say which in the hand-off.
- **Voice is optional.** For voice lines, use a TTS API the user has a key for (`tools/tts_sarvam.py` for Indian languages), then `kinetix captions`.

## 2. Plan on the grid

At 150 bpm a beat is 0.4 s and a bar is 1.6 s. Every section boundary and every big hit goes on a beat. A proven 50–60 s shape:

| section | bars | job |
|---|---|---|
| cold open | 3 | relatable hook in 2 s: POV + the pain |
| build | 6–7 | escalate on bar cuts, then a riser |
| **gap** | ¼ | 0.4 s of near-silence ("until now…") |
| drop 1 | 8 | logo slam, then the product flow, one beat per action |
| half-time | 4–5 | the twist or the depth, filtered and quieter |
| drop 2 | 8–10 | rapid flex: footage, real stats, proof |
| outro | 3 | logo, tagline, URL, fade |

**Text must be readable.** Fast in, then hold: about 0.8 s for a label and 0.3 s per word for a sentence. Sequential text goes on every *other* beat. Only non-text accents may hit every beat.

## 3. Build the reel

```bash
kinetix new my-reel            # vertical; add --landscape for 1920x1080
```

`my-reel/index.html` uses the runtime (`references/runtime.md`):

```js
const K = Kinetix.init({ width: 1080, height: 1920, bpm: 150, build: [[3.2, 9.2]], drops: [[9.6, 16]], glitches: [9.6], fonts: [...] });
K.scene(9.6, 12.8, `<div class="c big t" style="left:540px;top:800px;font-size:230px">BRAND</div>`,
  (lt, q) => K.slam(q(".t"), lt, 0, { from: 3 }));
K.start({ dur: 19.2 }).then(({ timeline }) => { window.__timelines["main"] = timeline; });  // keep this literal
```

Scene patterns (phone frames, hologram footage panels, stat slams, chat bubbles, counters, typing) are in `references/recipes.md`.
Stay on brand: take colours, fonts and the logo from the product, and theme them through the `:root` variables in `kinetix.css`.

## 4. Build the soundtrack (`references/music.md`)

- **Bed:** `kinetix music gen "<genre, instruments, mood>" --bpm 150 --seconds 60 -o my-reel/assets/bed.wav`. MusicGen follows the BPM in the prompt, and the tool time-stretches to the exact grid and writes `bed.json`. Without a GPU or MusicGen, `Mix(bpm=150, seconds=DUR)` builds a pure-synth mix.
- **`music.py`:** `m = Mix("assets/bed.wav", seconds=DUR)`, then:
  - place hits by the same times as the scenes: `m.add(t, h.impact())`, `m.drums(...)`, `m.sfx("impact/...")`
  - shape the arrangement: `m.lowpass([(t, hz), ...])`, `m.bed_level(...)`, `m.gap(14.0, 14.4)`
  - then run `kinetix mix my-reel`.
- **Check the dynamics** (you can't listen, so measure). RMS per section should rise from build to drop, dip at half-time, and peak at the drops. If the build is louder than the drop, turn the build's synth layers down. Also render a spectrogram (`ffmpeg ... showspectrumpic`) and look at it.
- **Voices:** after mixing, confirm they're audible with Whisper on the mixed segment.

## 5. Captions (optional, needs voice)

`captions-lines.json` holds `[{"clip": "assets/line1.wav", "at": 1.62, "text": "exact script", "y": 600}]`. Then run `kinetix captions my-reel`. Whisper runs in English mode with the script as its prompt, so Hinglish and other romanised lines keep their spelling. Pages are built per line.

## 6. Verify: look, then gate

1. **`kinetix snap my-reel 1.5,4,9,...`**, one time per scene. Open the contact sheets and actually look. A blank frame means a JS error or an unregistered timeline.
2. **`kinetix check my-reel`** samples every ½ s, and must end with **0 errors**.
   - Fix real findings: text overflowing its box, overlaps, hidden text, contrast.
   - Mark only *intentional* layering, never real problems: `data-layout-allow-overlap` for a stamp over a document, `data-layout-allow-occlusion` for text deliberately on top of a sprite, `data-layout-allow-overflow` for a cropped screenshot in a frame, `data-layout-ignore` for a decorative background or huge faded emoji.
   - Before claiming a "fix" was visible, compare the before and after frames. Some findings are checker false positives.

## 7. Effects and render

```bash
kinetix fx leak --hue 200 -o overlays/leak-cyan.mov        # hue: 0 amber, 70 pink, 200 cyan, 290 lime
kinetix fx stinger --colors "#c8ff3d,#5a45c9" -o overlays/stinger.mov
kinetix render my-reel -o out.mp4 --overlay overlays/leak-cyan.mov@15.6:0.8 --overlay overlays/stinger.mov@28.5 --poster 18.3
```

- **Leaks:** `leak-*` files are *screened* in as light, so text stays readable. Start a leak ~0.4 s before a drop so it peaks on it, and don't let one peak on a logo slam.
- **Stingers:** start ~0.3 s before a cut so the panel covers it.
- **Poster:** `--poster` bakes the best settled frame in as frame 0, which is the thumbnail on X, YouTube, Slack and Discord. Pick a logo card or the money shot, never a frame mid-animation or on a flash.
- **Final check:** pull frames from the final mp4 (frame 0, each overlay peak, each footage scene) and look at them.

## Gotchas (all hit for real)

- **The bridge returns `{ timeline }`, not the timeline.** A GSAP timeline is a thenable, so returning it bare from an async function hangs forever and every frame renders blank.
- **Highlight boxes on display fonts need `line-height: 1.12`** (already in `kinetix.css`), or glyphs poke out and `check` flags `text_box_overflow`.
- **Footage must be `<video muted data-start data-duration [data-media-start]>`** in a non-timed wrapper, never JPG sequences. Animate the wrapper, not the video.
- **Image swaps (screen A → B) use `KinetixBridge.stackSet(img, src)`**, which pre-decodes the variants. Setting `src` at render time captures undecoded frames.
- **Every named font needs `@font-face`.** For the system emoji font, declare `src: local("Noto Color Emoji")`.
- **MusicGen beds:** librosa's `beat_track` misreads phonk and club tempos (it called 150 bpm "121" and "199"), which is why `hypebeat` uses onset autocorrelation and caps stretching at ±12%. musicgen-medium needs ~8 GB of free RAM to load; small is the default.
- **Captions:** pooling all lines into one `createTikTokStyleCaptions` call merges the last word of a line into the next, so page per line (the runtime does).
- **Remotion:** render with `--gl=swangle` (software GL works everywhere) and as ProRes 4444 with alpha. ffmpeg's VP9 decoder drops alpha.
- **Licences:**
  - MusicGen output is CC-BY-NC, fine for demos and personal channels, not for paid work.
  - Remotion is free for individuals and companies of up to 3 people.
  - Bundled SFX are CC0.

## Hand-off

Tell the user:
- where the mp4 is
- what's in it, as a short beat-by-beat list
- what you verified and how (contact sheets, check result, loudness)
- any number or claim choices you made
- what you could not verify (you cannot hear it; ask them to listen)

Offer to post, but don't post without a yes.

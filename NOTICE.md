# Third-party notices

Kinetix's own code is MIT (see `LICENSE`). It builds on these, which keep their own licences:

| component | how it's used | licence |
|---|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) | `npm` dependency: lint/check/snapshot/render | Apache-2.0 |
| [Remotion](https://www.remotion.dev) (`remotion`, `@remotion/cli`, `@remotion/light-leaks`, `@remotion/transitions`) | `npm` dependency in `fx/` for overlay rendering; not redistributed | [Remotion License](https://www.remotion.dev/license): free for individuals and companies with up to 3 employees, otherwise a company licence |
| `@remotion/captions`, `@remotion/noise`, `@remotion/layout-utils` | bundled locally into `vendor/` by `setup.sh` (not committed) | MIT |
| GSAP | loaded from jsDelivr by reel pages | GreenSock standard licence (free) |
| [MusicGen](https://huggingface.co/facebook/musicgen-small) weights | downloaded on first `kinetix music gen` | CC-BY-NC 4.0: generated beds are for non-commercial use |
| Sound effects in `music/sfx/` | Kenney (kenney.nl), "Keyboard Soundpack #1" by unicae_games | CC0 1.0 |
| faster-whisper | optional, for captions | MIT |

Example media: the Connect and Chaukanna screenshots, recordings and voice lines are from those projects by the same author and are included here as demo material under this repo's MIT licence. Voices were generated with Sarvam bulbul TTS.

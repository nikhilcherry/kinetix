// Kinetix effects factory: Remotion renders reusable transparent overlays (ProRes 4444 + alpha),
// which tools/overlay.sh (or `kinetix render --overlay`) composites onto a reel at a beat time.
// Leak/Stinger are 1080x1920; LeakH/StingerH are 1920x1080. Add your own compositions here.
import React from "react";
import { AbsoluteFill, Composition } from "remotion";
import { LightLeak } from "@remotion/light-leaks";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { iris } from "@remotion/transitions/iris";

const W = 1080, H = 1920, FPS = 30;

type LeakProps = { seed: number; hueShift: number };
const Leak: React.FC<LeakProps> = ({ seed, hueShift }) => (
  <AbsoluteFill>
    <LightLeak seed={seed} hueShift={hueShift} />
  </AbsoluteFill>
);

type StingerProps = { a: string; b: string };
const Panel: React.FC<{ color: string; ring?: string }> = ({ color, ring }) => (
  <AbsoluteFill style={{ background: color }}>
    {ring ? <AbsoluteFill style={{ margin: 70, borderRadius: 60, background: ring }} /> : null}
  </AbsoluteFill>
);
// clock-wipes a lime panel in, holds a beat with a violet core, irises back out to transparent
const Stinger: React.FC<StingerProps & { w?: number; h?: number }> = ({ a, b, w = W, h = H }) => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={10}>
      <AbsoluteFill />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={clockWipe({ width: w, height: h })} timing={linearTiming({ durationInFrames: 8 })} />
    <TransitionSeries.Sequence durationInFrames={14}>
      <Panel color={a} ring={b} />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={iris({ width: w, height: h })} timing={linearTiming({ durationInFrames: 8 })} />
    <TransitionSeries.Sequence durationInFrames={10}>
      <AbsoluteFill />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Leak" component={Leak} durationInFrames={24} fps={FPS} width={W} height={H} defaultProps={{ seed: 3, hueShift: 0 }} />
    <Composition id="LeakH" component={Leak} durationInFrames={24} fps={FPS} width={H} height={W} defaultProps={{ seed: 3, hueShift: 0 }} />
    <Composition id="StingerH" component={Stinger} durationInFrames={10 + 14 + 10 - 8 - 8} fps={FPS} width={H} height={W}
      defaultProps={{ a: "#3fd0ff", b: "#0f4c81", w: H, h: W }} />
    <Composition id="Stinger" component={Stinger} durationInFrames={10 + 14 + 10 - 8 - 8} fps={FPS} width={W} height={H}
      defaultProps={{ a: "#c8ff3d", b: "#5a45c9" }} />
  </>
);

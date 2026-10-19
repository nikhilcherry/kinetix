#!/usr/bin/env bash
# Composite Remotion-rendered overlays (overlays/*.mov, ProRes 4444 with alpha) onto a reel.
#   overlay.sh in.mp4 out.mp4 overlays/leak-warm.mov@15.6:0.7:screen overlays/stinger-lime.mov@28.5 ...
#   each arg is file@start[:opacity[:mode]]
#     mode screen (default for leak-*): added as light, like film exposure, so the picture stays readable
#     mode over   (default otherwise):  normal alpha overlay, for opaque stingers/wipes
# audio is copied untouched
set -euo pipefail
in=$1; out=$2; shift 2
IFS=x read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$in")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")

inputs=(-i "$in"); chain=""; k=1; light=""; overs=()
# light layer: every screen-mode overlay is premultiplied onto one black canvas, then screened in once
chain+="color=c=black:s=${W}x${H}:r=30:d=$DUR,format=gbrp[L0];"
for spec in "$@"; do
  file=${spec%@*}; rest=${spec##*@}
  IFS=: read -r at op mode <<< "$rest"
  op=${op:-1}
  [[ -z ${mode:-} ]] && { [[ $(basename "$file") == leak-* ]] && mode=screen || mode=over; }
  inputs+=(-i "$file")
  if [[ $mode == screen ]]; then
    chain+="[$k:v]format=yuva444p,colorchannelmixer=aa=$op,setpts=PTS-STARTPTS+$at/TB[s$k];"
    chain+="[L$((${#light} ))][s$k]overlay=eof_action=pass:format=gbrp[L$((${#light} + 1))];"
    light+="x"
  else
    overs+=("$k:$at:$op")
  fi
  k=$((k + 1))
done
prev="0:v"
if [[ -n $light ]]; then
  chain+="[0:v]format=gbrp[B];[B][L${#light}]blend=all_mode=screen:shortest=1,format=yuv420p[V0];"
  prev="V0"
fi
n=0
for o in "${overs[@]}"; do
  IFS=: read -r idx at op <<< "$o"
  chain+="[$idx:v]format=yuva444p,colorchannelmixer=aa=$op,setpts=PTS-STARTPTS+$at/TB[o$idx];"
  chain+="[$prev][o$idx]overlay=eof_action=pass:format=auto[W$n];"
  prev="W$n"; n=$((n + 1))
done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${chain%;}" -map "[$prev]" -map 0:a? \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a copy -movflags +faststart "$out"
echo "$out ($((k - 1)) overlays: ${#light} screen, ${#overs[@]} over)"

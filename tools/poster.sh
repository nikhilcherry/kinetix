#!/usr/bin/env bash
# Bake the best frame in as frame 0, so X/YouTube/Slack/Discord thumbnails show it (they grab frame 0).
#   poster.sh in.mp4 <seconds> [out.mp4]     also writes <out>.jpg for platforms that take a custom thumbnail
set -euo pipefail
in=$1; at=$2; out=${3:-${in%.mp4}-poster.mp4}
jpg=${out%.mp4}.jpg
ffmpeg -v error -y -ss "$at" -i "$in" -frames:v 1 -q:v 2 "$jpg"
ffmpeg -v error -y -i "$in" -i "$jpg" -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]" \
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a copy -movflags +faststart "$out"
echo "$out (poster $jpg from ${at}s)"

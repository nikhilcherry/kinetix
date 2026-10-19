#!/usr/bin/env bash
# Bundle the MIT @remotion helpers the runtime uses into browser globals: vendor/remotion-*.js
#   RemotionCaptions (TikTok-style caption pages), RemotionNoise (smooth shake), RemotionLayoutUtils (fitText)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor fx/.entries
for p in captions noise layout-utils; do
  g=Remotion$(echo "$p" | sed -E 's/(^|-)(.)/\U\2/g')
  echo "export * from '@remotion/$p';" > "fx/.entries/$p.js"
  fx/node_modules/.bin/esbuild "fx/.entries/$p.js" --bundle --format=iife --global-name="$g" --minify \
    --outfile="vendor/remotion-$p.js" --log-level=warning
  echo "vendor/remotion-$p.js -> window.$g"
done

#!/usr/bin/env bash
# Kinetix setup.   ./setup.sh [--musicgen] [--captions] [--skill]
#   --musicgen  install torch + transformers for `kinetix music gen` (large download)
#   --captions  install faster-whisper for `kinetix captions`
#   --skill     link skill/kinetix into ~/.claude/skills so Claude Code can drive the pipeline
set -euo pipefail
cd "$(dirname "$0")"
MUSICGEN=0; CAPTIONS=0; SKILL=0
for a in "$@"; do case $a in --musicgen) MUSICGEN=1;; --captions) CAPTIONS=1;; --skill) SKILL=1;; *) echo "unknown flag $a"; exit 1;; esac; done

node -e 'process.exit(+process.versions.node.split(".")[0] >= 22 ? 0 : 1)' || { echo "need node >= 22"; exit 1; }
command -v ffmpeg >/dev/null || { echo "need ffmpeg on PATH"; exit 1; }

echo "== node: hyperframes CLI";      npm install --no-fund --no-audit --silent
echo "== node: remotion effects";     (cd fx && npm install --no-fund --no-audit --silent)
echo "== vendor bundles";             bash tools/build-vendor.sh
echo "== python venv (.venv)"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
[ $MUSICGEN = 1 ] && .venv/bin/pip install -q -r requirements-musicgen.txt
[ $CAPTIONS = 1 ] && .venv/bin/pip install -q -r requirements-captions.txt
if [ $SKILL = 1 ]; then
  mkdir -p ~/.claude/skills && ln -sfn "$PWD/skill/kinetix" ~/.claude/skills/kinetix
  echo "== skill linked: ~/.claude/skills/kinetix"
fi
for ex in examples/*/ template/; do ./kinetix sync "$ex" >/dev/null; done
echo; ./kinetix doctor

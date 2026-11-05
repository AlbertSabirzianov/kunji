#!/usr/bin/env bash
# Record and render every demo clip into assets/.
#
#   bash scripts/demo/build.sh            # all scenes
#   bash scripts/demo/build.sh compare    # one scene
#
# Needs: kunji installed (pip install -e .), pyte, ffmpeg and node. The npm packages
# (playwright, xterm.js, gifsicle) are installed into $RENDER_DIR on the first run.
# The answers come from scripts/demo/mock_server.py: no real API, no key, no cost.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${WORK:-$(mktemp -d)}"
RENDER_DIR="${RENDER_DIR:-$WORK/render}"
OUT="$ROOT/assets"
SCENES=("${@:-demo compare commit budget}")
SCENES=(${SCENES[@]})
mkdir -p "$OUT" "$RENDER_DIR"

if [ ! -x "$RENDER_DIR/node_modules/gifsicle/vendor/gifsicle" ]; then
  (cd "$RENDER_DIR" && npm init -y >/dev/null && \
   npm i --silent playwright @xterm/xterm@5.5.0 @xterm/addon-canvas@0.7.0 gifsicle@7.0.1)
fi

python "$HERE/mock_server.py" 8765 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
sleep 0.5

for scene in "${SCENES[@]}"; do
  echo "== $scene"
  home="$WORK/home-$scene"; cwd="$WORK/cwd-$scene"
  rm -rf "$home" "$cwd"; mkdir -p "$cwd"
  python "$HERE/setup_home.py" "$home"
  HERE="$HERE" python - "$scene" "$home" "$cwd" <<'PY'
import sys; from pathlib import Path
import os; sys.path.insert(0, os.environ["HERE"])
from scenes import SCENES
setup = SCENES[sys.argv[1]].get("setup")
if setup: setup(Path(sys.argv[2]), Path(sys.argv[3]))
PY
  (cd "$cwd" && KUNJI_HOME="$home" PYTHONPATH="$HERE" PS1='$ ' \
     PYTHON_KEYRING_BACKEND=demo_keyring.Keyring \
     python "$HERE/record.py" "$scene" "$WORK/$scene.cast")

  # MP4 for social media: 30 fps, 2x scale.
  rm -rf "$WORK/mp4-$scene"
  (cd "$RENDER_DIR" && node "$HERE/render.mjs" "$WORK/$scene.cast" "$WORK/mp4-$scene" 30 2)
  ffmpeg -loglevel error -y -framerate 30 -i "$WORK/mp4-$scene/f%05d.png" \
    -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=0x0d0d0d,format=yuv420p" \
    -c:v libx264 -crf 20 -preset slow -movflags +faststart "$OUT/$scene.mp4"

  # GIF for README and website: 12 fps, 1x scale, shared palette.
  rm -rf "$WORK/gif-$scene"
  (cd "$RENDER_DIR" && node "$HERE/render.mjs" "$WORK/$scene.cast" "$WORK/gif-$scene" 12 1)
  ffmpeg -loglevel error -y -framerate 12 -i "$WORK/gif-$scene/f%05d.png" \
    -vf "split[a][b];[a]palettegen=max_colors=96:reserve_transparent=1:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" \
    "$WORK/$scene-raw.gif"
  # Lossless frame-diff optimisation: ~9 MB → ~300 KB.
  "$RENDER_DIR/node_modules/gifsicle/vendor/gifsicle" -O3 "$WORK/$scene-raw.gif" -o "$OUT/$scene.gif"
  cp "$WORK/$scene.cast" "$OUT/$scene.cast"
done
ls -la "$OUT"

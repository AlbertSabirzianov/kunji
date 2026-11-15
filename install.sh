#!/bin/sh
# kunji installer for macOS and Linux.
#
#   curl -fsSL https://kunji.iamsuraj.me/install.sh | sh
#
# What it does:
#   1. Installs uv (https://docs.astral.sh/uv/) if you don't have it. uv is a single file.
#   2. Runs `uv tool install kunji`. uv downloads Python 3.11+ by itself if you don't have it,
#      and keeps kunji in its own environment, so it never clashes with your other Python apps.
#   3. Adds the folder with the `kunji` command to your PATH.
#
# Options (environment variables):
#   KUNJI_VERSION=0.1.2       install that version instead of the newest
#   KUNJI_NO_MODIFY_PATH=1    don't change your shell profile
#
# Uninstall: uv tool uninstall kunji

set -eu

say() { printf '%s\n' "$*"; }
err() { printf 'kunji installer: %s\n' "$*" >&2; exit 1; }

download() {
  # download URL -> stdout
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$1"
  else
    err "curl or wget is needed. Install one of them and run this again."
  fi
}

find_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi
  for dir in "${XDG_BIN_HOME:-}" "$HOME/.local/bin" "${CARGO_HOME:-$HOME/.cargo}/bin"; do
    if [ -n "$dir" ] && [ -x "$dir/uv" ]; then
      say "$dir/uv"
      return 0
    fi
  done
  return 1
}

# Runs a command quietly with a one-line progress display: "[2/3] Installing kunji  / 12s".
# The command's own output goes to a log that is shown only if it fails.
step() {
  label=$1
  shift
  log=$(mktemp)
  "$@" >"$log" 2>&1 &
  pid=$!
  if [ -t 1 ]; then
    secs=0
    spin="|/-\\"
    while kill -0 "$pid" 2>/dev/null; do
      i=$((secs % 4 + 1))
      printf '\r%s  %s %ss ' "$label" "$(printf '%s' "$spin" | cut -c "$i")" "$secs"
      sleep 1
      secs=$((secs + 1))
    done
  fi
  if wait "$pid"; then
    status=0
  else
    status=$?
  fi
  if [ -t 1 ]; then
    printf '\r\033[K'
  fi
  if [ "$status" -eq 0 ]; then
    say "$label  done"
  else
    say "$label  failed:"
    cat "$log" >&2
  fi
  rm -f "$log"
  return "$status"
}

say "Installing kunji"
say ""

UV=$(find_uv || true)
if [ -z "$UV" ]; then
  # Download to a file first: with `download | sh` a failed download would go unnoticed.
  UV_INSTALLER=$(mktemp)
  trap 'rm -f "$UV_INSTALLER"' EXIT
  download https://astral.sh/uv/install.sh >"$UV_INSTALLER" \
    || err "couldn't download uv from astral.sh. Check your internet connection and run this again."
  if [ "${KUNJI_NO_MODIFY_PATH:-}" = "1" ]; then
    export UV_NO_MODIFY_PATH=1
  fi
  step "[1/3] Getting uv (manages Python for kunji)" sh "$UV_INSTALLER" --quiet \
    || err "uv's installer failed (see above)."
  UV=$(find_uv || true)
  [ -n "$UV" ] || err "uv was installed but can't be found. Open a new terminal and run this again."
else
  say "[1/3] Getting uv (manages Python for kunji)  already installed"
fi

PACKAGE="kunji"
if [ -n "${KUNJI_VERSION:-}" ]; then
  PACKAGE="kunji==${KUNJI_VERSION}"
fi

# --upgrade: running the installer again updates kunji. --python: uv downloads one if needed.
step "[2/3] Installing kunji (the first time takes a minute)" \
  "$UV" tool install --upgrade --python ">=3.11" "$PACKAGE" \
  || err "uv couldn't install kunji (the reason is above). Fix that and run this again."

BIN_DIR=$("$UV" tool dir --bin 2>/dev/null) || BIN_DIR="$HOME/.local/bin"

if [ "${KUNJI_NO_MODIFY_PATH:-}" != "1" ]; then
  "$UV" tool update-shell >/dev/null 2>&1 || true
  say "[3/3] Adding kunji to your PATH  done"
else
  say "[3/3] Adding kunji to your PATH  skipped (KUNJI_NO_MODIFY_PATH=1)"
fi

"$BIN_DIR/kunji" --version >/dev/null 2>&1 \
  || err "kunji was installed but doesn't start. Try: $BIN_DIR/kunji --version"

say ""
say "$("$BIN_DIR/kunji" --version) is installed."
case ":$PATH:" in
  *":$BIN_DIR:"*)
    say "Run: kunji"
    ;;
  *)
    say "Open a new terminal, then run: kunji"
    say "(or use it in this terminal now: export PATH=\"$BIN_DIR:\$PATH\")"
    ;;
esac
say "Update later with: kunji upgrade"

#!/usr/bin/env bash
set -euo pipefail

# macOS Bubble: one-click build script
#
# Usage:
#   tools/build_macos.sh                # clean build, package, zip, checksum
#   tools/build_macos.sh --no-clean     # keep existing build/dist
#   tools/build_macos.sh --install-deps # pip install -r requirements.txt first
#   tools/build_macos.sh --smoke        # run a brief launch smoke-test (then kill)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer the active virtualenv's Python, fallback to python3 on PATH
if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PY="$VIRTUAL_ENV/bin/python"
else
  PY="$(command -v python3 || true)"
fi
if [[ -z "$PY" ]]; then
  echo "[!] Could not find a Python interpreter. Activate a venv or install Python 3." >&2
  exit 1
fi
echo "[*] Using Python: $PY"
APP_NAME="Bubble"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
APP_PATH="$DIST_DIR/${APP_NAME}.app"
# Read version from pyproject.toml (fallback to 0.0.0)
VERSION=$("$PY" - << 'PY'
import sys, tomllib
try:
    with open('pyproject.toml','rb') as f:
        print(tomllib.load(f)['project']['version'])
except Exception:
    print('0.0.0')
PY
)
ZIP_PATH="$DIST_DIR/${APP_NAME}-v${VERSION}.zip"

CLEAN=1
INSTALL_DEPS=0
SMOKE=0
for arg in "$@"; do
  case "$arg" in
    --no-clean) CLEAN=0 ;;
    --install-deps) INSTALL_DEPS=1 ;;
    --smoke) SMOKE=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$INSTALL_DEPS" == "1" ]]; then
  echo "[*] Installing Python build dependencies..."
  "$PY" -m pip install --upgrade pip wheel setuptools packaging >/dev/null
  "$PY" -m pip install -r requirements.txt
fi

if [[ "$CLEAN" == "1" ]]; then
  echo "[*] Cleaning previous build..."
  rm -rf "$BUILD_DIR" "$DIST_DIR"
fi

echo "[*] Building .app via py2app..."
"$PY" setup.py py2app -O2

if [[ ! -d "$APP_PATH" ]]; then
  echo "[!] Build failed (no $APP_PATH)" >&2
  exit 1
fi

echo "[*] Creating zip artifact..."
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
shasum -a 256 "$ZIP_PATH" | awk '{print $1}' > "$ZIP_PATH.sha256"

echo "[*] Built: $APP_PATH"
echo "[*] Zip:   $ZIP_PATH"
echo -n "[*] SHA256: " && cat "$ZIP_PATH.sha256"

if [[ "$SMOKE" == "1" ]]; then
  echo "[*] Running smoke test (launch & kill after 4s)..."
  ("$APP_PATH"/Contents/MacOS/$APP_NAME >/tmp/bubble-smoke.log 2>&1 & echo $! > /tmp/bubble-smoke.pid)
  sleep 4
  if pkill -f "$APP_PATH/Contents/MacOS/$APP_NAME"; then
    echo "[*] Smoke test done. Logs: /tmp/bubble-smoke.log"
  else
    echo "[!] Smoke test could not kill process (it may have quit). Check /tmp/bubble-smoke.log"
  fi
fi

echo "[*] Done."

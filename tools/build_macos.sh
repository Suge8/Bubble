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
APP_NAME="Bubble"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
APP_PATH="$DIST_DIR/${APP_NAME}.app"
ZIP_PATH="$DIST_DIR/${APP_NAME}-v0.1.0.zip"

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
  python3 -m pip install --upgrade pip wheel setuptools packaging >/dev/null
  python3 -m pip install -r requirements.txt
fi

if [[ "$CLEAN" == "1" ]]; then
  echo "[*] Cleaning previous build..."
  rm -rf "$BUILD_DIR" "$DIST_DIR"
fi

echo "[*] Building .app via py2app..."
python3 setup.py py2app -O2

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


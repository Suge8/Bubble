# setup.py
from setuptools import setup, find_packages
import sys, os, glob
import ctypes.util

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.join(_ROOT, "Bubble.py")

def _write_launcher(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            """
import os, sys
try:
    # Add ./src to sys.path (development-like layout)
    here = os.path.dirname(__file__)
    src_path = os.path.join(here, "src")
    if os.path.isdir(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
    from bubble.main import main
except Exception:
    from bubble.main import main  # type: ignore

if __name__ == "__main__":
    main()
""".strip()
        )

# Force fallback launcher in CI to avoid path assumptions
_force_fallback = os.environ.get("BUBBLE_FORCE_FALLBACK_LAUNCHER") == "1" or \
                   os.environ.get("GITHUB_ACTIONS") == "true" or \
                   os.environ.get("CI") is not None

if _force_fallback or not os.path.exists(_SCRIPT):
    _SCRIPT = os.path.join(_ROOT, "build", "Bubble.py")
    _write_launcher(_SCRIPT)

APP = [_SCRIPT]
DATA_FILES = []
def _detect_libffi():
    # Try ctypes to find the library name
    name = ctypes.util.find_library('ffi')
    candidates = []
    # Common locations: current interpreter prefix and conda base
    for base in filter(None, [sys.prefix, os.environ.get('CONDA_PREFIX'), '/opt/homebrew/Caskroom/miniconda/base', '/usr/local', '/opt/homebrew']):
        for pat in (
            os.path.join(base, 'lib', 'libffi*.dylib'),
            os.path.join(base, 'Cellar', 'libffi', '*', 'lib', 'libffi*.dylib'),
        ):
            candidates.extend(glob.glob(pat))
    # Prefer versioned .8 first
    candidates.sort(key=lambda p: ('.8.' not in p and not p.endswith('libffi.8.dylib'), len(p)))
    for p in candidates:
        if os.path.isfile(p):
            return p
    # Last resort: if ctypes found a basename, hope dyld finds it at runtime
    return None

_extra_frameworks = []
_ffi = _detect_libffi()
if _ffi:
    _extra_frameworks.append(_ffi)

_ICON = os.path.join(_ROOT, "src", "bubble", "logo", "icon.icns")

OPTIONS = {
    # Bundle your package directory so imports “just work”
    "packages": ["bubble"],
    # Explicitly copy image assets to app Resources for NSBundle lookups
    "resources": [
        "src/bubble/logo",
        "src/bubble/assets/icons",
    ],
    "includes": [],
    # Exclude build-time tooling that can cause duplicate dist-info when collected
    "excludes": [
        "pip",
        "setuptools",
        "wheel",
        "pkg_resources",
    ],
    # Build arch and GUI mode
    "arch": "universal2",
    # GUI app (no console window)
    "argv_emulation": False,
    # Optional: your .icns icon (only if present)
    **({"iconfile": _ICON} if os.path.exists(_ICON) else {}),
    # Allow microphone & Accessibility prompts by embedding Info.plist keys:
    "plist": {
        "CFBundleName": "Bubble",
        "CFBundleDisplayName": "Bubble",
        "NSMicrophoneUsageDescription": "Bubble needs your mic for voice input.",
        "NSAppleEventsUsageDescription": "Bubble needs accessibility permission for hotkeys."
    },
    # Bundle missing dylibs that Python depends on (e.g., libffi for _ctypes)
    "frameworks": _extra_frameworks,
}

setup(
    name="bubble",
    version="0.3.4",
    # Explicit package list (robust on CI; ignores any sibling packages)
    packages=[
        "bubble",
        "bubble.components",
        "bubble.components.utils",
        "bubble.i18n",
        "bubble.models",
        "bubble.utils",
    ],
    package_dir={"bubble": "src/bubble"},
    # Ensure non-Python assets (icons) are bundled
    package_data={
        "bubble": [
            "logo/*",
            "logo/icon.iconset/*",
            "assets/icons/*",
            "i18n/*.json",
            "about/*.txt",
        ]
    },
    include_package_data=True,
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

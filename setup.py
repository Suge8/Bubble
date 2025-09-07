# setup.py
from setuptools import setup, find_packages
import sys, os, glob
import ctypes.util

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.join(_ROOT, "Bubble.py")

# Ensure an app entry script exists for py2app even if repository layout differs
if not os.path.exists(_SCRIPT):
    os.makedirs(os.path.join(_ROOT, "build"), exist_ok=True)
    _SCRIPT = os.path.join(_ROOT, "build", "py2app_launcher.py")
    with open(_SCRIPT, "w", encoding="utf-8") as f:
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
except Exception as e:
    # Fallback: try regular import if installed layout
    from bubble.main import main  # type: ignore

if __name__ == "__main__":
    main()
""".strip()
        )

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
    version="0.3.3",
    # Only include our app packages (exclude historical 'bubblebot')
    packages=find_packages(where="src", include=["bubble", "bubble.*"]),
    package_dir={"": "src"},
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

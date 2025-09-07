# setup.py
from setuptools import setup, find_packages
import sys, os, glob
import ctypes.util

APP = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "Bubble.py")]
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

_ROOT = os.path.dirname(os.path.abspath(__file__))
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
    version="0.3.2",
    packages=find_packages(where="src", include=["bubble*"]),
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

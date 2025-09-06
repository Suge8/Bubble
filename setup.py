# setup.py
from setuptools import setup, find_packages

APP = ["BubbleBot.py"]
DATA_FILES = []
OPTIONS = {
    # Bundle your package directory so imports “just work”
    "packages": ["bubblebot"],
    # Explicitly copy image assets to app Resources for NSBundle lookups
    "resources": [
        "src/bubblebot/logo",
    ],
    "includes": [],
    # GUI app (no console window)
    "argv_emulation": False,
    # Optional: your .icns icon
    "iconfile": "src/bubblebot/logo/icon.icns",
    # Allow microphone & Accessibility prompts by embedding Info.plist keys:
    "plist": {
        "CFBundleName": "Bubble",
        "CFBundleDisplayName": "Bubble",
        "NSMicrophoneUsageDescription": "Bubble needs your mic for voice input.",
        "NSAppleEventsUsageDescription": "Bubble needs accessibility permission for hotkeys."
    },
}

setup(
    name="bubblebot",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Ensure non-Python assets (icons) are bundled
    package_data={
        "bubblebot": [
            "logo/*",
            "logo/icon.iconset/*",
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

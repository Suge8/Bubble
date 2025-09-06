import os
import platform
import types

import pytest


def test_detect_system_language_from_ns_locale(monkeypatch):
    from bubblebot.components.config_manager import ConfigManager

    class _FakeNSLocale:
        @staticmethod
        def preferredLanguages():
            return ["ja-JP"]

    # Inject fake NSLocale so test is cross-platform
    monkeypatch.setattr("bubblebot.components.config_manager.NSLocale", _FakeNSLocale, raising=False)
    assert ConfigManager.detect_system_language() == "ja"


def test_detect_system_language_from_env(monkeypatch):
    from bubblebot.components.config_manager import ConfigManager

    # Make sure NSLocale path is ignored
    monkeypatch.setattr("bubblebot.components.config_manager.NSLocale", None, raising=False)
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")
    assert ConfigManager.detect_system_language() == "zh"


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="Login items only supported on macOS")
def test_login_items_enable_disable_monkeypatched(tmp_path, monkeypatch):
    from bubblebot.utils import login_items

    # Redirect LaunchAgents dir into a temp directory to avoid touching user files
    monkeypatch.setattr(login_items, "_launch_agents_dir", lambda: tmp_path)
    # Make _is_darwin return True in case of edge environments
    monkeypatch.setattr(login_items, "_is_darwin", lambda: True)

    # Stub program args to a harmless command
    monkeypatch.setattr(login_items, "_program_args", lambda: ["/usr/bin/true"])

    # Stub launchctl to always succeed
    def _fake_launchctl(*args):
        # Treat any print/load/unload/bootstrap/enable/disable as success
        return 0, "", ""

    monkeypatch.setattr(login_items, "_launchctl", _fake_launchctl)

    ok, msg = login_items.set_enabled(True)
    assert ok, msg
    # Plist should exist after enabling
    assert list(tmp_path.glob("*.plist")), "plist not created"

    ok, msg = login_items.set_enabled(False)
    assert ok, msg
    # Plist should be removed after disabling
    assert not list(tmp_path.glob("*.plist")), "plist not removed"


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="AppKit required on macOS")
def test_format_launcher_hotkey_default(monkeypatch):
    # Verify the human-readable formatting for the status bar hint
    from bubblebot.constants import LAUNCHER_TRIGGER
    from bubblebot import app as app_mod

    # Make a light-weight instance; .init() only sets attributes
    delegate = app_mod.AppDelegate.alloc().init()
    # Ensure default trigger (⌘ + g / keycode 5)
    LAUNCHER_TRIGGER["flags"] = getattr(app_mod, "kCGEventFlagMaskCommand", None) or LAUNCHER_TRIGGER["flags"]
    LAUNCHER_TRIGGER["key"] = 5
    hotkey = delegate._format_launcher_hotkey()
    assert hotkey.lower() in ("⌘+g", "⌘+5", "⌘+g")

import os
import platform

import pytest


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="AppKit required on macOS")
def test_status_hint_updates_on_hotkey_change(monkeypatch):
    """The status menu hint should reflect the current hotkey and update after change."""
    from bubblebot.constants import LAUNCHER_TRIGGER
    from bubblebot import app as app_mod

    # Create a lightweight delegate instance
    delegate = app_mod.AppDelegate.alloc().init()

    class _FakeItem:
        def __init__(self):
            self._title = None
        def setTitle_(self, t):
            self._title = t
        def title(self):
            return self._title or ""

    # Attach fake menu items and skip heavy init in refresher
    delegate.menu_hint_item = _FakeItem()
    delegate.menu_settings_item = _FakeItem()
    delegate.menu_quit_item = _FakeItem()
    # Prevent _refresh_status_menu_titles from creating event taps or touching window
    setattr(delegate, '_status_menu_initialized', True)

    # Default trigger: ensure a baseline
    LAUNCHER_TRIGGER["flags"] = LAUNCHER_TRIGGER.get("flags")
    LAUNCHER_TRIGGER["key"] = 5  # 'g'
    delegate._refresh_status_menu_titles()
    t1 = delegate.menu_hint_item.title()
    # Should contain a formatted hotkey like "⌘+g"
    assert t1 and "⌘+" in t1, t1

    # Change hotkey (Space)
    LAUNCHER_TRIGGER["key"] = 49
    delegate._refresh_status_menu_titles()
    t2 = delegate.menu_hint_item.title()
    assert t2 and t2 != t1 and ("Space" in t2 or "空格" in t2 or "\u7a7a\u683c" in t2)

    # Other items localized
    assert delegate.menu_settings_item.title()
    assert delegate.menu_quit_item.title()


def test_status_menu_no_legacy_items_in_codebase():
    """Ensure old menu entries are not present anymore (structural sanity)."""
    here = os.path.dirname(os.path.dirname(__file__))
    app_path = os.path.join(here, "src", "bubblebot", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Legacy entries that should not exist anymore
    assert "Set New Trigger" not in content
    assert "Clear Web Cache" not in content
    # Hint text may include "Show/Hide" as part of i18n; we don't assert its absence here.


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="AppKit required on macOS")
def test_status_icon_updates_on_appearance(monkeypatch):
    """Status bar icon should switch between black/white based on dark mode with fallbacks."""
    from bubblebot.app import AppDelegate

    # Create a lightweight AppDelegate instance (no app launch)
    delegate = AppDelegate.alloc().init()

    # Prepare fake status item/button to capture images
    class _FakeButton:
        def __init__(self):
            self.image = None
        def setWantsLayer_(self, v):
            return None
        def setImage_(self, img):
            self.image = img

    class _FakeStatusItem:
        def __init__(self):
            self._btn = _FakeButton()
        def button(self):
            return self._btn

    delegate.status_item = _FakeStatusItem()
    # Use simple sentinels to verify selection
    BLACK = object()
    WHITE = object()
    delegate.logo_black = BLACK
    delegate.logo_white = WHITE

    # Dark mode -> white icon
    monkeypatch.setattr(delegate, '_is_dark_appearance', lambda: True)
    delegate.updateStatusItemImage()
    assert delegate.status_item.button().image is WHITE

    # Light mode -> black icon
    monkeypatch.setattr(delegate, '_is_dark_appearance', lambda: False)
    delegate.updateStatusItemImage()
    assert delegate.status_item.button().image is BLACK

    # Missing preferred icon falls back to available one
    delegate.logo_black = None
    monkeypatch.setattr(delegate, '_is_dark_appearance', lambda: False)
    delegate.updateStatusItemImage()
    assert delegate.status_item.button().image is WHITE

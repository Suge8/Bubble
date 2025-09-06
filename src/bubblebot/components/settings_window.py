"""
Settings window for Bubble.

Provides:
- Language selector (zh/en/ja/ko/fr)
- Launch at Login checkbox (persist only for now)
- Hotkey display + Change…
- Clear Web Cache
- Save / Cancel
"""

from __future__ import annotations

import objc
from typing import Optional
from AppKit import (
    NSApp,
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSBackingStoreBuffered,
    NSView,
    NSMakeRect,
    NSTextField,
    NSButton,
    NSSwitchButton,
    NSPopUpButton,
    NSFont,
)

from Foundation import NSObject

from ..i18n import t as _t, get_language as _get_lang
from .config_manager import ConfigManager
from ..listener import set_custom_launcher_trigger


class SettingsWindow(NSObject):
    def initWithAppDelegate_(self, app_delegate):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        self.app_delegate = app_delegate
        self.window: Optional[NSWindow] = None
        # Controls
        self.lang_label = None
        self.lang_popup = None
        self.launch_checkbox = None
        self.hotkey_label = None
        self.hotkey_value = None
        self.hotkey_button = None
        self.clear_cache_button = None
        self.save_button = None
        self.cancel_button = None
        return self

    def _create_window(self):
        rect = NSMakeRect(0, 0, 420, 260)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_(_t('settings.title'))
        self.window.setReleasedWhenClosed_(False)
        self._build_ui()

    def _build_ui(self):
        content = self.window.contentView()
        bounds = content.bounds()

        def add_label(text, x, y, w, h, bold=False):
            lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            lbl.setStringValue_(text)
            if bold:
                lbl.setFont_(NSFont.boldSystemFontOfSize_(13))
            else:
                lbl.setFont_(NSFont.systemFontOfSize_(13))
            content.addSubview_(lbl)
            return lbl

        def add_button(title, x, y, w, h):
            btn = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            btn.setTitle_(title)
            content.addSubview_(btn)
            return btn

        # Title
        add_label(_t('settings.title'), 20, bounds.size.height - 40, 200, 20, bold=True)

        # Language selector
        self.lang_label = add_label(_t('settings.language'), 20, bounds.size.height - 80, 120, 20)
        self.lang_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(150, bounds.size.height - 84, 180, 26), False)
        self.lang_popup.addItemWithTitle_("English")
        self.lang_popup.addItemWithTitle_("中文")
        self.lang_popup.addItemWithTitle_("日本語")
        self.lang_popup.addItemWithTitle_("한국어")
        self.lang_popup.addItemWithTitle_("Français")
        content.addSubview_(self.lang_popup)

        # Launch at login
        self.launch_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, bounds.size.height - 120, 260, 20))
        self.launch_checkbox.setButtonType_(NSSwitchButton)
        self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
        content.addSubview_(self.launch_checkbox)

        # Hotkey
        self.hotkey_label = add_label(_t('settings.hotkey'), 20, bounds.size.height - 160, 80, 20)
        self.hotkey_value = add_label("", 110, bounds.size.height - 160, 160, 20)
        self.hotkey_button = add_button(_t('button.change'), 280, bounds.size.height - 164, 120, 28)
        self.hotkey_button.setTarget_(self)
        self.hotkey_button.setAction_("changeHotkey:")

        # Clear cache
        self.clear_cache_button = add_button(_t('settings.clearCache'), 20, bounds.size.height - 200, 180, 28)
        self.clear_cache_button.setTarget_(self)
        self.clear_cache_button.setAction_("clearCache:")

        # Save / Cancel
        self.save_button = add_button(_t('button.save') if hasattr(self, 'window') else "Save", bounds.size.width - 190, 20, 80, 30)
        self.save_button.setTarget_(self)
        self.save_button.setAction_("saveSettings:")
        self.cancel_button = add_button(_t('button.cancel'), bounds.size.width - 100, 20, 80, 30)
        self.cancel_button.setTarget_(self)
        self.cancel_button.setAction_("cancelSettings:")

        self._load_values_into_ui()

    def _load_values_into_ui(self):
        # Language
        lang = ConfigManager.get_language() or _get_lang()
        order = ["en", "zh", "ja", "ko", "fr"]
        try:
            idx = order.index(lang)
        except ValueError:
            idx = 0
        self.lang_popup.selectItemAtIndex_(idx)
        # Launch at login (persisted only)
        cfg = ConfigManager.load()
        launch = bool(cfg.get("launch_at_login", False))
        try:
            self.launch_checkbox.setState_(1 if launch else 0)
        except Exception:
            pass
        # Hotkey (hint only)
        try:
            from ..app import AppDelegate  # avoid cycle at import time
            fmt = getattr(self.app_delegate, '_format_launcher_hotkey', None)
            if callable(fmt):
                self.hotkey_value.setStringValue_(fmt())
        except Exception:
            pass

    def _apply_localization(self):
        if not self.window:
            return
        self.window.setTitle_(_t('settings.title'))
        if self.lang_label:
            self.lang_label.setStringValue_(_t('settings.language'))
        if self.launch_checkbox:
            self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
        if self.hotkey_label:
            self.hotkey_label.setStringValue_(_t('settings.hotkey'))
        if self.clear_cache_button:
            self.clear_cache_button.setTitle_(_t('settings.clearCache'))
        if self.save_button:
            self.save_button.setTitle_(_t('button.save'))
        if self.cancel_button:
            self.cancel_button.setTitle_(_t('button.cancel'))

    # Public API
    def show(self):
        if self.window is None:
            self._create_window()
        self._apply_localization()
        self._load_values_into_ui()
        self.window.center()
        self.window.makeKeyAndOrderFront_(None)
        try:
            NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass

    # Actions
    def saveSettings_(self, sender):
        # Language
        idx = int(self.lang_popup.indexOfSelectedItem()) if self.lang_popup else 0
        order = ["en", "zh", "ja", "ko", "fr"]
        new_lang = order[idx] if idx < len(order) else "en"
        try:
            # Persist and apply
            ConfigManager.set_language(new_lang)
            if hasattr(self.app_delegate, 'changeLanguage_'):
                self.app_delegate.changeLanguage_(new_lang)
        except Exception:
            pass
        # Launch at login (persist only)
        try:
            cfg = ConfigManager.load()
            try:
                state = bool(self.launch_checkbox.state())
            except Exception:
                state = False
            cfg["launch_at_login"] = state
            ConfigManager.save(cfg)
        except Exception:
            pass
        # Close
        if self.window:
            self.window.orderOut_(None)

    def cancelSettings_(self, sender):
        if self.window:
            self.window.orderOut_(None)

    def clearCache_(self, sender):
        try:
            if hasattr(self.app_delegate, 'clearWebViewData_'):
                self.app_delegate.clearWebViewData_(None)
        except Exception:
            pass

    def changeHotkey_(self, sender):
        try:
            set_custom_launcher_trigger(self.app_delegate)
        except Exception:
            pass
        # Update hint value soon after
        try:
            from Foundation import NSTimer
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                2.1, self, 'refreshHotkey:', None, False
            )
        except Exception:
            # fallback immediate refresh
            self.refreshHotkey_(None)

    def refreshHotkey_(self, _):
        try:
            if hasattr(self.app_delegate, '_refresh_status_menu_titles'):
                self.app_delegate._refresh_status_menu_titles()
        except Exception:
            pass
        try:
            fmt = getattr(self.app_delegate, '_format_launcher_hotkey', None)
            if callable(fmt):
                self.hotkey_value.setStringValue_(fmt())
        except Exception:
            pass

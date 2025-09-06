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
import os
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
    NSColor,
    NSImage,
    NSImageView,
    NSBezelStyleRounded,
    NSAnimationContext,
    NSVisualEffectView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectStateActive,
    NSVisualEffectMaterialHUDWindow,
    NSTrackingArea,
    NSTrackingMouseEnteredAndExited,
    NSTrackingActiveAlways,
    NSTrackingInVisibleRect,
)

from Foundation import NSObject

from ..i18n import t as _t, get_language as _get_lang
from .config_manager import ConfigManager
from ..listener import set_custom_launcher_trigger


class HoverButton(NSButton):
    def initWithFrame_(self, frame):
        self = objc.super(HoverButton, self).initWithFrame_(frame)
        if self is None:
            return None
        try:
            self.setWantsLayer_(True)
            self.layer().setCornerRadius_(8.0)
            self.layer().setMasksToBounds_(True)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08).CGColor())
        except Exception:
            pass
        self._tracking_area = None
        return self

    def updateTrackingAreas(self):
        try:
            if self._tracking_area is not None:
                self.removeTrackingArea_(self._tracking_area)
            opts = NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect
            self._tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                self.bounds(), opts, self, None
            )
            self.addTrackingArea_(self._tracking_area)
        except Exception:
            pass
        objc.super(HoverButton, self).updateTrackingAreas()

    def mouseEntered_(self, event):
        try:
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.12).CGColor())
        except Exception:
            pass

    def mouseExited_(self, event):
        try:
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08).CGColor())
        except Exception:
            pass

    def mouseDown_(self, event):
        try:
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.16).CGColor())
        except Exception:
            pass
        objc.super(HoverButton, self).mouseDown_(event)

    def mouseUp_(self, event):
        try:
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.12).CGColor())
        except Exception:
            pass
        objc.super(HoverButton, self).mouseUp_(event)

class SettingsWindow(NSObject):
    def initWithAppDelegate_(self, app_delegate):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        self.app_delegate = app_delegate
        self.window: Optional[NSWindow] = None
        # Controls / layout references
        self.lang_label = None
        self.lang_popup = None
        self.launch_checkbox = None
        self.hotkey_label = None
        self.hotkey_value = None
        self.hotkey_button = None
        self.clear_cache_button = None
        self.save_button = None
        self.cancel_button = None
        self.header_logo_view = None
        self.header_title_label = None
        self.bg_blur = None
        return self

    def _create_window(self):
        rect = NSMakeRect(0, 0, 460, 300)
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
        try:
            # Polished look: translucent titlebar and better blending
            self.window.setTitleVisibility_(1)  # NSWindowTitleHidden
            self.window.setTitlebarAppearsTransparent_(True)
        except Exception:
            pass
        self._build_ui()

    def _build_ui(self):
        content = self.window.contentView()
        bounds = content.bounds()

        # Background blur (unified with app aesthetic)
        try:
            if os.environ.get('BB_NO_EFFECTS') == '1':
                raise Exception('effects disabled by env')
            self.bg_blur = NSVisualEffectView.alloc().initWithFrame_(bounds)
            self.bg_blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            try:
                material = self._preferred_material()
                self.bg_blur.setMaterial_(material)
            except Exception:
                pass
            self.bg_blur.setState_(NSVisualEffectStateActive)
            # autoresize with window
            self.bg_blur.setAutoresizingMask_((1 << 1) | (1 << 4))  # width + height sizable
            # Add first to be behind
            content.addSubview_(self.bg_blur)
        except Exception:
            self.bg_blur = None

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
            try:
                lbl.setTextColor_(NSColor.labelColor())
            except Exception:
                pass
            content.addSubview_(lbl)
            return lbl

        def style_button(btn):
            try:
                btn.setBezelStyle_(NSBezelStyleRounded)
            except Exception:
                pass
            try:
                btn.setWantsLayer_(True)
                btn.layer().setCornerRadius_(8.0)
                btn.layer().setMasksToBounds_(True)
                # Subtle card-like background
                btn.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08).CGColor())
            except Exception:
                pass
            return btn

        def add_button(title, x, y, w, h):
            btn = HoverButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            btn.setTitle_(title)
            style_button(btn)
            content.addSubview_(btn)
            return btn

        def add_image_view(img, x, y, w, h):
            iv = NSImageView.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            try:
                iv.setImageScaling_(1)  # NSImageScaleProportionallyUpOrDown
            except Exception:
                pass
            iv.setImage_(img)
            content.addSubview_(iv)
            return iv

        # Header with logo + title
        logo_img = self._load_logo_for_appearance()
        if logo_img is not None:
            self.header_logo_view = add_image_view(logo_img, 20, bounds.size.height - 46, 20, 20)
        self.header_title_label = add_label(_t('settings.title'), 46, bounds.size.height - 44, 260, 22, bold=True)
        # Hairline separator
        try:
            sep = NSView.alloc().initWithFrame_(NSMakeRect(20, bounds.size.height - 52, bounds.size.width - 40, 1))
            sep.setWantsLayer_(True)
            sep.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
            content.addSubview_(sep)
        except Exception:
            pass

        # Language selector
        self.lang_label = add_label(_t('settings.language'), 20, bounds.size.height - 92, 120, 20)
        self.lang_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(150, bounds.size.height - 96, 200, 28), False)
        self.lang_popup.addItemWithTitle_("English")
        self.lang_popup.addItemWithTitle_("中文")
        self.lang_popup.addItemWithTitle_("日本語")
        self.lang_popup.addItemWithTitle_("한국어")
        self.lang_popup.addItemWithTitle_("Français")
        try:
            self.lang_popup.setWantsLayer_(True)
            self.lang_popup.layer().setCornerRadius_(8.0)
            self.lang_popup.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.06).CGColor())
        except Exception:
            pass
        content.addSubview_(self.lang_popup)

        # Launch at login
        self.launch_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, bounds.size.height - 132, 260, 20))
        self.launch_checkbox.setButtonType_(NSSwitchButton)
        self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
        content.addSubview_(self.launch_checkbox)

        # Hotkey
        self.hotkey_label = add_label(_t('settings.hotkey'), 20, bounds.size.height - 172, 80, 20)
        self.hotkey_value = add_label("", 110, bounds.size.height - 172, 180, 20)
        self.hotkey_button = add_button(_t('button.change'), 300, bounds.size.height - 176, 120, 30)
        self.hotkey_button.setTarget_(self)
        self.hotkey_button.setAction_("changeHotkey:")

        # Clear cache
        self.clear_cache_button = add_button(_t('settings.clearCache'), 20, bounds.size.height - 212, 200, 30)
        self.clear_cache_button.setTarget_(self)
        self.clear_cache_button.setAction_("clearCache:")

        # Save / Cancel
        self.save_button = add_button(_t('button.save') if hasattr(self, 'window') else "Save", bounds.size.width - 200, 20, 90, 32)
        self.save_button.setTarget_(self)
        self.save_button.setAction_("saveSettings:")
        try:
            # Accent background for primary
            self.save_button.layer().setBackgroundColor_(NSColor.controlAccentColor().colorWithAlphaComponent_(0.22).CGColor())
        except Exception:
            pass
        self.cancel_button = add_button(_t('button.cancel'), bounds.size.width - 100, 20, 80, 32)
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
        if self.header_title_label:
            self.header_title_label.setStringValue_(_t('settings.title'))
        # Update header logo for current appearance
        try:
            if self.header_logo_view is not None:
                self.header_logo_view.setImage_(self._load_logo_for_appearance())
        except Exception:
            pass

    # Public API
    def show(self):
        if self.window is None:
            self._create_window()
        self._apply_localization()
        self._load_values_into_ui()
        self.window.center()
        # Polished animated presentation (fade only; safer across macOS versions)
        try:
            if os.environ.get('BB_NO_EFFECTS') == '1':
                raise Exception('effects disabled by env')
            self.window.setAlphaValue_(0.0)
            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            NSAnimationContext.beginGrouping()
            NSAnimationContext.currentContext().setDuration_(0.18)
            self.window.animator().setAlphaValue_(1.0)
            NSAnimationContext.endGrouping()
        except Exception:
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
        self._dismiss(animated=True)

    def cancelSettings_(self, sender):
        self._dismiss(animated=True)

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

    # Helpers
    def _dismiss(self, animated=True):
        if not self.window:
            return
        if not animated or os.environ.get('BB_NO_EFFECTS') == '1':
            self.window.orderOut_(None)
            return
        try:
            NSAnimationContext.beginGrouping()
            NSAnimationContext.currentContext().setDuration_(0.16)
            self.window.animator().setAlphaValue_(0.0)
            NSAnimationContext.endGrouping()
            # Slight delay to ensure fade completes
            from Foundation import NSTimer
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.18, self, 'performOrderOut:', None, False
            )
        except Exception:
            self.window.orderOut_(None)

    def performOrderOut_(self, _):
        try:
            self.window.orderOut_(None)
            self.window.setAlphaValue_(1.0)
        except Exception:
            pass

    def _load_logo_for_appearance(self):
        """Load a small logo matching current appearance (light/dark)."""
        try:
            # Determine dark vs light
            dark = False
            try:
                app = NSApp
                appearance = app.effectiveAppearance()
                name = appearance.bestMatchFromAppearancesWithNames_([
                    "NSAppearanceNameDarkAqua",
                    "NSAppearanceNameAqua",
                ])
                dark = name == "NSAppearanceNameDarkAqua"
            except Exception:
                pass
            rel_path = 'logo/logo_white.png' if dark else 'logo/logo_black.png'
            # Try to load from package data first (works in bundle)
            try:
                import pkgutil
                data = pkgutil.get_data('bubblebot', rel_path)
                if data:
                    from Foundation import NSData
                    nsdata = NSData.dataWithBytes_length_(data, len(data))
                    img = NSImage.alloc().initWithData_(nsdata)
                    if img is not None:
                        try: img.setTemplate_(False)
                        except Exception: pass
                        try: img.setSize_((20, 20))
                        except Exception: pass
                        return img
            except Exception:
                pass
            # Fallback to filesystem path next to module
            try:
                import os
                here = os.path.dirname(os.path.abspath(__file__))
                p = os.path.join(here, '..', rel_path)
                p = os.path.normpath(p)
                img = NSImage.alloc().initWithContentsOfFile_(p)
                if img is not None:
                    return img
            except Exception:
                pass
        except Exception:
            pass
        return None

    def _preferred_material(self):
        # Try a few materials in order of preference; return the first that exists
        candidates = [
            'NSVisualEffectMaterialHUDWindow',
            'NSVisualEffectMaterialPopover',
            'NSVisualEffectMaterialSidebar',
            'NSVisualEffectMaterialWindowBackground',
            'NSVisualEffectMaterialAppearanceBased',
        ]
        for name in candidates:
            try:
                return getattr(__import__('AppKit', fromlist=[name]), name)
            except Exception:
                continue
        # Fallback to an int (AppearanceBased is 0 on some SDKs)
        return 0

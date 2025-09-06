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
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSView,
    NSMakeRect,
    NSTextField,
    NSTextAlignmentCenter,
    NSButton,
    NSSwitchButton,
    NSPopUpButton,
    NSFont,
    NSColor,
    NSImage,
    NSImageView,
    NSBezelStyleRounded,
    NSCursor,
    NSAnimationContext,
    NSVisualEffectView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectStateActive,
    NSVisualEffectMaterialHUDWindow,
    NSTrackingArea,
    NSTrackingMouseEnteredAndExited,
    NSTrackingActiveAlways,
    NSTrackingInVisibleRect,
    NSBezierPath,
    NSRectFill,
    NSFocusRingTypeNone,
)

from Foundation import NSObject, NSAttributedString

from ..i18n import t as _t, get_language as _get_lang
from ..utils import login_items
from .config_manager import ConfigManager
from ..listener import set_custom_launcher_trigger


class VercelButton(NSButton):
    def initWithFrame_(self, frame):
        self = objc.super(VercelButton, self).initWithFrame_(frame)
        if self is None:
            return None
        try:
            self.setWantsLayer_(True)
            self.layer().setCornerRadius_(10.0)
            self.layer().setMasksToBounds_(True)
            # Base ghost style (subtle surface, no border)
            self._base_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08)
            self._hover_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.14)
            self._press_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.22)
            self._dark_style = False
            self.layer().setBackgroundColor_(self._base_bg.CGColor())
            # No visible border and no blue focus ring
            self.layer().setBorderWidth_(0.0)
            try:
                self.setFocusRingType_(NSFocusRingTypeNone)
                self.setBordered_(False)
            except Exception:
                pass
        except Exception:
            pass
        self._tracking_area = None
        self._is_primary = False
        return self

    def resetCursorRects(self):
        try:
            self.discardCursorRects()
            self.addCursorRect_cursor_(self.bounds(), NSCursor.pointingHandCursor())
        except Exception:
            pass
        try:
            objc.super(VercelButton, self).resetCursorRects()
        except Exception:
            pass

    def _apply_title_color(self, color):
        try:
            from AppKit import NSForegroundColorAttributeName
            title = self.title() or ""
            attr = {NSForegroundColorAttributeName: color}
            self.setAttributedTitle_(NSAttributedString.alloc().initWithString_attributes_(title, attr))
        except Exception:
            pass

    def setStyleDark_(self, dark):
        self._dark_style = bool(dark)
        try:
            if self._dark_style:
                self._base_bg = NSColor.blackColor().colorWithAlphaComponent_(0.86)
                self._hover_bg = NSColor.blackColor().colorWithAlphaComponent_(0.93)
                self._press_bg = NSColor.blackColor().colorWithAlphaComponent_(1.0)
                self.layer().setBorderWidth_(0.0)
                self.layer().setBorderColor_(NSColor.clearColor().CGColor())
                self._apply_title_color(NSColor.whiteColor())
            else:
                self._base_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08)
                self._hover_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.14)
                self._press_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.22)
            self.layer().setBackgroundColor_(self._base_bg.CGColor())
        except Exception:
            pass

    def setTitle_(self, title):
        # Ensure white title on dark style even after localization resets the title
        try:
            objc.super(VercelButton, self).setTitle_(title)
            from AppKit import NSForegroundColorAttributeName
            if getattr(self, '_dark_style', False):
                color = NSColor.whiteColor()
            else:
                try:
                    color = NSColor.labelColor()
                except Exception:
                    color = NSColor.blackColor()
            attr = {NSForegroundColorAttributeName: color}
            self.setAttributedTitle_(NSAttributedString.alloc().initWithString_attributes_(title or "", attr))
        except Exception:
            try:
                objc.super(VercelButton, self).setTitle_(title)
            except Exception:
                pass
        return None

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
        objc.super(VercelButton, self).updateTrackingAreas()

    def mouseEntered_(self, event):
        try:
            self.layer().setBackgroundColor_(self._hover_bg.CGColor())
        except Exception:
            pass

    def mouseExited_(self, event):
        try:
            self.layer().setBackgroundColor_(self._base_bg.CGColor())
        except Exception:
            pass

    def mouseDown_(self, event):
        try:
            self.layer().setBackgroundColor_(self._press_bg.CGColor())
        except Exception:
            pass
        objc.super(VercelButton, self).mouseDown_(event)

    def mouseUp_(self, event):
        try:
            self.layer().setBackgroundColor_(self._hover_bg.CGColor())
        except Exception:
            pass
        objc.super(VercelButton, self).mouseUp_(event)

    def setPrimary_(self, primary):
        self._is_primary = bool(primary)
        try:
            if primary:
                # Use system accent with transparency
                self._base_bg = NSColor.controlAccentColor().colorWithAlphaComponent_(0.28)
                self._hover_bg = NSColor.controlAccentColor().colorWithAlphaComponent_(0.36)
                self._press_bg = NSColor.controlAccentColor().colorWithAlphaComponent_(0.44)
                self.layer().setBorderWidth_(0.0)
                self.layer().setBorderColor_(NSColor.clearColor().CGColor())
            else:
                self._base_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08)
                self._hover_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.14)
                self._press_bg = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.22)
                self.layer().setBorderWidth_(0.0)
                self.layer().setBorderColor_(NSColor.clearColor().CGColor())
            self.layer().setBackgroundColor_(self._base_bg.CGColor())
        except Exception:
            pass

class CardView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(CardView, self).initWithFrame_(frame)
        if self is None:
            return None
        try:
            self.setWantsLayer_(True)
            self.layer().setCornerRadius_(20.0)
            # Mask subviews to achieve true rounded window look on transparent window
            self.layer().setMasksToBounds_(True)
            # Adaptive background
            bg = NSColor.windowBackgroundColor().colorWithAlphaComponent_(0.75)
            self.layer().setBackgroundColor_(bg.CGColor())
            # Remove border for a cleaner card look
            self.layer().setBorderWidth_(0.0)
            # Soft shadow
            self.layer().setShadowColor_(NSColor.blackColor().CGColor())
            self.layer().setShadowOpacity_(0.18)
            self.layer().setShadowRadius_(10.0)
            self.layer().setShadowOffset_((0.0, -1.0))
        except Exception:
            pass
        return self

class BBPointerPopUpButton(NSPopUpButton):
    def resetCursorRects(self):
        try:
            self.discardCursorRects()
            self.addCursorRect_cursor_(self.bounds(), NSCursor.pointingHandCursor())
        except Exception:
            pass
        try:
            objc.super(BBPointerPopUpButton, self).resetCursorRects()
        except Exception:
            pass

class BBPointerCheckbox(NSButton):
    def resetCursorRects(self):
        try:
            self.discardCursorRects()
            self.addCursorRect_cursor_(self.bounds(), NSCursor.pointingHandCursor())
        except Exception:
            pass
        try:
            objc.super(BBPointerCheckbox, self).resetCursorRects()
        except Exception:
            pass

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
        # Borderless settings panel window with large rounded corners
        rect = NSMakeRect(0, 0, 460, 320)
        class SettingsPanelWindow(NSWindow):
            def canBecomeKeyWindow(self):
                return True
            def canBecomeMainWindow(self):
                return True
        self.window = SettingsPanelWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        self.window.setReleasedWhenClosed_(False)
        try:
            self.window.setHasShadow_(True)
            self.window.setOpaque_(False)
            self.window.setBackgroundColor_(NSColor.clearColor())
            self.window.setMovableByWindowBackground_(True)
        except Exception:
            pass
        self._build_ui()

    def _build_ui(self):
        content = self.window.contentView()
        bounds = content.bounds()

        # Background: default to solid (black/white Vercel style). Enable blur only when BB_USE_BLUR=1
        try:
            if os.environ.get('BB_NO_EFFECTS') == '1' or os.environ.get('BB_USE_BLUR') != '1':
                raise Exception('effects disabled or blur not requested')
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

        # Card container (fill window to realize large rounded corners)
        margin = 0
        card_frame = NSMakeRect(margin, margin, bounds.size.width - margin * 2, bounds.size.height - margin * 2)
        self.card = CardView.alloc().initWithFrame_(card_frame)
        try:
            self.card.setAutoresizingMask_((1 << 1) | (1 << 4) | (1 << 3) | (1 << 0))  # width/height + minX/maxY
        except Exception:
            pass
        content.addSubview_(self.card)
        # If a blur background was created earlier, move it inside the card so
        # the large rounded corners mask it correctly.
        try:
            if self.bg_blur is not None:
                try:
                    self.bg_blur.removeFromSuperview()
                except Exception:
                    pass
                self.bg_blur.setFrame_(self.card.bounds())
                # autoresize with card
                self.bg_blur.setAutoresizingMask_((1 << 1) | (1 << 4))
                # Add behind other card content
                self.card.addSubview_(self.bg_blur)
        except Exception:
            pass
        # Apply black/white theme to card and controls
        self._apply_theme()

        def add_label(text, x, y, w, h, bold=False):
            lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            lbl.setStringValue_(text)
            if bold:
                lbl.setFont_(NSFont.boldSystemFontOfSize_(18))
            else:
                lbl.setFont_(NSFont.systemFontOfSize_(16))
            try:
                lbl.setTextColor_(NSColor.labelColor())
            except Exception:
                pass
            self.card.addSubview_(lbl)
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
                # Subtle card-like background, no borders
                btn.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).CGColor())
                try:
                    btn.setFocusRingType_(NSFocusRingTypeNone)
                    btn.setBordered_(False)
                    btn.setFont_(NSFont.systemFontOfSize_(16))
                except Exception:
                    pass
            except Exception:
                pass
            return btn

        def add_button(title, x, y, w, h):
            btn = VercelButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            btn.setTitle_(title)
            style_button(btn)
            self.card.addSubview_(btn)
            return btn

        def add_image_view(img, x, y, w, h):
            iv = NSImageView.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            try:
                iv.setImageScaling_(1)  # NSImageScaleProportionallyUpOrDown
            except Exception:
                pass
            try:
                iv.setWantsLayer_(True)
                iv.layer().setMasksToBounds_(True)
                iv.layer().setCornerRadius_(4.0)
            except Exception:
                pass
            iv.setImage_(img)
            self.card.addSubview_(iv)
            return iv

        # Header: centered logo only (no title)
        logo_img = self._load_logo_for_appearance()
        card_bounds = self.card.bounds()
        logo_size = 40
        top_margin = 16
        if logo_img is not None:
            lx = (card_bounds.size.width - logo_size) / 2
            ly = card_bounds.size.height - top_margin - logo_size
            self.header_logo_view = add_image_view(logo_img, lx, ly, logo_size, logo_size)
        # No title label

        # Layout constants
        pad_x = 24  # left padding for labels/checkbox
        group_shift_x = 10  # slight right shift for centered groups
        # Language selector + uniform row centers (equal spacing)
        row_gap = 52
        language_center = (ly - 36) if logo_img is not None else (card_bounds.size.height - 96)
        self.lang_label = add_label(_t('settings.language'), pad_x, language_center - 11, 120, 22)
        self.lang_popup = BBPointerPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(pad_x + 140, language_center - 17, 220, 34), False)
        self.lang_popup.addItemWithTitle_("English")
        self.lang_popup.addItemWithTitle_("中文")
        self.lang_popup.addItemWithTitle_("日本語")
        self.lang_popup.addItemWithTitle_("한국어")
        self.lang_popup.addItemWithTitle_("Français")
        try:
            # Add a subtle visible border and rounded corners for discoverability
            self.lang_popup.setWantsLayer_(True)
            self.lang_popup.setBordered_(False)
            self.lang_popup.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
            self.lang_popup.layer().setCornerRadius_(6.0)
            self.lang_popup.layer().setBorderWidth_(1.0)
            try:
                dark = self._is_dark()
                border = (NSColor.whiteColor().colorWithAlphaComponent_(0.22) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.18))
                self.lang_popup.layer().setBorderColor_(border.CGColor())
            except Exception:
                pass
            try:
                self.lang_popup.setFont_(NSFont.systemFontOfSize_(16))
            except Exception:
                pass
        except Exception:
            pass
        self.card.addSubview_(self.lang_popup)

        # Launch at login
        self.launch_checkbox = BBPointerCheckbox.alloc().initWithFrame_(NSMakeRect(pad_x, 0, 260, 24))
        self.launch_checkbox.setButtonType_(NSSwitchButton)
        self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
        try:
            self.launch_checkbox.setFont_(NSFont.systemFontOfSize_(16))
        except Exception:
            pass
        self.card.addSubview_(self.launch_checkbox)
        # Disable on non-Darwin
        try:
            import platform as _platform

            if _platform.system().lower() != 'darwin':
                self.launch_checkbox.setEnabled_(False)
                try:
                    self.launch_checkbox.setToolTip_("macOS only")
                except Exception:
                    pass
        except Exception:
            pass

        # Hotkey row — center aligned using row centers
        hotkey_center = language_center - row_gap
        self.hotkey_label = add_label(_t('settings.hotkey'), pad_x, hotkey_center - 12, 80, 24)
        # Center the value + button group horizontally, but avoid overlap with label area
        group_w = 220 + 16 + 112
        min_left = pad_x + 80 + 12
        hv_x = max(min_left, (card_bounds.size.width - group_w) / 2 + group_shift_x)
        self.hotkey_value = add_label("", hv_x, hotkey_center - 12, 220, 24)
        self.hotkey_button = add_button(_t('button.change'), hv_x + 220 + 16, hotkey_center - 17, 112, 34)
        try:
            self.hotkey_button.setStyleDark_(True)
        except Exception:
            pass
        self.hotkey_button.setTarget_(self)
        self.hotkey_button.setAction_("changeHotkey:")
        try:
            self.hotkey_button.setAutoresizingMask_((1 << 1) | (1 << 3))  # width + maxY
        except Exception:
            pass

        # Clear cache — center aligned using row centers
        clear_center = hotkey_center - row_gap
        cc_w, cc_h = 140, 34
        cc_x = (card_bounds.size.width - cc_w) / 2 + group_shift_x
        self.clear_cache_button = add_button(_t('settings.clearCache'), cc_x, clear_center - cc_h / 2, cc_w, cc_h)
        try:
            self.clear_cache_button.setStyleDark_(True)
        except Exception:
            pass
        self.clear_cache_button.setTarget_(self)
        self.clear_cache_button.setAction_("clearCache:")

        # Save / Cancel — center aligned using row centers
        extra_bottom_gap = 12  # slightly larger gap between Clear and Save
        bottom_center = clear_center - (row_gap + extra_bottom_gap)
        cancel_w, cancel_h = 92, 34
        save_w, save_h = 104, 34
        pad = 16
        spacing = 12
        # Center the Save+Cancel group horizontally with slight right shift
        group_w2 = save_w + spacing + cancel_w
        group_left = (card_bounds.size.width - group_w2) / 2 + group_shift_x
        save_x = group_left
        cancel_x = group_left + save_w + spacing
        self.save_button = add_button(_t('button.save') if hasattr(self, 'window') else "Save", save_x, bottom_center - save_h / 2, save_w, save_h)
        self.save_button.setTarget_(self)
        self.save_button.setAction_("saveSettings:")
        try:
            self.save_button.setAutoresizingMask_((1 << 1) | (1 << 0))  # width + minX
        except Exception:
            pass
        # Black vercel-style buttons
        try:
            self.save_button.setStyleDark_(True)
        except Exception:
            pass
        self.cancel_button = add_button(_t('button.cancel'), cancel_x, bottom_center - cancel_h / 2, cancel_w, cancel_h)
        self.cancel_button.setTarget_(self)
        self.cancel_button.setAction_("cancelSettings:")
        try:
            self.cancel_button.setAutoresizingMask_((1 << 1) | (1 << 0))
        except Exception:
            pass
        try:
            self.cancel_button.setStyleDark_(True)
        except Exception:
            pass
        # Launch at login aligned with Save/Cancel row center
        try:
            self.launch_checkbox.setFrameOrigin_((16, bottom_center - 24 / 2))
        except Exception:
            pass

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
        # Launch at login
        try:
            if login_items.is_supported():
                launch = bool(login_items.is_enabled())
            else:
                cfg = ConfigManager.load()
                launch = bool(cfg.get("launch_at_login", False))
        except Exception:
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
        if self.hotkey_button:
            try:
                self.hotkey_button.setStyleDark_(True)
            except Exception:
                pass
        if self.clear_cache_button:
            self.clear_cache_button.setTitle_(_t('settings.clearCache'))
            try:
                self.clear_cache_button.setStyleDark_(True)
            except Exception:
                pass
        if self.save_button:
            self.save_button.setTitle_(_t('button.save'))
            try:
                self.save_button.setStyleDark_(True)
            except Exception:
                pass
        if self.cancel_button:
            self.cancel_button.setTitle_(_t('button.cancel'))
            try:
                self.cancel_button.setStyleDark_(True)
            except Exception:
                pass
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
            try:
                # Prepare card for slight rise + fade
                if hasattr(self, 'card') and self.card:
                    cf = self.card.frame()
                    self.card.setAlphaValue_(0.0)
                    self.card.setFrameOrigin_((cf.origin.x, cf.origin.y - 6))
            except Exception:
                pass
            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            NSAnimationContext.beginGrouping()
            NSAnimationContext.currentContext().setDuration_(0.18)
            self.window.animator().setAlphaValue_(1.0)
            try:
                # Animate card in
                if hasattr(self, 'card') and self.card:
                    cf = self.card.frame()
                    self.card.animator().setAlphaValue_(1.0)
                    self.card.animator().setFrameOrigin_((cf.origin.x, cf.origin.y + 6))
            except Exception:
                pass
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
        # Launch at login
        try:
            try:
                state = bool(self.launch_checkbox.state())
            except Exception:
                state = False
            if login_items.is_supported():
                ok, _msg = login_items.set_enabled(state)
                # Persist mirror state for UI consistency
                cfg = ConfigManager.load()
                cfg["launch_at_login"] = bool(state and ok)
                ConfigManager.save(cfg)
            else:
                # Non-Darwin: keep persisted flag only (UI disabled to prevent change)
                cfg = ConfigManager.load()
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
            # Show localized toast feedback
            self._show_toast(_t('settings.clearCacheDone'))
        except Exception:
            # Best-effort feedback even if clearing threw
            try:
                self._show_toast(_t('settings.clearCacheDone'))
            except Exception:
                pass

    def changeHotkey_(self, sender):
        try:
            # Show the hotkey overlay attached to the Settings window so it appears on top
            set_custom_launcher_trigger(self.app_delegate, target_window=self.window)
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
        """Load a small colored rounded app logo for the header.

        Prefer a colored icon from icon.iconset; fall back to monochrome
        white/black assets when unavailable.
        """
        try:
            # Preferred colored icon candidates (rounded PNGs)
            color_candidates = [
                'logo/icon.iconset/icon_32x32@2x.png',
                'logo/icon.iconset/icon_32x32.png',
                'logo/icon.iconset/icon_64x64.png',
            ]
            # Try package data first (inside app bundle)
            try:
                import pkgutil
                from Foundation import NSData
                for rel in color_candidates:
                    data = pkgutil.get_data('bubblebot', rel)
                    if data:
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
                for rel in color_candidates:
                    p = os.path.join(here, '..', rel)
                    p = os.path.normpath(p)
                    img = NSImage.alloc().initWithContentsOfFile_(p)
                    if img is not None:
                        return img
            except Exception:
                pass
        except Exception:
            pass
        # Last resort: fall back to monochrome for current appearance
        try:
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
            import pkgutil
            from Foundation import NSData
            data = pkgutil.get_data('bubblebot', rel_path)
            if data:
                nsdata = NSData.dataWithBytes_length_(data, len(data))
                img = NSImage.alloc().initWithData_(nsdata)
                if img is not None:
                    return img
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

    def _is_dark(self):
        try:
            app = NSApp
            appearance = app.effectiveAppearance()
            name = appearance.bestMatchFromAppearancesWithNames_(["NSAppearanceNameDarkAqua", "NSAppearanceNameAqua"])
            return name == "NSAppearanceNameDarkAqua"
        except Exception:
            return False

    def _apply_theme(self):
        # Apply Vercel-style card and keep the window itself transparent so rounded corners are visible
        try:
            dark = self._is_dark()
            if self.window:
                try:
                    self.window.setOpaque_(False)
                    self.window.setBackgroundColor_(NSColor.clearColor())
                except Exception:
                    pass
            if hasattr(self, 'card') and self.card and self.card.layer():
                card_bg = NSColor.colorWithCalibratedWhite_alpha_(0.10, 0.96) if dark else NSColor.whiteColor()
                self.card.layer().setBackgroundColor_(card_bg.CGColor())
                try:
                    self.card.layer().setBorderWidth_(0.0)
                except Exception:
                    pass
        except Exception:
            pass

    def _show_toast(self, message: str):
        if not self.window:
            return
        try:
            content = self.card if hasattr(self, 'card') and self.card else self.window.contentView()
            bounds = content.bounds()
            tw, th = 260, 36
            # Top-right corner toast
            margin = 16
            tx = max(margin, bounds.size.width - tw - margin)
            ty = max(margin, bounds.size.height - th - margin)
            toast = NSView.alloc().initWithFrame_(NSMakeRect(tx, ty, tw, th))
            toast.setWantsLayer_(True)
            # Black translucent background with rounded corners
            toast.layer().setCornerRadius_(8.0)
            toast.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.85).CGColor())

            lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(12, 8, tw - 24, th - 16))
            lbl.setBezeled_(False); lbl.setDrawsBackground_(False); lbl.setEditable_(False); lbl.setSelectable_(False)
            lbl.setFont_(NSFont.systemFontOfSize_(13))
            try:
                lbl.setTextColor_(NSColor.whiteColor())
            except Exception:
                pass
            lbl.setStringValue_(message)
            toast.addSubview_(lbl)

            # Start hidden and fade in/out
            toast.setAlphaValue_(0.0)
            content.addSubview_(toast)
            try:
                if os.environ.get('BB_NO_EFFECTS') != '1':
                    NSAnimationContext.beginGrouping()
                    NSAnimationContext.currentContext().setDuration_(0.18)
                    toast.animator().setAlphaValue_(1.0)
                    NSAnimationContext.endGrouping()
            except Exception:
                toast.setAlphaValue_(1.0)

            # Auto dismiss after 1.2s
            try:
                from Foundation import NSTimer
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    1.2, self, 'dismissToast:', toast, False
                )
            except Exception:
                pass
        except Exception:
            pass

    def dismissToast_(self, timer):
        try:
            toast = timer.userInfo()
            if os.environ.get('BB_NO_EFFECTS') != '1':
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.18)
                toast.animator().setAlphaValue_(0.0)
                NSAnimationContext.endGrouping()
            toast.removeFromSuperview()
        except Exception:
            pass

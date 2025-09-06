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
    # The following may not exist on older macOS; used conditionally
    # NSImageSymbolConfiguration is looked up dynamically in helpers
    NSImageLeft,
    NSImageScaleProportionallyUpOrDown,
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
try:
    from Quartz.CoreAnimation import CAGradientLayer, CATextLayer
except Exception:
    CAGradientLayer = None
    CATextLayer = None

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
        self.launch_label = None
        self.hotkey_label = None
        self.hotkey_value = None
        self.hotkey_box = None
        self.hotkey_button = None
        self.clear_cache_button = None
        self.save_button = None
        self.cancel_button = None
        self.header_logo_view = None
        self.header_art_label = None
        self.header_title_label = None
        self.header_art_view = None
        self.bg_blur = None
        # Small icon views for label rows
        self.lang_icon_view = None
        self.hotkey_icon_view = None
        # Layout tuning offsets
        self._launch_x_offset = -20  # shift Launch at Login slightly left
        # Legacy overlay storage (previous approach). We'll remove overlays and
        # rely on native NSButton image+title rendering for stability.
        self._button_icon_views = {}
        self._button_text_labels = {}
        return self

    def _create_window(self):
        # Borderless settings panel window with large rounded corners
        # Increase width to add more horizontal whitespace while keeping content centered
        # Increase bottom whitespace (about 412 height as requested +12)
        rect = NSMakeRect(0, 0, 560, 412)
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

        # UI text helpers are instance methods so they can also be used in _apply_localization

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
        # Enlarge logo a bit further (~1.2x again)
        logo_size = 70
        top_margin = 16
        if logo_img is not None:
            lx = (card_bounds.size.width - logo_size) / 2 - 52  # shift logo left further by 20
            ly = card_bounds.size.height - top_margin - logo_size
            self.header_logo_view = add_image_view(logo_img, lx, ly, logo_size, logo_size)
            # Artistic "Bubble" text (gradient pink, bold, right of logo)
            try:
                art_h = 34
                art_w = 220
                art_x = lx + logo_size + 12
                art_y = ly + (logo_size - art_h) / 2
                self.header_art_view = NSView.alloc().initWithFrame_(NSMakeRect(art_x, art_y, art_w, art_h))
                self.header_art_view.setWantsLayer_(True)
                if CAGradientLayer and CATextLayer:
                    grad = CAGradientLayer.layer()
                    grad.setFrame_(self.header_art_view.bounds())
                    # Pink gradient colors
                    c1 = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.52, 0.82, 1.0).CGColor()
                    c2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.29, 0.62, 1.0).CGColor()
                    c3 = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.18, 0.46, 1.0).CGColor()
                    grad.setColors_([c1, c2, c3])
                    grad.setStartPoint_((0.0, 0.5))
                    grad.setEndPoint_((1.0, 0.5))
                    # Text mask layer
                    tl = CATextLayer.layer()
                    tl.setString_("Bubble")
                    try:
                        tl.setAlignmentMode_("left")
                    except Exception:
                        pass
                    try:
                        # Prefer a cute, heavier font family; fallback handled by system
                        tl.setFont_("ChalkboardSE-Bold")
                        tl.setFontSize_(30.0)
                    except Exception:
                        pass
                    try:
                        # Avoid blurry text on Retina
                        from AppKit import NSScreen
                        scale = NSScreen.mainScreen().backingScaleFactor() if NSScreen.mainScreen() else 2.0
                        tl.setContentsScale_(scale)
                    except Exception:
                        pass
                    tl.setFrame_(self.header_art_view.bounds())
                    # Apply mask
                    grad.setMask_(tl)
                    self.header_art_view.layer().addSublayer_(grad)
                else:
                    # Fallback: solid pink bold label inside art view (correctly positioned)
                    lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, art_w, art_h))
                    lbl.setBezeled_(False)
                    lbl.setDrawsBackground_(False)
                    lbl.setEditable_(False)
                    lbl.setSelectable_(False)
                    lbl.setStringValue_("Bubble")
                    try:
                        lbl.setAlignment_(NSTextAlignmentLeft)
                    except Exception:
                        pass
                    # Choose a cute bold font chain
                    try:
                        font = (
                            NSFont.fontWithName_size_("Chalkboard SE Bold", 30)
                            or NSFont.fontWithName_size_("ChalkboardSE-Bold", 30)
                            or NSFont.fontWithName_size_("MarkerFelt-Wide", 30)
                            or NSFont.fontWithName_size_("Noteworthy-Bold", 30)
                            or NSFont.fontWithName_size_("AvenirNext-Heavy", 30)
                            or NSFont.fontWithName_size_("Helvetica-Bold", 30)
                            or NSFont.boldSystemFontOfSize_(28)
                        )
                        if font:
                            lbl.setFont_(font)
                    except Exception:
                        pass
                    try:
                        lbl.setTextColor_(NSColor.systemPinkColor())
                    except Exception:
                        pass
                    try:
                        self.header_art_view.addSubview_(lbl)
                    except Exception:
                        pass
                self.card.addSubview_(self.header_art_view)
            except Exception:
                pass
        # No title label

        # Layout constants — revert global right shift to original modest values
        pad_x = 24  # left padding for labels/checkbox
        # Keep centered groups without extra right shift
        group_shift_x = 0
        # Language selector + uniform row centers (equal spacing)
        row_gap = 72  # increase each inter-row gap by +20
        # Move content slightly downward to compensate the larger logo
        content_down_shift = 12
        language_center = (ly - 36 - content_down_shift) if logo_img is not None else (card_bounds.size.height - 96 - content_down_shift)
        # Shift language title 50px to the right (20 + 30)
        self.lang_label = add_label(_t('settings.language'), pad_x + 50, language_center - 11, 120, 22)
        # Attach a nice icon to the Language label (no emoji)
        try:
            self._set_label_text_with_icon(self.lang_label, _t('settings.language'), 'globe')
        except Exception:
            pass
        # Language dropdown: center align around the content center and slightly shorten width
        content_center_x = card_bounds.size.width / 2 + group_shift_x
        lang_w = 150  # reduce to three-quarters of previous width
        # Move dropdown 45px left from centered position (previous 40 + 5)
        self.lang_popup = BBPointerPopUpButton.alloc().initWithFrame_pullsDown_(
            # Nudge a bit further to the right
            NSMakeRect(content_center_x - lang_w / 2 + 10, language_center - 17, lang_w, 34), False
        )
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
            # Center the selected title text within the popup
            try:
                cell = self.lang_popup.cell()
                if cell is not None:
                    cell.setAlignment_(NSTextAlignmentCenter)
            except Exception:
                try:
                    # Fallback: attempt alignment on control if supported
                    self.lang_popup.setAlignment_(NSTextAlignmentCenter)
                except Exception:
                    pass
        except Exception:
            pass
        self.card.addSubview_(self.lang_popup)

        # Launch at login
        # Launch at login: revert to original combined control (checkbox + title)
        self.launch_checkbox = BBPointerCheckbox.alloc().initWithFrame_(NSMakeRect(pad_x, 0, 260, 24))
        self.launch_checkbox.setButtonType_(NSSwitchButton)
        # Add icon + text to checkbox (native image+title; indicator在最左)
        try:
            self._set_control_title_with_icon(self.launch_checkbox, _t('settings.launchAtLogin'), 'power', center_group=False)
        except Exception:
            # Fallback to plain text
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
        # Shift hotkey title 50px to the right (20 + 30)
        self.hotkey_label = add_label(_t('settings.hotkey'), pad_x + 50, hotkey_center - 12, 80, 24)
        # Attach icon to Hotkey label
        try:
            self._set_label_text_with_icon(self.hotkey_label, _t('settings.hotkey'), 'keyboard')
        except Exception:
            pass
        # Center the value + button group horizontally to the same center as language dropdown
        # Create a bordered hotkey box (container) with a centered text label that resizes to content
        hv_w = 160  # temporary width; will be replaced by dynamic sizing
        spacing_hotkey = 28  # increase gap between hotkey box and Change
        group_w = hv_w + spacing_hotkey + 112
        min_left = pad_x + 80 + 12
        hv_base = max(min_left, (card_bounds.size.width - group_w) / 2 + group_shift_x)
        # Store layout anchors for dynamic updates
        self._hotkey_group_base_x = hv_base
        self._hotkey_value_y = hotkey_center - 12
        self._hotkey_button_y = hotkey_center - 17
        self._hotkey_right_shift = 0  # value starts at group base; overall group stays centered
        self._hotkey_spacing = spacing_hotkey
        hv_x_init = hv_base + self._hotkey_right_shift
        # Create bordered container view
        box_h = 28
        # Slight upward offset so the text feels visually centered in the row
        self._hotkey_box_y_offset = 3
        self.hotkey_box = NSView.alloc().initWithFrame_(NSMakeRect(hv_x_init, hotkey_center - box_h / 2 + self._hotkey_box_y_offset, hv_w, box_h))
        try:
            self.hotkey_box.setWantsLayer_(True)
            # Full rounded corners
            try:
                self.hotkey_box.layer().setCornerRadius_(box_h / 2.0)
            except Exception:
                self.hotkey_box.layer().setCornerRadius_(6.0)
            self.hotkey_box.layer().setBorderWidth_(1.0)
            self.hotkey_box.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
            dark = self._is_dark()
            border = (NSColor.whiteColor().colorWithAlphaComponent_(0.28) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.22))
            self.hotkey_box.layer().setBorderColor_(border.CGColor())
        except Exception:
            pass
        self.card.addSubview_(self.hotkey_box)
        # Inner centered text field
        self.hotkey_value = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, hv_w, box_h))
        self.hotkey_value.setBezeled_(False)
        self.hotkey_value.setDrawsBackground_(False)
        self.hotkey_value.setEditable_(False)
        self.hotkey_value.setSelectable_(False)
        try:
            self.hotkey_value.setAlignment_(NSTextAlignmentCenter)
            self.hotkey_value.setFont_(NSFont.systemFontOfSize_(16))
            self.hotkey_value.setTextColor_(NSColor.labelColor())
        except Exception:
            pass
        try:
            self.hotkey_box.addSubview_(self.hotkey_value)
        except Exception:
            pass
        # Place the Change button relative to the value so the gap equals spacing_hotkey
        hotkey_button_x = hv_x_init + hv_w + spacing_hotkey + 85  # shift Change/Cancel further right by ~25
        self.hotkey_button = add_button(_t('button.change'), hotkey_button_x, self._hotkey_button_y, 112, 34)
        try:
            self.hotkey_button.setStyleDark_(True)
        except Exception:
            pass
        # Apply icon to Change button (no emoji)
        try:
            self._set_control_title_with_icon(self.hotkey_button, _t('button.change'), 'pencil')
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
        cc_w, cc_h = 146, 34  # 1.3x wider (from 112), keep centered by formula below
        cc_x = (card_bounds.size.width - cc_w) / 2 + group_shift_x + 8  # nudge Clear Cache slightly right
        self.clear_cache_button = add_button(_t('settings.clearCache'), cc_x, clear_center - cc_h / 2, cc_w, cc_h)
        try:
            self.clear_cache_button.setStyleDark_(True)
        except Exception:
            pass
        # Apply icon to Clear Cache (no emoji)
        try:
            self._set_control_title_with_icon(self.clear_cache_button, _t('settings.clearCache'), 'broom')
        except Exception:
            pass
        self.clear_cache_button.setTarget_(self)
        self.clear_cache_button.setAction_("clearCache:")

        # Save / Cancel — align Save with Clear Cache horizontally (left edges), Cancel align with Change
        extra_bottom_gap = 12  # slightly larger gap between Clear and Save
        bottom_center = clear_center - (row_gap + extra_bottom_gap)
        cancel_w, cancel_h = 112, 34  # unified button width
        save_w, save_h = 112, 34      # unified button width
        spacing = 16
        save_x = cc_x  # align Save left edge with Clear Cache left edge
        cancel_x = hotkey_button_x  # align Cancel left edge with Change button
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
        # Apply icon to Save (no emoji)
        try:
            self._set_control_title_with_icon(self.save_button, _t('button.save') if hasattr(self, 'window') else "Save", 'checkmark.circle')
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
        # Apply icon to Cancel (no emoji)
        try:
            self._set_control_title_with_icon(self.cancel_button, _t('button.cancel'), 'xmark.circle')
        except Exception:
            pass
        # No extra alignment for Clear Cache; it remains centered above Save/Cancel
        # Launch at login aligned with Save/Cancel row center — align horizontally with Hotkey title
        try:
            self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
            try:
                hx = int(self.hotkey_label.frame().origin.x)
            except Exception:
                hx = pad_x + 50
            # Slightly shift left to align with other label rows (a bit more left)
            self.launch_checkbox.setFrameOrigin_((hx + getattr(self, '_launch_x_offset', -20), bottom_center - 24 / 2))
            try:
                if self.launch_label is not None:
                    # Hide the separate label if it exists from prior layouts
                    self.launch_label.setHidden_(True)
            except Exception:
                pass
        except Exception:
            pass

        self._load_values_into_ui()

        # After initial values are loaded, update hotkey layout to fit content
        try:
            self._update_hotkey_group_layout()
        except Exception:
            pass

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
                try:
                    self._update_hotkey_group_layout()
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_localization(self):
        if not self.window:
            return
        self.window.setTitle_(_t('settings.title'))
        if self.lang_label:
            try:
                self._set_label_text_with_icon(self.lang_label, _t('settings.language'), 'globe')
            except Exception:
                self.lang_label.setStringValue_(_t('settings.language'))
        if self.launch_checkbox:
            try:
                self._set_control_title_with_icon(self.launch_checkbox, _t('settings.launchAtLogin'), 'power', center_group=False)
            except Exception:
                try:
                    self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
                except Exception:
                    pass
        if self.hotkey_label:
            try:
                self._set_label_text_with_icon(self.hotkey_label, _t('settings.hotkey'), 'keyboard')
            except Exception:
                self.hotkey_label.setStringValue_(_t('settings.hotkey'))
        if self.hotkey_button:
            try:
                self.hotkey_button.setStyleDark_(True)
            except Exception:
                pass
            try:
                # Re-apply iconized title after localization changes
                self._set_control_title_with_icon(self.hotkey_button, _t('button.change'), 'pencil')
            except Exception:
                pass
        if self.clear_cache_button:
            self.clear_cache_button.setTitle_(_t('settings.clearCache'))
            try:
                self.clear_cache_button.setStyleDark_(True)
            except Exception:
                pass
            try:
                self._set_control_title_with_icon(self.clear_cache_button, _t('settings.clearCache'), 'broom')
            except Exception:
                pass
        if self.save_button:
            self.save_button.setTitle_(_t('button.save'))
            try:
                self.save_button.setStyleDark_(True)
            except Exception:
                pass
            try:
                self._set_control_title_with_icon(self.save_button, _t('button.save'), 'checkmark.circle')
            except Exception:
                pass
        if self.cancel_button:
            self.cancel_button.setTitle_(_t('button.cancel'))
            try:
                self.cancel_button.setStyleDark_(True)
            except Exception:
                pass
            try:
                self._set_control_title_with_icon(self.cancel_button, _t('button.cancel'), 'xmark.circle')
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
        # Present a custom Vercel-style confirmation overlay
        try:
            self._present_clear_cache_confirm()
        except Exception:
            # Fallback: perform clear directly if overlay failed to present
            self._perform_clear_cache()

    def _perform_clear_cache(self):
        try:
            if hasattr(self.app_delegate, 'clearWebViewData_'):
                self.app_delegate.clearWebViewData_(None)
            self._show_toast(_t('settings.clearCacheDone'))
        except Exception:
            try:
                self._show_toast(_t('settings.clearCacheDone'))
            except Exception:
                pass

    def _present_clear_cache_confirm(self):
        # Avoid showing multiple overlays
        if getattr(self, '_confirm_overlay', None) is not None:
            return
        container = self.card if hasattr(self, 'card') and self.card else self.window.contentView()
        bounds = container.bounds()
        # Dimmed backdrop
        overlay = NSView.alloc().initWithFrame_(bounds)
        overlay.setWantsLayer_(True)
        try:
            overlay.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.36).CGColor())
        except Exception:
            pass
        # Dialog card
        dlg_w, dlg_h = 360, 168
        dlg_x = int((bounds.size.width - dlg_w) / 2)
        dlg_y = int((bounds.size.height - dlg_h) / 2)
        dialog = NSView.alloc().initWithFrame_(NSMakeRect(dlg_x, dlg_y, dlg_w, dlg_h))
        try:
            dialog.setWantsLayer_(True)
            dark = self._is_dark()
            bg = (NSColor.colorWithCalibratedWhite_alpha_(0.12, 0.96) if dark else NSColor.whiteColor())
            dialog.layer().setBackgroundColor_(bg.CGColor())
            dialog.layer().setCornerRadius_(14.0)
            dialog.layer().setBorderWidth_(1.0)
            border = (NSColor.whiteColor().colorWithAlphaComponent_(0.12) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.08))
            dialog.layer().setBorderColor_(border.CGColor())
            # Soft shadow
            try:
                dialog.layer().setShadowColor_(NSColor.blackColor().CGColor())
                dialog.layer().setShadowOpacity_(0.18)
                dialog.layer().setShadowRadius_(12.0)
                dialog.layer().setShadowOffset_((0.0, -1.0))
            except Exception:
                pass
        except Exception:
            pass

        # Title and message
        ttl = NSTextField.alloc().initWithFrame_(NSMakeRect(18, dlg_h - 44, dlg_w - 36, 24))
        ttl.setBezeled_(False); ttl.setDrawsBackground_(False); ttl.setEditable_(False); ttl.setSelectable_(False)
        ttl.setStringValue_(_t('settings.clearCacheConfirmTitle', default='Clear Cache?'))
        try:
            ttl.setFont_(NSFont.boldSystemFontOfSize_(18))
            ttl.setTextColor_(NSColor.labelColor())
        except Exception:
            pass
        # Position message to avoid overlap with title and buttons
        btn_h = 34
        btn_y = 16
        msg_y = btn_y + btn_h + 20  # ensure ~20px gap above buttons
        msg_h = dlg_h - msg_y - 44  # leave space below title area (~44)
        if msg_h < 28:
            msg_h = 28
        msg = NSTextField.alloc().initWithFrame_(NSMakeRect(18, msg_y, dlg_w - 36, msg_h))
        msg.setBezeled_(False); msg.setDrawsBackground_(False); msg.setEditable_(False); msg.setSelectable_(False)
        msg.setStringValue_(_t('settings.clearCacheConfirmMessage', default='This will clear web cache and all login sessions. Continue?'))
        try:
            msg.setFont_(NSFont.systemFontOfSize_(13))
            msg.setTextColor_(NSColor.secondaryLabelColor())
            msg.setLineBreakMode_(0)
        except Exception:
            pass
        dialog.addSubview_(ttl); dialog.addSubview_(msg)

        # Buttons
        btn_h = 34
        btn_w = 112
        spacing = 12
        total_w = btn_w * 2 + spacing
        btn_left_x = int((dlg_w - total_w) / 2)
        btn_y = 16
        confirm_btn = VercelButton.alloc().initWithFrame_(NSMakeRect(btn_left_x, btn_y, btn_w, btn_h))
        confirm_btn.setTitle_(_t('button.confirm', default='Confirm'))
        try:
            # Solid black style
            confirm_btn.setStyleDark_(True)
        except Exception:
            pass
        confirm_btn.setTarget_(self)
        confirm_btn.setAction_("confirmClearCacheAction:")

        cancel_btn = VercelButton.alloc().initWithFrame_(NSMakeRect(btn_left_x + btn_w + spacing, btn_y, btn_w, btn_h))
        cancel_btn.setTitle_(_t('button.cancel'))
        try:
            # White background with black border (ghost)
            cancel_btn.setStyleDark_(False)
            cancel_btn.setWantsLayer_(True)
            cancel_btn.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
            cancel_btn.layer().setBorderWidth_(1.0)
            cancel_btn.layer().setBorderColor_(NSColor.blackColor().colorWithAlphaComponent_(0.85).CGColor())
        except Exception:
            pass
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancelClearCacheConfirm:")

        dialog.addSubview_(confirm_btn); dialog.addSubview_(cancel_btn)

        # Iconize overlay buttons too (ensure it fits; otherwise fallback handled in helper)
        try:
            self._set_control_title_with_icon(confirm_btn, _t('button.confirm', default='Confirm'), 'checkmark')
            self._set_control_title_with_icon(cancel_btn, _t('button.cancel'), 'xmark')
        except Exception:
            pass

        # Assemble
        overlay.addSubview_(dialog)
        overlay.setAlphaValue_(0.0)
        container.addSubview_(overlay)
        self._confirm_overlay = overlay
        try:
            if os.environ.get('BB_NO_EFFECTS') != '1':
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.18)
                overlay.animator().setAlphaValue_(1.0)
                NSAnimationContext.endGrouping()
            else:
                overlay.setAlphaValue_(1.0)
        except Exception:
            overlay.setAlphaValue_(1.0)

    def cancelClearCacheConfirm_(self, sender):
        self._dismiss_confirm_overlay()

    def confirmClearCacheAction_(self, sender):
        try:
            self._perform_clear_cache()
        finally:
            self._dismiss_confirm_overlay()

    def _dismiss_confirm_overlay(self):
        try:
            overlay = getattr(self, '_confirm_overlay', None)
            if overlay is None:
                return
            if os.environ.get('BB_NO_EFFECTS') != '1':
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.18)
                overlay.animator().setAlphaValue_(0.0)
                NSAnimationContext.endGrouping()
            overlay.removeFromSuperview()
        except Exception:
            pass
        finally:
            try:
                setattr(self, '_confirm_overlay', None)
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
                try:
                    self._update_hotkey_group_layout()
                except Exception:
                    pass
        except Exception:
            pass

    def _update_hotkey_group_layout(self):
        """Dynamically size and position the hotkey value label and Change button.
        - Tight border around the value that adapts to content length
        - Keep Change button anchored while reducing gap
        - Apply the right-shift requested for the value label only
        """
        if not (self.hotkey_box and self.hotkey_value and self.hotkey_button):
            return
        try:
            # Measure text width with current font
            text = self.hotkey_value.stringValue() or ""
            try:
                from AppKit import NSFontAttributeName
                from Foundation import NSAttributedString
                font = self.hotkey_value.font() or NSFont.systemFontOfSize_(16)
                attr = {NSFontAttributeName: font}
                measured = NSAttributedString.alloc().initWithString_attributes_(text, attr).size()
                text_w = measured.width
            except Exception:
                text_w = max(60, min(len(text) * 9, 280))

            # Align the hotkey box to Save button horizontally and match its width
            # Fallback to defaults if save_button not available yet
            try:
                sf = self.save_button.frame() if self.save_button is not None else None
            except Exception:
                sf = None
            save_x = sf.origin.x if sf is not None else max(16, self._hotkey_group_base_x)
            save_w = sf.size.width if sf is not None else 104

            hv_w = int(save_w)

            # Update the bordered box frame around the text (with slight upward offset)
            box_h = 28
            # Align the hotkey box left edge with the language dropdown left edge, then nudge right a bit
            try:
                hv_x = int(self.lang_popup.frame().origin.x) + 20  # nudge the hotkey box slightly left from previous
            except Exception:
                hv_x = save_x + 20
            hv_y = self._hotkey_value_y - (box_h - 24) / 2 + getattr(self, '_hotkey_box_y_offset', 0)
            self.hotkey_box.setFrame_(NSMakeRect(hv_x, hv_y, hv_w, box_h))
            try:
                # Full rounded corners
                self.hotkey_box.layer().setCornerRadius_(box_h / 2.0)
            except Exception:
                pass

            # Center the text field inside the box both horizontally and vertically
            lbl_x = 0
            lbl_w = hv_w
            lbl_h = 24
            # Move the text slightly downward within the box (box stays at same Y)
            lbl_y = (box_h - lbl_h) / 2 - 2
            self.hotkey_value.setFrame_(NSMakeRect(lbl_x, lbl_y, lbl_w, lbl_h))
            try:
                self.hotkey_value.setAlignment_(NSTextAlignmentCenter)
            except Exception:
                pass

            # Keep Change and Cancel positions unchanged (do not alter their X)
            try:
                if self.hotkey_button is not None:
                    hb_frame = self.hotkey_button.frame()
                    self.hotkey_button.setFrameOrigin_((hb_frame.origin.x, self._hotkey_button_y))
            except Exception:
                pass
            # Keep Launch checkbox horizontally aligned with the Hotkey title (not the dropdown)
            try:
                if self.launch_checkbox is not None and self.hotkey_label is not None:
                    lc_frame = self.launch_checkbox.frame()
                    hx = int(self.hotkey_label.frame().origin.x)
                    off = getattr(self, '_launch_x_offset', -20)
                    self.launch_checkbox.setFrameOrigin_((hx + off, lc_frame.origin.y))
            except Exception:
                pass

            # Align Save button's horizontal center with the hotkey box center
            try:
                if self.save_button is not None:
                    sb_frame = self.save_button.frame()
                    hv_center = hv_x + (hv_w / 2.0)
                    new_save_x = int(hv_center - (sb_frame.size.width / 2.0))
                    self.save_button.setFrameOrigin_((new_save_x, sb_frame.origin.y))
            except Exception:
                pass
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

    # -----------------------------
    # Icon helpers (no emoji)
    # -----------------------------
    def _create_symbol_image(self, symbol_name: str | None, point_size: float = 16.0):
        """Create an NSImage from SF Symbols when available.
        Returns None if the symbol or API isn't available.
        """
        if not symbol_name:
            return None
        try:
            # Lazily import to keep compatibility on older macOS/PyObjC
            from AppKit import NSImage
            try:
                # macOS 11+
                img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
            except Exception:
                img = None
            if img is None:
                return None
            try:
                # Prefer template so it tints with contentTintColor
                img.setTemplate_(True)
            except Exception:
                pass
            try:
                # Attempt to apply size configuration when available
                from AppKit import NSImageSymbolConfiguration
                conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(point_size, 0, 1)
                img = img.imageWithSymbolConfiguration_(conf)
            except Exception:
                # Fallback: set a nominal size
                try:
                    img.setSize_((point_size, point_size))
                except Exception:
                    pass
            return img
        except Exception:
            return None

    def _map_hint_to_symbol(self, control, hint: str | None) -> str | None:
        """Best-effort mapping from a control context or legacy emoji hint to an SF Symbol name."""
        # Prefer explicit hint if it already looks like a symbol name
        if hint and all(ch.islower() or ch.isdigit() or ch in {'.', '_'} for ch in hint):
            return hint
        # Control identity mapping
        try:
            if control is getattr(self, 'save_button', None):
                return 'checkmark.circle'
            if control is getattr(self, 'cancel_button', None):
                return 'xmark.circle'
            if control is getattr(self, 'hotkey_button', None):
                return 'pencil'
            if control is getattr(self, 'clear_cache_button', None):
                # Prefer broom if available, else trash
                return 'broom'
            if control is getattr(self, 'launch_checkbox', None):
                return 'arrow.triangle.2.circlepath'
        except Exception:
            pass
        # Legacy emoji hint mapping
        mapping = {
            '✔️': 'checkmark', '✅': 'checkmark',
            '✖️': 'xmark', '❌': 'xmark',
            '🧹': 'broom',
            '✏️': 'pencil',
            '💾': 'square.and.arrow.down',
            '🌐': 'globe',
            '🔄': 'arrow.triangle.2.circlepath',
            '⌨️': 'keyboard',
        }
        return mapping.get(hint or '', None)

    def _apply_button_tint(self, control):
        try:
            dark = bool(getattr(control, '_dark_style', False)) or self._is_dark()
            from AppKit import NSColor
            tint = NSColor.whiteColor() if dark else NSColor.labelColor()
            control.setContentTintColor_(tint)
            # Also tint any attached icon subview
            try:
                key = int(objc.pyobjc_id(control))
            except Exception:
                key = id(control)
            iv = self._button_icon_views.get(key)
            if iv is not None:
                try:
                    iv.setContentTintColor_(tint)
                except Exception:
                    pass
            # Tint overlay text label if present
            lbl = self._button_text_labels.get(key)
            if lbl is not None:
                try:
                    lbl.setTextColor_(tint)
                except Exception:
                    pass
        except Exception:
            pass

    def _set_control_title_with_icon(self, control, title: str, icon_hint: str | None = None, center_group: bool = True):
        """Use native NSButton image+title rendering so icon与文字同在按钮内显示且居中。
        兼容复选框：指示器在最左，图标紧随其后，再是文字。
        """
        # Remove any legacy overlays if存在，防止叠加
        try:
            key = int(objc.pyobjc_id(control))
        except Exception:
            key = id(control)
        try:
            iv = self._button_icon_views.pop(key, None)
            if iv is not None:
                iv.removeFromSuperview()
        except Exception:
            pass
        try:
            lbl = self._button_text_labels.pop(key, None)
            if lbl is not None:
                lbl.removeFromSuperview()
        except Exception:
            pass

        # Only proceed for NSButton-like controls
        try:
            from AppKit import NSButton
            if not isinstance(control, NSButton):
                return
        except Exception:
            return

        # Build symbol with fallbacks (e.g., broom -> trash)
        symbol = self._map_hint_to_symbol(control, icon_hint) or ''
        candidates = [symbol]
        if symbol == 'broom':
            candidates += ['trash', 'trash.circle']
        elif symbol in ('checkmark.circle', 'checkmark'):
            candidates += ['checkmark.circle']
        elif symbol in ('xmark.circle', 'xmark'):
            candidates += ['xmark.circle']
        img = None
        for name in filter(None, candidates):
            img = self._create_symbol_image(name, point_size=18.0)
            if img is not None:
                break

        # Set title first (完整标题，避免截断)
        try:
            control.setTitle_(title or '')
        except Exception:
            pass

        # Attach image if available
        try:
            if img is not None:
                control.setImage_(img)
                # 图标在左、文字在右
                control.setImagePosition_(NSImageLeft)
                try:
                    cell = control.cell()
                    if cell is not None:
                        cell.setImagePosition_(NSImageLeft)
                        # For normal buttons,缩短图文间距；复选框也用更紧凑的间距
                        try:
                            # Closer spacing
                            cell.setImageHugsTitle_(True)
                        except Exception:
                            pass
                except Exception:
                    pass
                # Add a tiny hair space for normal buttons only; checkbox不加，整体更靠左
                try:
                    base = control.title() or ''
                    # Strip any leading spaces we may have previously added
                    for lead in ("\u2009", "\u200a", " "):
                        if base.startswith(lead):
                            base = base[len(lead):]
                            break
                    add_space = True
                    try:
                        add_space = (control.buttonType() != NSSwitchButton)
                    except Exception:
                        add_space = True
                    if add_space:
                        thin = "\u2009"  # THIN SPACE (slightly larger than hair space)
                        control.setTitle_(thin + base)
                    else:
                        control.setTitle_(base)
                except Exception:
                    pass
        except Exception:
            pass

        # 让按钮整体居中布局由系统处理（image+title 作为一个整体）
        self._apply_button_tint(control)

    def _set_label_text_with_icon(self, label, text: str, icon_hint: str | None = None):
        """Attach a small image view to the left of a label without using emoji."""
        if not label:
            return
        try:
            label.setStringValue_(text or '')
        except Exception:
            pass
        try:
            frame = label.frame()
            size = 16
            margin = 6
            icon_x = int(frame.origin.x - size - margin)
            # Nudge upward a bit to visually align with text baseline
            icon_y = int(frame.origin.y + (frame.size.height - size) / 2) + 2

            # Pick or build image view holder for known labels
            iv_attr = None
            if label is getattr(self, 'lang_label', None):
                iv_attr = 'lang_icon_view'
            elif label is getattr(self, 'hotkey_label', None):
                iv_attr = 'hotkey_icon_view'
            # Get or create the image view
            iv = getattr(self, iv_attr, None) if iv_attr else None
            if iv is None:
                try:
                    iv = NSImageView.alloc().initWithFrame_(NSMakeRect(icon_x, icon_y, size, size))
                    iv.setImageScaling_(1)
                    iv.setWantsLayer_(True)
                    iv.layer().setCornerRadius_(3.0)
                    # Insert alongside the label into the same container (card)
                    (self.card or self.window.contentView()).addSubview_(iv)
                    try:
                        iv.setAutoresizingMask_(label.autoresizingMask())
                    except Exception:
                        pass
                    if iv_attr:
                        setattr(self, iv_attr, iv)
                except Exception:
                    return
            else:
                try:
                    iv.setFrame_(NSMakeRect(icon_x, icon_y, size, size))
                except Exception:
                    pass
            # Load and apply the symbol image
            symbol = icon_hint or self._map_hint_to_symbol(None, icon_hint)
            if not symbol:
                # Fallback mapping by label identity
                if label is getattr(self, 'lang_label', None):
                    symbol = 'globe'
                elif label is getattr(self, 'hotkey_label', None):
                    symbol = 'keyboard'
            img = self._create_symbol_image(symbol, point_size=15.0)
            if img is not None:
                try:
                    iv.setImage_(img)
                    # Tint to label color if possible
                    try:
                        iv.setContentTintColor_(label.textColor())
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

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
    NSImageOnly,
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
        # Switcher hotkey (cycle pages)
        self.switch_label = None
        self.switch_box = None
        self.switch_value = None
        self.switch_button = None
        # Small description labels under each hotkey box
        self.hotkey_desc_label = None
        self.switch_desc_label = None
        self.clear_cache_button = None
        # Suspend (sleep) time controls
        self.suspend_label = None
        self.suspend_popup = None
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
        # Removed: popup title overlays
        return self

    # Draw-only click-through view for dashed border (always visible above target)
    class _DashedBorderView(NSView):
        def isFlipped(self):
            return False
        def hitTest_(self, p):
            # Allow clicks to pass through to the control underneath
            return None
        def drawRect_(self, rect):
            try:
                from AppKit import NSBezierPath, NSColor, NSApp
                # Choose a high-contrast adaptive color for visibility
                try:
                    appearance = NSApp.effectiveAppearance()
                    name = appearance.bestMatchFromAppearancesWithNames_(["NSAppearanceNameDarkAqua", "NSAppearanceNameAqua"]) if appearance else None
                    is_dark = (name == "NSAppearanceNameDarkAqua")
                except Exception:
                    is_dark = False
                # Make border slightly darker for better contrast per request
                stroke_color = (NSColor.whiteColor().colorWithAlphaComponent_(0.80) if is_dark
                                else NSColor.blackColor().colorWithAlphaComponent_(0.65))
                bounds = self.bounds()
                path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 6.0, 6.0)
                dashes = (5.0, 3.0)
                path.setLineDash_count_phase_(dashes, 2, 0.0)
                stroke_color.set()
                path.setLineWidth_(1.6)
                path.stroke()
            except Exception:
                pass

    # Custom cell to center popup title inside the control (no overlays)
    class BBCenteredPopUpButtonCell(objc.lookUpClass('NSPopUpButtonCell')):
        def titleRectForBounds_(self, theRect):
            try:
                inset_l, inset_r, inset_v = 8.0, 24.0, 4.0
                return NSMakeRect(
                    theRect.origin.x + inset_l,
                    theRect.origin.y + inset_v,
                    max(0.0, theRect.size.width - inset_l - inset_r),
                    max(0.0, theRect.size.height - inset_v * 2),
                )
            except Exception:
                return theRect
        def drawTitle_withFrame_inView_(self, title, frame, view):
            try:
                from AppKit import NSFont, NSColor, NSFontAttributeName, NSForegroundColorAttributeName
                from Foundation import NSAttributedString
                try:
                    from AppKit import NSMutableParagraphStyle, NSTextAlignmentCenter, NSParagraphStyleAttributeName
                except Exception:
                    NSMutableParagraphStyle = None
                    NSTextAlignmentCenter = 2
                    NSParagraphStyleAttributeName = None
                # Determine the text to draw (selected item's title)
                try:
                    txt = self.titleOfSelectedItem()
                except Exception:
                    txt = None
                if not txt:
                    try:
                        txt = title.string()
                    except Exception:
                        txt = ""
                attrs = {NSFontAttributeName: NSFont.systemFontOfSize_(16)}
                try:
                    attrs[NSForegroundColorAttributeName] = NSColor.labelColor()
                except Exception:
                    pass
                try:
                    ps = NSMutableParagraphStyle.alloc().init()
                    ps.setAlignment_(NSTextAlignmentCenter)
                    if NSParagraphStyleAttributeName is not None:
                        attrs[NSParagraphStyleAttributeName] = ps
                except Exception:
                    pass
                s = NSAttributedString.alloc().initWithString_attributes_(txt or "", attrs)
                r = self.titleRectForBounds_(frame)
                s.drawInRect_(r)
                return r
            except Exception:
                return frame

    # Solid white rounded panel using drawRect_ (more reliable than layer-only on some systems)
    class _PlainPanelView(NSView):
        def isFlipped(self):
            return False
        def drawRect_(self, rect):
            try:
                from AppKit import NSBezierPath, NSColor
                bounds = self.bounds()
                path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 12.0, 12.0)
                NSColor.whiteColor().setFill()
                path.fill()
                # remove border per design (clean edge on white)
            except Exception:
                pass

    # Modal overlay that blocks clicks to underlying settings window
    class _ModalOverlay(NSView):
        def isFlipped(self):
            return False
        def acceptsFirstResponder(self):
            return True
        def acceptsFirstMouse_(self, event):
            return True
        def hitTest_(self, point):
            try:
                # Allow hits for subviews (dialog / buttons) but block others
                hit = objc.super(SettingsWindow._ModalOverlay, self).hitTest_(point)
                return hit if hit is not None else self
            except Exception:
                return self
        # Swallow mouse events outside dialog
        def mouseDown_(self, event):
            return None
        def mouseUp_(self, event):
            return None
        def mouseDragged_(self, event):
            return None

    class _XIconView(NSView):
        def isFlipped(self):
            return False
        def hitTest_(self, point):
            # Let clicks pass through to the underlying button
            return None
        def drawRect_(self, rect):
            try:
                from AppKit import NSBezierPath, NSColor
                NSColor.whiteColor().setStroke()
                path = NSBezierPath.bezierPath()
                # Thinner and slightly inset to look more delicate
                path.setLineWidth_(1.2)
                pad = 5.0
                w = rect.size.width; h = rect.size.height
                path.moveToPoint_((pad, pad))
                path.lineToPoint_((w - pad, h - pad))
                path.moveToPoint_((w - pad, pad))
                path.lineToPoint_((pad, h - pad))
                path.stroke()
            except Exception:
                pass

    def _add_dashed_border_around(self, target_view, radius=6.0):
        """Legacy: add dashed border as a subview of the control (kept for safety)."""
        try:
            bounds = target_view.bounds()
            border = SettingsWindow._DashedBorderView.alloc().initWithFrame_(bounds)
            border.setWantsLayer_(True)
            try:
                # Ensure it paints above the control content when layer-backed
                if hasattr(border, 'layer') and border.layer():
                    try:
                        border.layer().setZPosition_(999)
                    except Exception:
                        pass
                border.setAutoresizingMask_((1 << 1) | (1 << 4))  # width+height sizable
            except Exception:
                pass
            target_view.addSubview_(border)
        except Exception:
            pass

    def _add_dashed_border_overlay(self, target_view, radius=6.0):
        """Preferred: overlay a dashed-border view onto the target view's frame on its parent.

        This ensures the border is always visible, regardless of the control's own drawing.
        """
        try:
            parent = target_view.superview()
            if parent is None:
                # Fallback to legacy method if not yet attached
                return self._add_dashed_border_around(target_view, radius=radius)
            frame = target_view.frame()
            border = SettingsWindow._DashedBorderView.alloc().initWithFrame_(frame)
            border.setWantsLayer_(True)
            try:
                # Keep above target
                if hasattr(border, 'layer') and border.layer():
                    border.layer().setZPosition_(999)
                border.setAutoresizingMask_((1 << 1) | (1 << 4))  # width+height sizable
            except Exception:
                pass
            parent.addSubview_positioned_relativeTo_(border, 1, target_view)  # NSWindowAbove=1
        except Exception:
            pass

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

        def _apply_pointer_cursor(control):
            try:
                control.discardCursorRects()
                control.addCursorRect_cursor_(control.bounds(), NSCursor.pointingHandCursor())
            except Exception:
                pass

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
            # Move right by 4 from previous (+2 -> +6)
            NSMakeRect(content_center_x - lang_w / 2 + 6, language_center - 17, lang_w, 34), False
        )
        self.lang_popup.addItemWithTitle_("English")
        self.lang_popup.addItemWithTitle_("中文")
        self.lang_popup.addItemWithTitle_("日本語")
        self.lang_popup.addItemWithTitle_("한국어")
        self.lang_popup.addItemWithTitle_("Français")
        try:
            # Add dashed border around popup; remove native border/outline
            self.lang_popup.setWantsLayer_(True)
            self.lang_popup.setBordered_(False)
            try:
                self.lang_popup.setFocusRingType_(NSFocusRingTypeNone)
            except Exception:
                pass
            try:
                _cell_lang = self.lang_popup.cell()
                if _cell_lang is not None:
                    try:
                        _cell_lang.setBordered_(False)
                    except Exception:
                        pass
                    try:
                        _cell_lang.setBezelStyle_(0)
                    except Exception:
                        pass
            except Exception:
                pass
            self.lang_popup.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
            self.lang_popup.layer().setCornerRadius_(6.0)
            self.lang_popup.layer().setBorderWidth_(0.0)
            try:
                # Adjust font size per request
                self.lang_popup.setFont_(NSFont.systemFontOfSize_(17))
            except Exception:
                pass
            # Ensure default left alignment (revert)
            try:
                from AppKit import NSTextAlignmentLeft
                al = NSTextAlignmentLeft
            except Exception:
                al = 1
            try:
                cell = self.lang_popup.cell()
                if cell is not None:
                    cell.setAlignment_(al)
            except Exception:
                try:
                    self.lang_popup.setAlignment_(al)
                except Exception:
                    pass
        except Exception:
            pass
        self.card.addSubview_(self.lang_popup)
        # Add dashed border as a child of the popup (won't bleed across windows)
        try:
            self._add_dashed_border_around(self.lang_popup, radius=6.0)
        except Exception:
            pass
        # Ensure default NSPopUpButton cell (no custom centering)
        try:
            DefaultCell = objc.lookUpClass('NSPopUpButtonCell')
            if DefaultCell is not None:
                menu = self.lang_popup.menu()
                def_cell = DefaultCell.alloc().initTextCell_pullsDown_("", False)
                try:
                    def_cell.setBordered_(False)
                    def_cell.setBezelStyle_(0)
                except Exception:
                    pass
                self.lang_popup.setCell_(def_cell)
                if menu is not None:
                    self.lang_popup.setMenu_(menu)
                try:
                    self.lang_popup.setFont_(NSFont.systemFontOfSize_(17))
                except Exception:
                    pass
        except Exception:
            pass
        # Apply language immediately on selection
        try:
            self.lang_popup.setTarget_(self)
            self.lang_popup.setAction_("languageChanged:")
        except Exception:
            pass

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
        spacing_hotkey = 28  # legacy; see common_spacing below
        group_w = hv_w + spacing_hotkey + 112
        min_left = pad_x + 80 + 12
        hv_base = max(min_left, (card_bounds.size.width - group_w) / 2 + group_shift_x)
        # Store layout anchors for dynamic updates
        self._hotkey_group_base_x = hv_base
        self._hotkey_value_y = hotkey_center - 12
        self._hotkey_button_y = hotkey_center - 17
        self._hotkey_right_shift = 0  # value starts at group base; overall group stays centered
        self._hotkey_spacing = spacing_hotkey
        # Shift hotkey group further to the left per request
        self._hotkey_right_shift = -70
        # Align Hotkey and Sleep boxes to the same left edge
        align_base_x = pad_x + 140
        # Shift both boxes left by 62px total (32 + 10 + 20)
        hv_x_init = align_base_x - 62
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
        # Add switcher value box to the right of launcher box
        spacing_between_boxes = 22
        sw_x_init = hv_x_init + hv_w + spacing_between_boxes
        self.switch_box = NSView.alloc().initWithFrame_(NSMakeRect(sw_x_init, hotkey_center - box_h / 2 + self._hotkey_box_y_offset, hv_w, box_h))
        try:
            self.switch_box.setWantsLayer_(True)
            try:
                self.switch_box.layer().setCornerRadius_(box_h / 2.0)
            except Exception:
                self.switch_box.layer().setCornerRadius_(6.0)
            self.switch_box.layer().setBorderWidth_(1.0)
            self.switch_box.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
            dark = self._is_dark()
            border = (NSColor.whiteColor().colorWithAlphaComponent_(0.28) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.22))
            self.switch_box.layer().setBorderColor_(border.CGColor())
        except Exception:
            pass
        self.card.addSubview_(self.switch_box)
        # Inner switcher text
        self.switch_value = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, hv_w, box_h))
        self.switch_value.setBezeled_(False)
        self.switch_value.setDrawsBackground_(False)
        self.switch_value.setEditable_(False)
        self.switch_value.setSelectable_(False)
        try:
            self.switch_value.setAlignment_(NSTextAlignmentCenter)
            self.switch_value.setFont_(NSFont.systemFontOfSize_(16))
            self.switch_value.setTextColor_(NSColor.labelColor())
        except Exception:
            pass
        try:
            self.switch_box.addSubview_(self.switch_value)
        except Exception:
            pass

        # Place the Change button to the right of the second box
        # Increase spacing between second value box and Change button
        common_spacing = 88
        # Shift Change button left by 68px total (32 + 16 + 20)
        hotkey_button_x = sw_x_init + hv_w + (common_spacing - 68)
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

        # Clear cache row now also hosts "sleep time" controls on the left
        sleep_center = hotkey_center - row_gap

        # 3.1: Add "sleep time" label + value box + Change button (left side)
        # Label
        self.suspend_label = add_label(_t('settings.suspendTime', default='Sleep time'), pad_x + 50, sleep_center - 12, 120, 24)
        try:
            self._set_label_text_with_icon(self.suspend_label, _t('settings.suspendTime', default='Sleep time'), 'clock')
        except Exception:
            pass

        # Sleep time dropdown (like language popup)
        sp_w = 180
        sp_h = 34
        # Add a bit more distance from the label to the dropdown (move further right)
        sp_x = align_base_x + 36  # moved left by 4 as requested
        self.suspend_popup = BBPointerPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(sp_x, sleep_center - sp_h/2, sp_w, sp_h), False
        )
        try:
            self.suspend_popup.setWantsLayer_(True)
            self.suspend_popup.setBordered_(False)
            try:
                self.suspend_popup.setFocusRingType_(NSFocusRingTypeNone)
            except Exception:
                pass
            try:
                _cell_suspend = self.suspend_popup.cell()
                if _cell_suspend is not None:
                    try:
                        _cell_suspend.setBordered_(False)
                    except Exception:
                        pass
                    try:
                        _cell_suspend.setBezelStyle_(0)
                    except Exception:
                        pass
            except Exception:
                pass
            self.suspend_popup.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
            self.suspend_popup.layer().setCornerRadius_(6.0)
            self.suspend_popup.layer().setBorderWidth_(0.0)
            # Adjust font size per request
            self.suspend_popup.setFont_(NSFont.systemFontOfSize_(17))
            # Ensure default left alignment (revert)
            try:
                from AppKit import NSTextAlignmentLeft
                al2 = NSTextAlignmentLeft
            except Exception:
                al2 = 1
            try:
                cell = self.suspend_popup.cell()
                if cell is not None:
                    cell.setAlignment_(al2)
            except Exception:
                try:
                    self.suspend_popup.setAlignment_(al2)
                except Exception:
                    pass
        except Exception:
            pass
        # Add options: No sleep, 10, 20, 30, 60
        try:
            self.suspend_popup.removeAllItems()
        except Exception:
            pass
        self.suspend_popup.addItemWithTitle_(_t('settings.suspendOff', default='No sleep'))
        for m in (10, 20, 30, 60):
            if str(_get_lang()).startswith('zh'):
                self.suspend_popup.addItemWithTitle_(f"{m} 分钟")
            else:
                self.suspend_popup.addItemWithTitle_(f"{m} min")
        # Bind change handler (apply immediately)
        try:
            self.suspend_popup.setTarget_(self)
            self.suspend_popup.setAction_("suspendChanged:")
        except Exception:
            pass
        self.card.addSubview_(self.suspend_popup)
        # Add dashed border as a child of the popup (won't bleed across windows)
        try:
            self._add_dashed_border_around(self.suspend_popup, radius=6.0)
        except Exception:
            pass
        # Ensure default NSPopUpButtonCell (no custom centering)
        try:
            DefaultCell = objc.lookUpClass('NSPopUpButtonCell')
            if DefaultCell is not None:
                menu2 = self.suspend_popup.menu()
                def_cell2 = DefaultCell.alloc().initTextCell_pullsDown_("", False)
                try:
                    def_cell2.setBordered_(False)
                    def_cell2.setBezelStyle_(0)
                except Exception:
                    pass
                self.suspend_popup.setCell_(def_cell2)
                if menu2 is not None:
                    self.suspend_popup.setMenu_(menu2)
                try:
                    self.suspend_popup.setFont_(NSFont.systemFontOfSize_(17))
                except Exception:
                    pass
        except Exception:
            pass

        # Clear cache button and Launch at login on the same row
        cc_w, cc_h = 146, 34
        # Move a bit further to the left from the right margin (additional -40)
        cc_x = card_bounds.size.width - cc_w - pad_x - 166
        # Footer row near bottom (slightly above bottom edge) — move up by 15
        footer_center = 55
        cc_y = footer_center - cc_h / 2.0
        self.clear_cache_button = add_button(_t('settings.clearCache'), cc_x, cc_y, cc_w, cc_h)
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

        # Remove Save button (apply-on-select behavior)
        self.save_button = None
        # Remove Cancel button per request; add a circular close icon at top-left instead
        try:
            cb = self.card.bounds()
            size = 28
            cx = 12
            cy = int(cb.size.height - size - 12)
            self.close_button = VercelButton.alloc().initWithFrame_(NSMakeRect(cx, cy, size, size))
            try:
                self.close_button.setStyleDark_(True)
                self.close_button.setWantsLayer_(True)
                self.close_button.layer().setCornerRadius_(size/2.0)
                # Add a thin ring
                self.close_button.layer().setBorderWidth_(1.0)
                dark = self._is_dark()
                ring = (NSColor.whiteColor().colorWithAlphaComponent_(0.22) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.18))
                self.close_button.layer().setBorderColor_(ring.CGColor())
            except Exception:
                pass
            # Pure icon (xmark) centered — use helper and force white tint
            try:
                from AppKit import NSColor
                img = self._create_symbol_image('xmark', point_size=14.0, color=NSColor.whiteColor())
                if img:
                    self.close_button.setImage_(img)
                    self.close_button.setImagePosition_(NSImageOnly)
                    try:
                        self.close_button.setContentTintColor_(NSColor.whiteColor())
                    except Exception:
                        pass
                    try:
                        self._apply_button_tint(self.close_button)
                    except Exception:
                        pass
                    try:
                        self.close_button.setTitle_("")
                    except Exception:
                        pass
            except Exception:
                pass
            # Pointer cursor on settings close button as well
            try:
                _apply_pointer_cursor(self.close_button)
            except Exception:
                pass
            self.close_button.setTarget_(self)
            self.close_button.setAction_("closeSettings:")
            self.card.addSubview_(self.close_button)
        except Exception:
            pass
        # Position Launch at login checkbox on the same row (left side)
        try:
            self.launch_checkbox.setTitle_(_t('settings.launchAtLogin'))
            try:
                hx = int(self.hotkey_label.frame().origin.x)
            except Exception:
                hx = pad_x + 50
            self.launch_checkbox.setFrameOrigin_((hx + getattr(self, '_launch_x_offset', -20), int(footer_center - 12)))
            try:
                if self.launch_label is not None:
                    self.launch_label.setHidden_(True)
            except Exception:
                pass
        except Exception:
            pass

        # Freeze save button position so later layout updates won't move it
        self._freeze_save_pos = True
        self._load_values_into_ui()

        # After initial values are loaded, update hotkey layout to fit content
        try:
            self._update_hotkey_group_layout()
        except Exception:
            pass
        # No overlay layout sync needed
        # Add small description labels under each box
        try:
            desc_h = 16
            # Move descriptions up by 24px from previous baseline (net +16 from original)
            desc_y = int(self._hotkey_value_y - box_h / 2 - 4 - desc_h + 16)
            # Launcher description
            self.hotkey_desc_label = add_label(_t('hotkey.desc.launcher', default='Show/Hide'), hv_x_init, desc_y, hv_w, desc_h)
            try:
                self.hotkey_desc_label.setAlignment_(NSTextAlignmentCenter)
                self.hotkey_desc_label.setTextColor_(NSColor.secondaryLabelColor())
                self.hotkey_desc_label.setFont_(NSFont.systemFontOfSize_(12))
            except Exception:
                pass
            # Switcher description
            self.switch_desc_label = add_label(_t('hotkey.desc.switcher', default='Switch windows'), sw_x_init, desc_y, hv_w, desc_h)
            try:
                self.switch_desc_label.setAlignment_(NSTextAlignmentCenter)
                self.switch_desc_label.setTextColor_(NSColor.secondaryLabelColor())
                self.switch_desc_label.setFont_(NSFont.systemFontOfSize_(12))
            except Exception:
                pass
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
        # No overlay sync needed
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
        # Switcher hotkey (hint only)
        try:
            fmt2 = getattr(self.app_delegate, '_format_switcher_hotkey', None)
            if callable(fmt2) and self.switch_value is not None:
                self.switch_value.setStringValue_(fmt2())
        except Exception:
            pass
        # Suspend minutes
        try:
            self._refresh_suspend_value()
        except Exception:
            pass
        # No overlay sync needed

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
        if self.switch_label:
            try:
                self._set_label_text_with_icon(self.switch_label, _t('settings.hotkeySwitch', default='Switch Windows'), 'arrow.triangle.2.circlepath')
            except Exception:
                try:
                    self.switch_label.setStringValue_(_t('settings.hotkeySwitch', default='Switch Windows'))
                except Exception:
                    pass
        # Small descriptions under the value boxes
        try:
            if self.hotkey_desc_label is not None:
                self.hotkey_desc_label.setStringValue_(_t('hotkey.desc.launcher', default='Show/Hide'))
            if self.switch_desc_label is not None:
                self.switch_desc_label.setStringValue_(_t('hotkey.desc.switcher', default='Switch windows'))
        except Exception:
            pass
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
        if self.switch_button:
            try:
                self.switch_button.setStyleDark_(True)
            except Exception:
                pass
            try:
                self._set_control_title_with_icon(self.switch_button, _t('button.change'), 'pencil')
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
        # No Save button (apply on select)
        # No cancel button anymore
        if self.header_title_label:
            self.header_title_label.setStringValue_(_t('settings.title'))
        # Update header logo for current appearance
        try:
            if self.header_logo_view is not None:
                self.header_logo_view.setImage_(self._load_logo_for_appearance())
        except Exception:
            pass
        # Refresh suspend popup item titles to current language
        try:
            self._refresh_suspend_popup_titles()
        except Exception:
            pass
        # Also refresh the centered overlays to reflect new localized titles
        # No overlay sync needed

    def _install_button_hover_effect(self, btn):
        try:
            # Install a tracking area for hover events; animate background alpha
            class _HoverProxy(objc.lookUpClass('NSObject')):
                def initWithBtn_(self, b):
                    self = objc.super(_HoverProxy, self).init()
                    if self is None:
                        return None
                    self._b = b
                    return self
                def mouseEntered_(self, _e):
                    try:
                        if btn.layer():
                            btn.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.16).CGColor())
                    except Exception:
                        pass
                def mouseExited_(self, _e):
                    try:
                        if btn.layer():
                            btn.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).CGColor())
                    except Exception:
                        pass
            area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                btn.bounds(), NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect, _HoverProxy.alloc().initWithBtn_(btn), None
            )
            btn.addTrackingArea_(area)
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

    # --- Hotkey mode picker actions ---
    def closeHotkeyPicker_(self, _):
        try:
            ov = getattr(self, '_hotkey_mode_overlay', None)
            if ov is None:
                return
            if os.environ.get('BB_NO_EFFECTS') != '1':
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.16)
                ov.animator().setAlphaValue_(0.0)
                NSAnimationContext.endGrouping()
            # Re-enable any disabled controls
            try:
                disabled = getattr(ov, '_bb_disabled_controls', None)
                if disabled:
                    for c in disabled:
                        try:
                            c.setEnabled_(True)
                        except Exception:
                            pass
            except Exception:
                pass
            # Restore dashed helper overlays hidden during modal display
            try:
                hidden = getattr(ov, '_bb_hidden_dashed', None)
                if hidden:
                    for v in hidden:
                        try:
                            v.setHidden_(False)
                        except Exception:
                            pass
            except Exception:
                pass
            ov.removeFromSuperview()
            setattr(self, '_hotkey_mode_overlay', None)
        except Exception:
            pass

    def _after_hotkey_change(self):
        # Refresh both displays shortly after capture panel closes
        try:
            from Foundation import NSTimer
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.2, self, 'refreshHotkey:', None, False
            )
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.2, self, 'refreshSwitcherHotkey:', None, False
            )
        except Exception:
            try:
                self.refreshHotkey_(None)
                self.refreshSwitcherHotkey_(None)
            except Exception:
                pass

    def chooseHotkeyLauncher_(self, _):
        try:
            set_custom_launcher_trigger(self.app_delegate, target_window=self.window, mode='launcher')
        except Exception:
            pass
        self.closeHotkeyPicker_(None)
        self._after_hotkey_change()

    def chooseHotkeySwitcher_(self, _):
        try:
            set_custom_launcher_trigger(self.app_delegate, target_window=self.window, mode='switcher')
        except Exception:
            pass
        self.closeHotkeyPicker_(None)
        self._after_hotkey_change()


    def closeSettings_(self, _sender):
        self._dismiss(animated=True)

    # Actions
    def saveSettings_(self, sender):
        # Save no longer needed for language; keep for future extensibility
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

    def languageChanged_(self, sender):
        # Apply language immediately on selection
        try:
            idx = int(self.lang_popup.indexOfSelectedItem()) if self.lang_popup else 0
        except Exception:
            idx = 0
        order = ["en", "zh", "ja", "ko", "fr"]
        new_lang = order[idx] if idx < len(order) else "en"
        try:
            ConfigManager.set_language(new_lang)
            if hasattr(self.app_delegate, 'changeLanguage_'):
                self.app_delegate.changeLanguage_(new_lang)
        except Exception:
            pass
        # Also refresh suspend popup titles immediately
        try:
            self._refresh_suspend_popup_titles()
        except Exception:
            pass

    def _refresh_suspend_popup_titles(self):
        if not self.suspend_popup:
            return
        # Preserve current selection as minutes
        try:
            idx = int(self.suspend_popup.indexOfSelectedItem())
        except Exception:
            idx = 3
        mapping = {0: 0, 1: 10, 2: 20, 3: 30, 4: 60}
        minutes = mapping.get(idx, 30)
        try:
            self.suspend_popup.removeAllItems()
        except Exception:
            pass
        # Rebuild titles in current language
        try:
            self.suspend_popup.addItemWithTitle_(_t('settings.suspendOff', default='No sleep'))
            for m in (10, 20, 30, 60):
                if str(_get_lang()).startswith('zh'):
                    self.suspend_popup.addItemWithTitle_(f"{m} 分钟")
                else:
                    self.suspend_popup.addItemWithTitle_(f"{m} min")
        except Exception:
            pass
        # Restore selection
        try:
            rev = {0: 0, 10: 1, 20: 2, 30: 3, 60: 4}
            sel = rev.get(minutes, 3)
            self.suspend_popup.selectItemAtIndex_(sel)
        except Exception:
            pass
        # No overlay sync needed

    def cancelSettings_(self, sender):
        self._dismiss(animated=True)

    def clearCache_(self, sender):
        # Present a custom Vercel-style confirmation overlay
        try:
            self._present_clear_cache_confirm()
        except Exception:
            # Fallback: perform clear directly if overlay failed to present
            self._perform_clear_cache()

    # Suspend (sleep) time change
    def changeSuspendTime_(self, sender):
        try:
            self._present_suspend_time_picker()
        except Exception:
            # Fallback: cycle through presets 10/20/30/60/Off
            cur = self._get_suspend_minutes()
            for m in (10, 20, 30, 60, 0):
                if m > cur:
                    self._apply_suspend_minutes(m)
                    break
            else:
                self._apply_suspend_minutes(0)

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
        # Attach modal overlay to the window's contentView so it's above the card
        container = self.window.contentView()
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
        # Make overlay first responder to ensure it receives key/mouse
        try:
            (self.window or NSApp().keyWindow()).makeFirstResponder_(overlay)
        except Exception:
            pass

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

    # ----- Suspend time helpers -----
    def _get_suspend_minutes(self) -> int:
        # Default to 30 if missing
        try:
            cfg = ConfigManager.load()
            val = cfg.get('suspend', {}).get('minutes', 30)
            v = int(val)
            return v if v >= 0 else 30
        except Exception:
            return 30

    def _format_suspend_minutes(self, minutes: int) -> str:
        try:
            lang = _get_lang()
        except Exception:
            lang = 'en'
        try:
            m = int(minutes)
        except Exception:
            m = 30
        # Disabled (no sleep)
        if m <= 0:
            try:
                label = _t('settings.suspendOff')
                if label and label != 'settings.suspendOff':
                    return label
            except Exception:
                pass
            if isinstance(lang, str) and lang.startswith('zh'):
                return "不休眠"
            if isinstance(lang, str) and lang.startswith('ja'):
                return "スリープしない"
            if isinstance(lang, str) and lang.startswith('ko'):
                return "절전 안 함"
            if isinstance(lang, str) and lang.startswith('fr'):
                return "Pas de veille"
            return "No sleep"
        if isinstance(lang, str) and lang.startswith('zh'):
            return f"{m} 分钟"
        return f"{m} min"

    def _refresh_suspend_value(self):
        # Update popup selection to current minutes
        try:
            minutes = int(self._get_suspend_minutes())
        except Exception:
            minutes = 30
        try:
            # Items: [No sleep(0), 10, 20, 30, 60]
            mapping = {0: 0, 10: 1, 20: 2, 30: 3, 60: 4}
            idx = mapping.get(minutes, 3)
            if self.suspend_popup is not None:
                self.suspend_popup.selectItemAtIndex_(idx)
        except Exception:
            pass
        # No overlay sync needed

    def _apply_suspend_minutes(self, minutes: int):
        # Persist
        try:
            cfg = ConfigManager.load()
            suspend = cfg.get('suspend') or {}
            suspend['minutes'] = int(minutes)
            cfg['suspend'] = suspend
            ConfigManager.save(cfg)
        except Exception:
            pass
        # Notify manager if available
        try:
            mw = getattr(self.app_delegate, 'multiwindow_manager', None)
            if mw and hasattr(mw, 'update_suspend_timeout'):
                mw.update_suspend_timeout(int(minutes))
        except Exception:
            pass
        # Refresh UI and toast
        try:
            self._refresh_suspend_value()
            self._show_toast(_t('settings.suspendTimeUpdated', default='Sleep time updated'))
        except Exception:
            pass

    def suspendChanged_(self, sender):
        # Map selection to minutes and apply immediately
        try:
            idx = int(self.suspend_popup.indexOfSelectedItem()) if self.suspend_popup else 3
        except Exception:
            idx = 3
        mapping = {0: 0, 1: 10, 2: 20, 3: 30, 4: 60}
        minutes = mapping.get(idx, 30)
        self._apply_suspend_minutes(minutes)
        # No overlay sync needed

    # (removed) overlay helpers

    def _present_suspend_time_picker(self):
        # Simple inline overlay with four presets and a cancel
        container = self.card if hasattr(self, 'card') and self.card else self.window.contentView()
        if not container:
            return
        cb = container.bounds()
        overlay = NSView.alloc().initWithFrame_(cb)
        overlay.setWantsLayer_(True)
        try:
            # Keep the overlay itself transparent; the dialog will be solid white
            overlay.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        except Exception:
            pass
        # Vertical list dialog whose height grows with the number of options
        opts = []
        try:
            off_label = _t('settings.suspendOff', default='No sleep')
        except Exception:
            off_label = 'No sleep'
        opts = [(off_label, 0), ("10", 10), ("20", 20), ("30", 30), ("60", 60)]
        btn_h, btn_w, btn_gap = 28, 120, 10
        top_pad, bottom_pad, title_h = 44, 18, 22
        # Dialog width leaves room on the right; keep compact
        w = 360
        # Compute height to fit all buttons vertically without folding
        h = top_pad + title_h + len(opts) * btn_h + (len(opts) - 1) * btn_gap + bottom_pad
        dialog = NSView.alloc().initWithFrame_(NSMakeRect((cb.size.width - w)/2, (cb.size.height - h)/2, w, h))
        dialog.setWantsLayer_(True)
        try:
            dialog.layer().setCornerRadius_(12.0)
            dialog.layer().setBackgroundColor_(NSColor.windowBackgroundColor().colorWithAlphaComponent_(0.96).CGColor())
        except Exception:
            pass

        title = NSTextField.alloc().initWithFrame_(NSMakeRect(16, h - (top_pad + title_h - 2), w - 32, 22))
        title.setBezeled_(False); title.setDrawsBackground_(False); title.setEditable_(False); title.setSelectable_(False)
        try:
            title.setAlignment_(1)  # left
            title.setFont_(NSFont.boldSystemFontOfSize_(15))
            title.setTextColor_(NSColor.labelColor())
        except Exception:
            pass
        title.setStringValue_(_t('settings.suspendTime', default='Sleep time'))
        dialog.addSubview_(title)

        def _add_opt(text, val, y):
            btn = NSButton.alloc().initWithFrame_(NSMakeRect(16, y, btn_w, btn_h))
            btn.setTitle_(text)
            btn.setBordered_(True)
            def _cb(_):
                try:
                    self._apply_suspend_minutes(val)
                finally:
                    try:
                        overlay.removeFromSuperview()
                    except Exception:
                        pass
            # Bind via small proxy
            Proxy = objc.lookUpClass('NSObject')
            class _Act(Proxy):
                def initWithHandler_(self, h):
                    self = objc.super(_Act, self).init()
                    if self is None:
                        return None
                    self._h = h
                    return self
                def callWithSender_(self, s):
                    try:
                        self._h(s)
                    except Exception:
                        pass
            p = _Act.alloc().initWithHandler_(_cb)
            btn.setTarget_(p); btn.setAction_("callWithSender:")
            dialog.addSubview_(btn)
            return btn, p

        # Layout options
        # Stack options vertically from top to bottom
        proxies = []
        start_y = h - (top_pad + title_h + btn_h)
        for idx, (label, minutes_val) in enumerate(opts):
            y = start_y - idx * (btn_h + btn_gap)
            _, proxy = _add_opt(label, minutes_val, y)
            proxies.append(proxy)
        overlay._bb_proxy_keep = tuple(proxies)

        dialog.addSubview_(title)
        overlay.addSubview_(dialog)
        overlay.setAlphaValue_(0.0)
        container.addSubview_(overlay)
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

    def changeHotkey_(self, sender):
        # Present a small choice to update Show/Hide or Switch Pages
        try:
            self._present_hotkey_mode_picker()
        except Exception:
            # Fallback: directly open launcher shortcut
            try:
                set_custom_launcher_trigger(self.app_delegate, target_window=self.window)
            except Exception:
                pass

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

    # Switcher change handled via _present_hotkey_mode_picker

    def refreshSwitcherHotkey_(self, _):
        try:
            fmt = getattr(self.app_delegate, '_format_switcher_hotkey', None)
            if callable(fmt) and self.switch_value is not None:
                self.switch_value.setStringValue_(fmt())
                try:
                    self._update_hotkey_group_layout()
                except Exception:
                    pass
        except Exception:
            pass

    def _present_hotkey_mode_picker(self):
        container = self.card if hasattr(self, 'card') and self.card else self.window.contentView()
        if not container:
            return
        cb = container.bounds()
        overlay = SettingsWindow._ModalOverlay.alloc().initWithFrame_(cb)
        overlay.setWantsLayer_(True)
        try:
            overlay.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.28).CGColor())
        except Exception:
            pass
        try:
            # Ensure overlay always covers container during resizes
            overlay.setAutoresizingMask_((1 << 1) | (1 << 4))  # width + height sizable
        except Exception:
            pass
        # Dialog
        w, h = 400, 180
        dlg_frame = NSMakeRect((cb.size.width - w)/2, (cb.size.height - h)/2, w, h)
        # Opaque white occluder behind dialog to ensure nothing bleeds through
        plate = NSView.alloc().initWithFrame_(dlg_frame)
        try:
            plate.setWantsLayer_(True)
            plate.layer().setCornerRadius_(12.0)
            plate.layer().setMasksToBounds_(True)
            plate.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
        except Exception:
            pass
        dialog = self._PlainPanelView.alloc().initWithFrame_(dlg_frame)
        try:
            dialog.setWantsLayer_(True)
            # Keep shadow on dialog; plate provides the fully opaque white background
            dialog.layer().setShadowOpacity_(0.20)
            dialog.layer().setShadowRadius_(10.0)
            dialog.layer().setShadowOffset_((0.0, -1.0))
        except Exception:
            pass
        # Centered title (we will later inset left/right equally to avoid overlap with the close button)
        # Increase height and size for better visual hierarchy
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - 48, w, 30))
        title.setBezeled_(False); title.setDrawsBackground_(False); title.setEditable_(False); title.setSelectable_(False)
        title.setStringValue_(_t('hotkey.overlay.title', default='Set Shortcut'))
        try:
            # Try a nicer, larger system font; fall back to bold
            try:
                # Prefer semibold if available
                title.setFont_(getattr(NSFont, 'systemFontOfSize_weight_', NSFont.boldSystemFontOfSize_)(20, 1))
            except Exception:
                try:
                    # Prefer PingFang SC Semibold for Chinese if present
                    pf = NSFont.fontWithName_size_("PingFangSC-Semibold", 20)
                    if pf:
                        title.setFont_(pf)
                    else:
                        title.setFont_(NSFont.boldSystemFontOfSize_(20))
                except Exception:
                    title.setFont_(NSFont.boldSystemFontOfSize_(20))
            title.setTextColor_(NSColor.labelColor())
            title.setAlignment_(NSTextAlignmentCenter)
            try:
                cell = title.cell()
                if cell:
                    cell.setAlignment_(NSTextAlignmentCenter)
            except Exception:
                pass
        except Exception:
            pass
        # Button style helper
        def style_choice_button(b):
            try:
                b.setBezelStyle_(NSBezelStyleRounded)
                b.setBordered_(False)
            except Exception:
                pass
            try:
                b.setWantsLayer_(True)
                b.layer().setCornerRadius_(10.0)
                b.layer().setMasksToBounds_(True)
                base = NSColor.controlAccentColor().colorWithAlphaComponent_(0.18)
                hover = NSColor.controlAccentColor().colorWithAlphaComponent_(0.26)
                b.layer().setBackgroundColor_(base.CGColor())
                class _Hover(objc.lookUpClass('NSObject')):
                    def initWithBtn_(self, btn):
                        self = objc.super(_Hover, self).init()
                        if self is None:
                            return None
                        self._btn = btn
                        return self
                    def mouseEntered_(self, _e):
                        try:
                            self._btn.layer().setBackgroundColor_(hover.CGColor())
                        except Exception:
                            pass
                    def mouseExited_(self, _e):
                        try:
                            self._btn.layer().setBackgroundColor_(base.CGColor())
                        except Exception:
                            pass
                ta = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                    b.bounds(), NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect, _Hover.alloc().initWithBtn_(b), None
                )
                b.addTrackingArea_(ta)
            except Exception:
                pass
            try:
                b.setFont_(NSFont.systemFontOfSize_(15))
            except Exception:
                pass
            return b

        btn_w, btn_h = 148, 38
        spacing = 12
        y = 48
        # Use dark vercel-style buttons with press effect; offset slightly right to create inner left padding
        # Move right: launcher +12
        btn1 = VercelButton.alloc().initWithFrame_(NSMakeRect(16 + 8 + 12, y, btn_w, btn_h))
        btn1.setStyleDark_(True)
        # Move right: switcher +36
        btn2 = VercelButton.alloc().initWithFrame_(NSMakeRect(16 + btn_w + spacing + 8 + 36, y, btn_w, btn_h))
        btn2.setStyleDark_(True)
        # Attach white-tinted SF Symbols + title via helper (ensures visibility)
        try:
            self._set_control_title_with_icon(btn1, _t('hotkey.overlay.launcher', default='Show/Hide Bubble'), 'bolt.circle')
        except Exception:
            try:
                btn1.setTitle_(_t('hotkey.overlay.launcher', default='Show/Hide Bubble'))
            except Exception:
                pass
        try:
            self._set_control_title_with_icon(btn2, _t('hotkey.overlay.switcher', default='Switch Windows'), 'arrow.triangle.2.circlepath')
        except Exception:
            try:
                btn2.setTitle_(_t('hotkey.overlay.switcher', default='Switch Windows'))
            except Exception:
                pass
        # Ensure icon is bright on dark buttons
        try:
            btn1.setContentTintColor_(NSColor.whiteColor())
            btn2.setContentTintColor_(NSColor.whiteColor())
        except Exception:
            pass
        # Close button (top-left) — match settings page style
        close_size = 28
        close_btn = VercelButton.alloc().initWithFrame_(NSMakeRect(12, h - 12 - close_size, close_size, close_size))
        try:
            close_btn.setStyleDark_(True)
            close_btn.setWantsLayer_(True)
            close_btn.layer().setCornerRadius_(close_size/2.0)
            # Add a subtle ring
            close_btn.layer().setBorderWidth_(1.0)
            dark = self._is_dark()
            ring = (NSColor.whiteColor().colorWithAlphaComponent_(0.22) if dark else NSColor.blackColor().colorWithAlphaComponent_(0.18))
            close_btn.layer().setBorderColor_(ring.CGColor())
            # Clear title before any image logic (avoid default localized title)
            try:
                close_btn.setTitle_("")
            except Exception:
                pass
            # Use helper to create templated symbol and force white tint
            from AppKit import NSColor
            # Force a crisp drawn white X at 12pt for reliability on macOS 15.6
            imgx = self._create_cross_image(12.0)
            if imgx:
                close_btn.setImage_(imgx)
            try:
                close_btn.setImagePosition_(NSImageOnly)
            except Exception:
                close_btn.setImagePosition_(1)
            # Ensure proportional image scaling so the X stays crisp
            try:
                cell = close_btn.cell()
                if cell and hasattr(cell, 'setImageScaling_'):
                    cell.setImageScaling_(NSImageScaleProportionallyUpOrDown)
            except Exception:
                pass
            try:
                close_btn.setContentTintColor_(NSColor.whiteColor())
                # Match settings page behavior: also apply our tint helper
                self._apply_button_tint(close_btn)
            except Exception:
                pass
        except Exception:
            pass
        # Final enforcement in case any earlier step raised and skipped clearing
        try:
            close_btn.setBordered_(False)
            close_btn.setTitle_("")
            try:
                close_btn.setImagePosition_(NSImageOnly)
            except Exception:
                close_btn.setImagePosition_(1)
        except Exception:
            pass
        # No extra overlay to keep icon light and small

        # Targets: use SettingsWindow self for reliability
        self._hotkey_mode_overlay = overlay
        try:
            btn1.setTarget_(self); btn1.setAction_("chooseHotkeyLauncher:")
            btn2.setTarget_(self); btn2.setAction_("chooseHotkeySwitcher:")
            close_btn.setTarget_(self); close_btn.setAction_("closeHotkeyPicker:")
        except Exception:
            pass
        # Apply pointer cursor to dialog buttons
        try:
            _apply_pointer_cursor(btn1)
            _apply_pointer_cursor(btn2)
            _apply_pointer_cursor(close_btn)
        except Exception:
            pass
        # Adjust title frame to avoid overlap with close button and remain visually centered
        try:
            # Margin equals left padding + button width + extra gap;
            # apply symmetrically on both sides to keep true center
            margin = int(close_btn.frame().origin.x + close_btn.frame().size.width + 8)
            title.setFrame_(NSMakeRect(margin, title.frame().origin.y, max(10, w - 2*margin), title.frame().size.height))
            try:
                title.setAlignment_(NSTextAlignmentCenter)
                cell = title.cell()
                if cell:
                    cell.setAlignment_(NSTextAlignmentCenter)
            except Exception:
                pass
        except Exception:
            pass
        dialog.addSubview_(title); dialog.addSubview_(btn1); dialog.addSubview_(btn2); dialog.addSubview_(close_btn)
        # Ensure overlay sits on top of existing content
        overlay.addSubview_(plate)
        overlay.addSubview_(dialog)
        overlay.setAlphaValue_(0.0)
        try:
            if hasattr(container, 'addSubview_positioned_relativeTo_'):
                from AppKit import NSWindowAbove
                subs = list(container.subviews())
                anchor = subs[-1] if subs else None
                container.addSubview_positioned_relativeTo_(overlay, NSWindowAbove, anchor)
            else:
                container.addSubview_(overlay)
        except Exception:
            container.addSubview_(overlay)
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

        # Make overlay first responder to ensure it receives key/mouse
        try:
            (self.window or NSApp().keyWindow()).makeFirstResponder_(overlay)
        except Exception:
            pass

        # Hide any dashed border helper views in underlying UI to avoid visual bleed-through
        try:
            hidden = []
            def _walk_hide(v):
                try:
                    for sv in list(getattr(v, 'subviews', lambda: [])() or []):
                        try:
                            if isinstance(sv, SettingsWindow._DashedBorderView):
                                if hasattr(sv, 'isHidden') and not sv.isHidden():
                                    sv.setHidden_(True)
                                    hidden.append(sv)
                        except Exception:
                            pass
                        _walk_hide(sv)
                except Exception:
                    pass
            _walk_hide(self.window.contentView())
            overlay._bb_hidden_dashed = tuple(hidden)
        except Exception:
            pass

        # Disable interactive controls underneath to prevent any chance of click-through
        try:
            disabled = []
            from AppKit import NSControl
            def _walk_and_disable(v):
                try:
                    if v is dialog or v is overlay:
                        return
                except Exception:
                    pass
                try:
                    # Disable NSControl instances (buttons, popups, etc.)
                    if isinstance(v, NSControl):
                        try:
                            if hasattr(v, 'isEnabled') and v.isEnabled():
                                v.setEnabled_(False)
                                disabled.append(v)
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    for sv in list(getattr(v, 'subviews', lambda: [])() or []):
                        _walk_and_disable(sv)
                except Exception:
                    pass
            for sv in list(container.subviews()) if hasattr(container, 'subviews') else []:
                _walk_and_disable(sv)
            overlay._bb_disabled_controls = tuple(disabled)
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
            # Move box right by 10 from current (+12 -> +22)
            try:
                # Shift both boxes left by 62px total
                hv_x = int(self.lang_popup.frame().origin.x) + 22 - 62
            except Exception:
                hv_x = save_x + 20 - 62
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

            # Position switcher box next to launcher box
            try:
                spacing_between_boxes = 22
                sw_x = hv_x + hv_w + spacing_between_boxes
                sw_y = hv_y
                if self.switch_box is not None:
                    self.switch_box.setFrame_(NSMakeRect(sw_x, sw_y, hv_w, box_h))
                    try:
                        self.switch_box.layer().setCornerRadius_(box_h / 2.0)
                    except Exception:
                        pass
                if self.switch_value is not None:
                    self.switch_value.setFrame_(NSMakeRect(0, lbl_y, hv_w, lbl_h))
            except Exception:
                pass
            # Reposition Change button to the right of second box
            try:
                if self.hotkey_button is not None:
                    # Shift Change button left by 68px total (32 + 16 + 20)
                    hb_x = sw_x + hv_w + (88 - 68)
                    self.hotkey_button.setFrameOrigin_((hb_x, self._hotkey_button_y))
            except Exception:
                pass
            # Update description labels positions under boxes
            try:
                desc_h = 16
                # Move descriptions up by 24px from previous baseline (net +16 from original)
                desc_y = int(self._hotkey_value_y - box_h / 2 - 4 - desc_h + 16)
                if self.hotkey_desc_label is not None:
                    self.hotkey_desc_label.setFrame_(NSMakeRect(hv_x, desc_y, hv_w, desc_h))
                if self.switch_desc_label is not None:
                    self.switch_desc_label.setFrame_(NSMakeRect(sw_x, desc_y, hv_w, desc_h))
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

            # Keep save button where we positioned it (do not auto-center)
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
                    data = pkgutil.get_data('bubble', rel)
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
            data = pkgutil.get_data('bubble', rel_path)
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
        # No overlay layout sync needed

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
            lbl.setStringValue_(str(message) if message is not None else "")
            toast.addSubview_(lbl)

            # Start hidden and fade in/out
            toast.setAlphaValue_(0.0)
            try:
                subs = list(content.subviews())
                anchor = subs[-1] if subs else None
                if hasattr(content, 'addSubview_positioned_relativeTo_'):
                    content.addSubview_positioned_relativeTo_(toast, NSWindowAbove, anchor)
                else:
                    content.addSubview_(toast)
            except Exception:
                content.addSubview_(toast)
            try:
                if os.environ.get('BB_NO_EFFECTS') != '1':
                    NSAnimationContext.beginGrouping()
                    NSAnimationContext.currentContext().setDuration_(0.18)
                    toast.animator().setAlphaValue_(1.0)
                    NSAnimationContext.endGrouping()
                else:
                    toast.setAlphaValue_(1.0)
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
    def _create_symbol_image(self, symbol_name: str | None, point_size: float = 16.0, color: object | None = None):
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
            # Default: use template for dynamic tint when no explicit color provided
            try:
                img.setTemplate_(color is None)
            except Exception:
                pass
            # Apply size and optional color configuration when available
            try:
                from AppKit import NSImageSymbolConfiguration, NSColor
                conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(point_size, 0, 1)
                img = img.imageWithSymbolConfiguration_(conf)
                # Apply hierarchical/palette color if requested (force white for dark buttons)
                if color is not None:
                    try:
                        col = color if hasattr(color, 'CGColor') else NSColor.whiteColor()
                        if hasattr(NSImageSymbolConfiguration, 'configurationWithHierarchicalColor_'):
                            c2 = NSImageSymbolConfiguration.configurationWithHierarchicalColor_(col)
                            img = img.imageWithSymbolConfiguration_(c2)
                        elif hasattr(NSImageSymbolConfiguration, 'configurationWithPaletteColors_'):
                            try:
                                c2 = NSImageSymbolConfiguration.configurationWithPaletteColors_([col])
                            except Exception:
                                c2 = NSImageSymbolConfiguration.configurationWithPaletteColors_(col)
                            img = img.imageWithSymbolConfiguration_(c2)
                        # When explicit color is provided, render as non-template so it keeps its color
                        try:
                            img.setTemplate_(False)
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                # Fallback: set a nominal size
                try:
                    img.setSize_((point_size, point_size))
                except Exception:
                    pass
            return img
        except Exception:
            return None

    def _create_cross_image(self, size: float = 14.0):
        """Draw a simple white cross into an NSImage (non-template)."""
        try:
            from AppKit import NSImage, NSBezierPath, NSColor
            img = NSImage.alloc().initWithSize_((size, size))
            img.lockFocus()
            try:
                NSColor.whiteColor().setStroke()
                path = NSBezierPath.bezierPath()
                path.setLineWidth_(2.0)
                pad = 3.0
                # Diagonal 1
                path.moveToPoint_((pad, pad))
                path.lineToPoint_((size - pad, size - pad))
                # Diagonal 2
                path.moveToPoint_((size - pad, pad))
                path.lineToPoint_((pad, size - pad))
                path.stroke()
            except Exception:
                pass
            img.unlockFocus()
            try:
                # Keep explicit white color; do not treat as template
                img.setTemplate_(False)
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

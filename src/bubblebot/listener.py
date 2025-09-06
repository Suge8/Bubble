"""
listener.py

Handles global keyboard listening and dynamic hotkey customization for BubbleBot overlay.
Allows users to set their own keyboard shortcut (trigger) for toggling the BubbleBot window.
"""

# Python libraries
import json
import os
import time
from pathlib import Path

# Apple libraries
from AppKit import (
    NSApp,
    NSColor,
    NSEvent,
    NSFont,
    NSKeyDown,
    NSMakeRect,
    NSTextAlignmentCenter,
    NSTextField,
    NSView,
    NSButton,
    NSAnimationContext,
    NSVisualEffectView,
    NSVisualEffectStateActive,
    NSVisualEffectBlendingModeBehindWindow,
)
from AppKit import NSWindowAbove
import objc
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventKeyboardGetUnicodeString,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGKeyboardEventKeycode,
    NSEvent,
    NSAlternateKeyMask,
    NSCommandKeyMask,
    NSControlKeyMask,
    NSShiftKeyMask,
)

# Local libraries
from .constants import LAUNCHER_TRIGGER, LAUNCHER_TRIGGER_MASK
from .health_checks import LOG_DIR

# File for storing the custom trigger
TRIGGER_FILE = LOG_DIR / "custom_trigger.json"
SPECIAL_KEY_NAMES = {
    49: "Space", 36: "Return", 53: "Escape",
    122: "F1", 120: "F2", 99: "F3", 118: "F4",
    96: "F5", 97: "F6", 98: "F7", 100: "F8",
    101: "F9", 109: "F10", 103: "F11", 111: "F12",
    123: "Left Arrow", 124: "Right Arrow",
    125: "Down Arrow", 126: "Up Arrow"
}
handle_new_trigger = None

class _ActionProxy(objc.lookUpClass('NSObject')):
    def initWithHandler_(self, handler):
        self = objc.super(_ActionProxy, self).init()
        if self is None:
            return None
        self._handler = handler
        return self

    def callWithSender_(self, sender):
        try:
            if callable(self._handler):
                self._handler(sender)
        except Exception:
            pass

def load_custom_launcher_trigger():
    """Load custom launcher trigger from JSON file if it exists."""
    if TRIGGER_FILE.exists():
        try:
            with open(TRIGGER_FILE, "r") as f:
                data = json.load(f)
                launcher_trigger = {"flags": data["flags"], "key": data["key"]}
            print(f"Overwriting default with a custom BubbleBot launch shortcut:\n  {launcher_trigger}", flush=True)
            print(f"To return to default, delete this file:\n  {TRIGGER_FILE}", flush=True)
            LAUNCHER_TRIGGER.update(launcher_trigger)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[BubbleBot] Failed to load custom trigger: {e}. Using default trigger.", flush=True)

def set_custom_launcher_trigger(app, target_window=None):
    """Show a polished Vercel-style overlay to set a new global hotkey trigger.

    If target_window is provided, the overlay attaches to that window's content view
    (e.g., Settings window). Otherwise attaches to the main app window.
    """
    from .i18n import t as _t
    if target_window is None:
        app.showWindow_(None)
    try:
        # Ensure the app is frontmost and target window is key
        NSApp.activateIgnoringOtherApps_(True)
        if target_window is not None:
            target_window.makeKeyAndOrderFront_(None)
    except Exception:
        pass
    print("Setting new BubbleBot launch shortcut. (Press keys or click Cancel)", flush=True)

    # Get the content view bounds (fallback to main window if target bounds look invalid)
    content_view = (target_window.contentView() if target_window is not None else app.window.contentView())
    content_bounds = content_view.bounds()
    try:
        if content_bounds.size.width < 50 or content_bounds.size.height < 50:
            content_view = app.window.contentView()
            content_bounds = content_view.bounds()
    except Exception:
        pass

    # Overlay dim layer (black alpha) + optional blur underlay
    overlay_view = NSView.alloc().initWithFrame_(content_bounds)
    overlay_view.setWantsLayer_(True)
    overlay_view.setAlphaValue_(0.0)
    overlay_view.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.45).CGColor())
    try:
        overlay_view.setAutoresizingMask_((1 << 1) | (1 << 4))
    except Exception:
        pass

    # Card (centered)
    card_w, card_h = 440, 220
    cx = (content_bounds.size.width - card_w) / 2
    cy = (content_bounds.size.height - card_h) / 2
    card_frame = NSMakeRect(cx, cy, card_w, card_h)
    card = NSView.alloc().initWithFrame_(card_frame)
    card.setWantsLayer_(True)
    # Theme-aware colors (black/white Vercel style)
    is_dark = False
    try:
        appearance = NSApp.effectiveAppearance()
        name = appearance.bestMatchFromAppearancesWithNames_(["NSAppearanceNameDarkAqua", "NSAppearanceNameAqua"])
        is_dark = (name == "NSAppearanceNameDarkAqua")
    except Exception:
        pass
    bg = (NSColor.colorWithCalibratedWhite_alpha_(0.10, 0.96) if is_dark else NSColor.whiteColor())
    border = (NSColor.whiteColor().colorWithAlphaComponent_(0.08) if is_dark else NSColor.blackColor().colorWithAlphaComponent_(0.08))
    card.layer().setBackgroundColor_(bg.CGColor())
    card.layer().setCornerRadius_(12.0)
    card.layer().setBorderWidth_(1.0)
    card.layer().setBorderColor_(border.CGColor())
    card.layer().setShadowColor_(NSColor.blackColor().CGColor())
    card.layer().setShadowOpacity_(0.18)
    card.layer().setShadowRadius_(10.0)
    card.layer().setShadowOffset_((0.0, -1.0))
    card.setAlphaValue_(0.0)

    # Title
    title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, card_h - 54, card_w - 40, 24))
    title.setBezeled_(False); title.setDrawsBackground_(False); title.setEditable_(False); title.setSelectable_(False)
    title.setAlignment_(NSTextAlignmentCenter)
    title.setFont_(NSFont.boldSystemFontOfSize_(16))
    title.setStringValue_(_t('hotkey.overlay.title', default='Set Shortcut'))

    # Subtitle
    subtitle = NSTextField.alloc().initWithFrame_(NSMakeRect(20, card_h - 78, card_w - 40, 20))
    subtitle.setBezeled_(False); subtitle.setDrawsBackground_(False); subtitle.setEditable_(False); subtitle.setSelectable_(False)
    subtitle.setAlignment_(NSTextAlignmentCenter)
    subtitle.setFont_(NSFont.systemFontOfSize_(12))
    try:
        subtitle.setTextColor_(NSColor.secondaryLabelColor())
    except Exception:
        pass
    subtitle.setStringValue_(_t('hotkey.overlay.subtitle', default='Press the new shortcut key combination now.'))

    # Trigger display pill
    pill_w, pill_h = 300, 38
    pill = NSView.alloc().initWithFrame_(NSMakeRect((card_w - pill_w)/2, card_h - 124, pill_w, pill_h))
    pill.setWantsLayer_(True)
    pill_bg = (NSColor.whiteColor().colorWithAlphaComponent_(0.06) if is_dark else NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0))
    pill_border = (NSColor.whiteColor().colorWithAlphaComponent_(0.12) if is_dark else NSColor.blackColor().colorWithAlphaComponent_(0.08))
    pill.layer().setBackgroundColor_(pill_bg.CGColor())
    pill.layer().setCornerRadius_(8.0)
    pill.layer().setBorderWidth_(1.0)
    pill.layer().setBorderColor_(pill_border.CGColor())

    display = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 1, pill_w, pill_h))
    display.setBezeled_(False); display.setDrawsBackground_(False); display.setEditable_(False); display.setSelectable_(False)
    display.setAlignment_(NSTextAlignmentCenter)
    display.setFont_(NSFont.systemFontOfSize_(15))
    display.setStringValue_(_t('hotkey.overlay.wait', default='Waiting for key press…'))
    pill.addSubview_(display)

    # Cancel button (ghost)
    cancel = NSButton.alloc().initWithFrame_(NSMakeRect((card_w - 110)/2, 18, 110, 36))
    cancel.setTitle_(_t('button.cancel'))
    try:
        cancel.setWantsLayer_(True)
        cancel.layer().setCornerRadius_(8.0)
        cancel.layer().setBackgroundColor_((NSColor.whiteColor().colorWithAlphaComponent_(0.10) if is_dark else NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10)).CGColor())
        # no border, remove focus ring
        try:
            from AppKit import NSFocusRingTypeNone
            cancel.setFocusRingType_(NSFocusRingTypeNone)
            cancel.setBordered_(False)
            cancel.setFont_(NSFont.systemFontOfSize_(14))
        except Exception:
            pass
    except Exception:
        pass

    def cancel_action(sender):
        print("Cancelled custom shortcut selection.", flush=True)
        # Restore previous trigger
        LAUNCHER_TRIGGER["flags"], LAUNCHER_TRIGGER["key"] = prev_flags, prev_key
        overlay_view.removeFromSuperview()
        global handle_new_trigger
        handle_new_trigger = None
        try:
            app.showWindow_(None)
        except Exception:
            pass
    proxy = _ActionProxy.alloc().initWithHandler_(cancel_action)
    cancel.setTarget_(proxy)
    cancel.setAction_("callWithSender:")
    # Keep proxy alive via attribute on overlay
    setattr(overlay_view, '_cancel_proxy', proxy)

    # Assemble
    card.addSubview_(title); card.addSubview_(subtitle); card.addSubview_(pill); card.addSubview_(cancel)
    overlay_view.addSubview_(card)
    try:
        content_view.addSubview_positioned_relativeTo_(overlay_view, NSWindowAbove, None)
    except Exception:
        content_view.addSubview_(overlay_view)
    try:
        if target_window is not None:
            target_window.makeKeyAndOrderFront_(None)
    except Exception:
        pass

    # Preserve previous trigger and temporarily disable current one only
    # after overlay has been added (avoid losing shortcut if overlay fails)
    prev_flags, prev_key = LAUNCHER_TRIGGER.get("flags"), LAUNCHER_TRIGGER.get("key")
    LAUNCHER_TRIGGER["flags"], LAUNCHER_TRIGGER["key"] = None, None

    # Animate overlay + card
    try:
        NSAnimationContext.beginGrouping()
        NSAnimationContext.currentContext().setDuration_(0.18)
        overlay_view.animator().setAlphaValue_(1.0)
        card.animator().setAlphaValue_(1.0)
        # slight rise
        cf = card.frame()
        card.animator().setFrameOrigin_((cf.origin.x, cf.origin.y + 6))
        NSAnimationContext.endGrouping()
    except Exception:
        overlay_view.setAlphaValue_(1.0)
        card.setAlphaValue_(1.0)
    print("DEBUG: Hotkey overlay shown", flush=True)

    # Handler for new trigger
    def custom_handle_new_trigger(event, flags, keycode):
        launcher_trigger = {"flags": flags, "key": keycode}
        with open(TRIGGER_FILE, "w") as f:
            json.dump(launcher_trigger, f)
        LAUNCHER_TRIGGER.update(launcher_trigger)
        trigger_str = get_trigger_string(event, flags, keycode)
        print("New BubbleBot launch shortcut set:", flush=True)
        print(f"  {launcher_trigger}", flush=True)
        print(f"  {trigger_str}", flush=True)
        try:
            display.setStringValue_(trigger_str)
        except Exception:
            pass
        # Fade out overlay after short delay
        try:
            from Foundation import NSTimer
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1.0, overlay_view, 'removeFromSuperview', None, False)
        except Exception:
            overlay_view.removeFromSuperview()
        # Immediately refresh menu + settings UI
        try:
            if hasattr(app, '_refresh_status_menu_titles'):
                app._refresh_status_menu_titles()
        except Exception:
            pass
        try:
            if hasattr(app, '_settings_window') and app._settings_window:
                app._settings_window.refreshHotkey_(None)
        except Exception:
            pass
        global handle_new_trigger
        handle_new_trigger = None
        app.showWindow_(None)
        return None

    # Set the global handler
    global handle_new_trigger
    handle_new_trigger = custom_handle_new_trigger

def get_modifier_names(flags):
    """Helper to get modifier names as list."""
    modifier_names = []
    if flags & NSShiftKeyMask:
        modifier_names.append("Shift")
    if flags & NSControlKeyMask:
        modifier_names.append("Control")
    if flags & NSAlternateKeyMask:
        modifier_names.append("Option")
    if flags & NSCommandKeyMask:
        modifier_names.append("Command")
    return modifier_names

def get_trigger_string(event, flags, keycode):
    """Return a human-readable string for the trigger."""
    modifier_names = get_modifier_names(flags)
    if keycode in SPECIAL_KEY_NAMES:
        key_name = SPECIAL_KEY_NAMES[keycode]
    else:
        key_name = NSEvent.eventWithCGEvent_(event).characters()
    return " + ".join(modifier_names + [key_name]) if modifier_names else key_name

def global_show_hide_listener(app):
    """Global event listener for showing/hiding BubbleBot and for new trigger assignment."""
    DEBUG_KEY_LOG = os.environ.get("BB_KEY_DEBUG") == "1"
    # 按键闩锁：每次按下只触发一次（去掉最小间隔限制，快速连按每次都生效）
    latch_active = [False]
    def listener(proxy, event_type, event, refcon):
        if event_type == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            flags = CGEventGetFlags(event)
            # Debug print for key/flag detection
            if DEBUG_KEY_LOG:
                print("Key event detected:", keycode, "flags:", flags, "trigger:", LAUNCHER_TRIGGER)
            if (None in set(LAUNCHER_TRIGGER.values())) and handle_new_trigger:
                print("  Received keys, establishing new shortcut..", flush=True)
                handle_new_trigger(event, flags, keycode)
                return None
            # Use bitwise AND for modifier matching (CMD + G etc)
            pressed = (keycode == LAUNCHER_TRIGGER["key"] and (flags & LAUNCHER_TRIGGER["flags"]) == LAUNCHER_TRIGGER["flags"])
            if pressed:
                # 去除时间阈值：只要不是长按重复触发（由闩锁抑制），每次按下都切换
                if not latch_active[0]:
                    if app.window and app.window.isVisible():
                        app.hideWindow_(None)
                    else:
                        app.showWindow_(None)
                    latch_active[0] = True
                return None
            else:
                # 非触发组合，释放闩锁
                latch_active[0] = False
        elif event_type == kCGEventKeyUp:
            # 任意按键抬起即释放闩锁，允许再次切换
            latch_active[0] = False
        return event
    return listener

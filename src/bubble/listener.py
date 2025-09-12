"""
listener.py

Handles global keyboard listening and dynamic hotkey customization for Bubble overlay.
Allows users to set their own keyboard shortcut (trigger) for toggling the Bubble window.
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
    NSWindow,
)
from AppKit import NSWindowAbove
from AppKit import NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskBorderless
from AppKit import NSBackingStoreBuffered, NSFloatingWindowLevel
from AppKit import NSEvent, NSEventMaskKeyDown
from AppKit import (
    NSEventModifierFlagCommand,
    NSEventModifierFlagOption,
    NSEventModifierFlagShift,
    NSEventModifierFlagControl,
)
from AppKit import NSImageOnly, NSImageScaleProportionallyUpOrDown
import objc
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventKeyboardGetUnicodeString,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGKeyboardEventKeycode,
    CGEventTapEnable,
    CGEventTapIsEnabled,
)

# Local libraries
from .constants import LAUNCHER_TRIGGER, LAUNCHER_TRIGGER_MASK
from .health_checks import LOG_DIR

# Files for storing custom triggers
TRIGGER_FILE = LOG_DIR / "custom_trigger.json"  # show/hide launcher
TRIGGER_SWITCH_FILE = LOG_DIR / "custom_trigger_switch.json"  # cycle/switch pages
SPECIAL_KEY_NAMES = {
    49: "Space", 36: "Return", 53: "Escape",
    122: "F1", 120: "F2", 99: "F3", 118: "F4",
    96: "F5", 97: "F6", 98: "F7", 100: "F8",
    101: "F9", 109: "F10", 103: "F11", 111: "F12",
    123: "Left Arrow", 124: "Right Arrow",
    125: "Down Arrow", 126: "Up Arrow"
}
SWITCHER_TRIGGER = {"flags": None, "key": None}
handle_new_trigger = None


# A borderless window subclass that can become key/main to host the hotkey UI
class HotkeyPanelWindow(NSWindow):
    def canBecomeKeyWindow(self):
        return True
    def canBecomeMainWindow(self):
        return True

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

def _create_symbol_image(symbol_name: str | None, point_size: float = 14.0, color: object | None = None):
    """Create an NSImage from SF Symbols when available; returns None on failure."""
    if not symbol_name:
        return None
    try:
        from AppKit import NSImage
        try:
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
        except Exception:
            img = None
        if img is None:
            return None
        try:
            img.setTemplate_(color is None)
        except Exception:
            pass
        try:
            from AppKit import NSImageSymbolConfiguration, NSColor
            conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(point_size, 0, 1)
            img = img.imageWithSymbolConfiguration_(conf)
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
                    # Keep explicit color by making the image non-template
                    try:
                        img.setTemplate_(False)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            try:
                img.setSize_((point_size, point_size))
            except Exception:
                pass
        return img
    except Exception:
        return None

def _create_cross_image(size: float = 14.0):
    """Fallback cross image when SF Symbols unavailable."""
    try:
        from AppKit import NSImage, NSBezierPath, NSColor
        img = NSImage.alloc().initWithSize_((size, size))
        img.lockFocus()
        try:
            NSColor.whiteColor().setStroke()
            path = NSBezierPath.bezierPath()
            path.setLineWidth_(2.0)
            pad = 3.0
            path.moveToPoint_((pad, pad))
            path.lineToPoint_((size - pad, size - pad))
            path.moveToPoint_((size - pad, pad))
            path.lineToPoint_((pad, size - pad))
            path.stroke()
        except Exception:
            pass
        img.unlockFocus()
        try:
            img.setTemplate_(True)
        except Exception:
            pass
        return img
    except Exception:
        return None

def load_custom_launcher_trigger():
    """Load custom triggers from JSON files if they exist (launcher + switcher)."""
    # Only recognize standard modifier bits for robust matching
    modifier_mask = (
        int(NSEventModifierFlagOption)
        | int(NSEventModifierFlagCommand)
        | int(NSEventModifierFlagControl)
        | int(NSEventModifierFlagShift)
    )
    if TRIGGER_FILE.exists():
        try:
            with open(TRIGGER_FILE, "r") as f:
                data = json.load(f)
                cleaned_flags = int(data["flags"]) & modifier_mask
                launcher_trigger = {"flags": cleaned_flags, "key": int(data["key"]) }
            print(f"Overwriting default with a custom Bubble launch shortcut:\n  {launcher_trigger}", flush=True)
            print(f"To return to default, delete this file:\n  {TRIGGER_FILE}", flush=True)
            LAUNCHER_TRIGGER.update(launcher_trigger)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[Bubble] Failed to load custom trigger: {e}. Using default trigger.", flush=True)
    # Switcher (optional)
    try:
        if TRIGGER_SWITCH_FILE.exists():
            with open(TRIGGER_SWITCH_FILE, "r") as f:
                data = json.load(f)
                cleaned_flags = None if data.get("flags") is None else (int(data.get("flags")) & modifier_mask)
                SWITCHER_TRIGGER.update({"flags": cleaned_flags, "key": data.get("key") and int(data.get("key"))})
            print(f"Loaded custom switcher shortcut: {SWITCHER_TRIGGER}", flush=True)
    except Exception as e:
        print(f"[Bubble] Failed to load custom switcher trigger: {e}", flush=True)

def set_custom_launcher_trigger(app, target_window=None, mode: str = 'launcher'):
    """Open a compact modal window to set a new global hotkey trigger (no overlay)."""
    from .i18n import t as _t
    try:
        NSApp.activateIgnoringOtherApps_(True)
    except Exception:
        pass

    # If a previous panel exists, close it first to reset state.
    try:
        prev = getattr(app, '_hotkey_panel_win', None)
        if prev is not None:
            try:
                prev.orderOut_(None)
            except Exception:
                pass
            setattr(app, '_hotkey_panel_win', None)
    except Exception:
        pass

    # Small borderless floating window that can become key, with custom background.
    w, h = 420, 160
    rect = NSMakeRect(0, 0, w, h)

    win = HotkeyPanelWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect,
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False,
    )
    try:
        win.setReleasedWhenClosed_(False)
        try:
            win.setLevel_(NSFloatingWindowLevel + 1)
        except Exception:
            pass
        try:
            win.setMovableByWindowBackground_(True)
        except Exception:
            pass
        try:
            # Transparent window; rounded content view will provide the visible card background
            win.setOpaque_(False)
            from AppKit import NSColor
            win.setBackgroundColor_(NSColor.clearColor())
            win.setHasShadow_(True)
        except Exception:
            pass
    except Exception:
        pass

    # Custom light rounded content background (solid white)
    content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, w, h))
    content.setWantsLayer_(True)
    try:
        content.layer().setCornerRadius_(14.0)
        content.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
        if hasattr(content.layer(), 'setMasksToBounds_'):
            content.layer().setMasksToBounds_(True)
    except Exception:
        pass
    win.setContentView_(content)
    try:
        setattr(app, '_hotkey_panel_win', win)
    except Exception:
        pass

    # Title — horizontally centered across the full width (larger and nicer)
    title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - 56, w, 30))
    title.setBezeled_(False); title.setDrawsBackground_(False); title.setEditable_(False); title.setSelectable_(False)
    title.setAlignment_(NSTextAlignmentCenter)
    try:
        cell = title.cell()
        if cell:
            cell.setAlignment_(NSTextAlignmentCenter)
    except Exception:
        pass
    try:
        # Try semibold system font at 20pt; fallback to bold
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
    try:
        # Dark text on light background
        title.setTextColor_(NSColor.labelColor())
    except Exception:
        pass
    title.setStringValue_(_t('hotkey.overlay.title', default='Set Shortcut'))

    # Subtitle
    subtitle = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - 72, w, 18))
    subtitle.setBezeled_(False); subtitle.setDrawsBackground_(False); subtitle.setEditable_(False); subtitle.setSelectable_(False)
    subtitle.setAlignment_(NSTextAlignmentCenter)
    subtitle.setFont_(NSFont.systemFontOfSize_(12))
    try:
        subtitle.setTextColor_(NSColor.secondaryLabelColor())
    except Exception:
        pass
    # Indicate which shortcut is being changed
    try:
        sub_txt = _t('hotkey.overlay.subtitle', default='⌨️ Press a combo with a modifier.')
        if mode == 'switcher':
            sub_txt = sub_txt + ' — ' + _t('hotkey.overlay.switcher', default='Switch Windows')
        else:
            sub_txt = sub_txt + ' — ' + _t('hotkey.overlay.launcher', default='Show/Hide Bubble')
        subtitle.setStringValue_(sub_txt)
    except Exception:
        subtitle.setStringValue_(_t('hotkey.overlay.subtitle', default='⌨️ Press a combo with a modifier.'))

    # Display (current pressed keys)
    display = NSTextField.alloc().initWithFrame_(NSMakeRect(0, h - 100, w, 24))
    display.setBezeled_(False); display.setDrawsBackground_(False); display.setEditable_(False); display.setSelectable_(False)
    display.setAlignment_(NSTextAlignmentCenter)
    display.setFont_(NSFont.systemFontOfSize_(14))
    try:
        display.setTextColor_(NSColor.labelColor())
    except Exception:
        pass
    display.setStringValue_(_t('hotkey.overlay.wait', default='Waiting for key press…'))

    # Close button — top-left, icon style like Settings close
    close_size = 28
    close_btn = NSButton.alloc().initWithFrame_(NSMakeRect(12, h - 12 - close_size, close_size, close_size))
    try:
        close_btn.setBezelStyle_(0)
    except Exception:
        pass
    try:
        close_btn.setBordered_(False)
    except Exception:
        pass
    try:
        close_btn.setWantsLayer_(True)
        close_btn.layer().setCornerRadius_(close_size/2.0)
        # Dark background with subtle ring, matches Settings style
        close_btn.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.86).CGColor())
        ring = NSColor.blackColor().colorWithAlphaComponent_(0.18)
        close_btn.layer().setBorderWidth_(1.0)
        close_btn.layer().setBorderColor_(ring.CGColor())
    except Exception:
        pass
    # Icon
    try:
        from AppKit import NSColor
        # Always clear title to avoid localized default like "按钮"
        try:
            close_btn.setTitle_("")
        except Exception:
            pass
        # Set icon to 12pt per request (no extra fallbacks)
        imgx = _create_symbol_image('xmark', point_size=12.0, color=NSColor.whiteColor())
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
        except Exception:
            pass
        # No drawn overlay fallback; rely solely on SF Symbol at 8pt
    except Exception:
        pass

    # Inset title left/right equally to avoid visual overlap with the close button while keeping true center
    try:
        margin = int(close_size + 12 + 6)
        title.setFrame_(NSMakeRect(margin, title.frame().origin.y, max(10, w - 2*margin), title.frame().size.height))
    except Exception:
        pass
    content.addSubview_(title); content.addSubview_(subtitle); content.addSubview_(display); content.addSubview_(close_btn)

    # Temporarily disable global event tap to avoid interference
    tap_was_enabled = False
    try:
        if hasattr(app, 'eventTap') and app.eventTap:
            tap_was_enabled = bool(CGEventTapIsEnabled(app.eventTap))
            CGEventTapEnable(app.eventTap, False)
    except Exception:
        pass

    # Show window
    try:
        win.center(); win.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
    except Exception:
        pass

    # Preserve and disable current trigger
    if mode == 'switcher':
        prev_flags, prev_key = SWITCHER_TRIGGER.get("flags"), SWITCHER_TRIGGER.get("key")
        SWITCHER_TRIGGER["flags"], SWITCHER_TRIGGER["key"] = None, None
    else:
        prev_flags, prev_key = LAUNCHER_TRIGGER.get("flags"), LAUNCHER_TRIGGER.get("key")
        LAUNCHER_TRIGGER["flags"], LAUNCHER_TRIGGER["key"] = None, None
    print("DEBUG: Hotkey window shown", flush=True)

    def close_panel():
        try:
            win.orderOut_(None)
            # Re-enable global tap
            try:
                if hasattr(app, 'eventTap') and app.eventTap:
                    CGEventTapEnable(app.eventTap, tap_was_enabled)
            except Exception:
                pass
            try:
                setattr(app, '_hotkey_panel_win', None)
            except Exception:
                pass
        except Exception:
            pass

    def cancel_action(_):
        print("Cancelled custom shortcut selection.", flush=True)
        if mode == 'switcher':
            SWITCHER_TRIGGER["flags"], SWITCHER_TRIGGER["key"] = prev_flags, prev_key
        else:
            LAUNCHER_TRIGGER["flags"], LAUNCHER_TRIGGER["key"] = prev_flags, prev_key
        close_panel()
        global handle_new_trigger
        handle_new_trigger = None
        try:
            app.showWindow_(None)
        except Exception:
            pass
    proxy = _ActionProxy.alloc().initWithHandler_(cancel_action)
    close_btn.setTarget_(proxy)
    close_btn.setAction_("callWithSender:")
    setattr(win, '_cancel_proxy', proxy)

    # Handler (uses global event tap to capture CGEvent)
    def custom_handle_new_trigger(event, flags, keycode):
        # Persist only recognized modifier bits to keep trigger matching stable
        modifier_mask = (
            int(NSEventModifierFlagOption)
            | int(NSEventModifierFlagCommand)
            | int(NSEventModifierFlagControl)
            | int(NSEventModifierFlagShift)
        )
        cleaned_flags = int(flags) & modifier_mask
        trigger_payload = {"flags": int(cleaned_flags), "key": int(keycode)}
        if mode == 'switcher':
            with open(TRIGGER_SWITCH_FILE, "w") as f:
                json.dump(trigger_payload, f)
            SWITCHER_TRIGGER.update(trigger_payload)
            # Persist to config as well for UI display or future use
            try:
                from .components.config_manager import ConfigManager as _CM
                _CM.set_switcher_hotkey(int(cleaned_flags), int(keycode))
            except Exception:
                pass
        else:
            with open(TRIGGER_FILE, "w") as f:
                json.dump(trigger_payload, f)
            LAUNCHER_TRIGGER.update(trigger_payload)
        trigger_str = get_trigger_string(event, cleaned_flags, keycode)
        print("New Bubble shortcut set:", flush=True)
        print(f"  mode={mode}: {trigger_payload}", flush=True)
        print(f"  {trigger_str}", flush=True)
        try:
            display.setStringValue_(trigger_str)
        except Exception:
            pass
        close_panel()
        try:
            if hasattr(app, '_refresh_status_menu_titles'):
                app._refresh_status_menu_titles()
        except Exception:
            pass
        try:
            if hasattr(app, '_settings_window') and app._settings_window:
                try:
                    app._settings_window.refreshHotkey_(None)
                except Exception:
                    pass
                try:
                    app._settings_window.refreshSwitcherHotkey_(None)
                except Exception:
                    pass
                try:
                    if hasattr(app._settings_window, '_refresh_suspend_value'):
                        app._settings_window._refresh_suspend_value()
                except Exception:
                    pass
        except Exception:
            pass
        global handle_new_trigger
        handle_new_trigger = None
        try:
            app.showWindow_(None)
        except Exception:
            pass
        return None

    global handle_new_trigger
    handle_new_trigger = custom_handle_new_trigger

    # Local fallback: if global event tap isn't delivering events (no accessibility
    # permission, or tap disabled), capture the next key press from this modal
    # window using a local monitor. This does not require Accessibility permissions.
    try:
        def _local_monitor(ev):
            try:
                # Key down only; gather flags and keycode
                flags = int(ev.modifierFlags())
                keycode = int(ev.keyCode())
                # Build a synthetic CGEvent for display string best-effort
                # If unavailable, pass through None; get_trigger_string handles it.
                cg_event = None
                try:
                    from Quartz import CGEventCreateKeyboardEvent
                    cg_event = CGEventCreateKeyboardEvent(None, keycode, True)
                except Exception:
                    cg_event = None

                # Only accept combinations that include at least one modifier to
                # avoid accidental single-key triggers.
                modifier_mask = (
                    int(NSEventModifierFlagOption)
                    | int(NSEventModifierFlagCommand)
                    | int(NSEventModifierFlagControl)
                    | int(NSEventModifierFlagShift)
                )
                has_modifier = bool(flags & modifier_mask)
                # ESC cancels
                if handle_new_trigger and keycode == 53:  # Escape
                    try:
                        cancel_action(None)
                    except Exception:
                        pass
                    # Swallow event to avoid beep
                    return None
                if has_modifier and handle_new_trigger:
                    # Persist only recognized modifier bits to keep trigger matching stable
                    cleaned_flags = flags & modifier_mask
                    # Invoke the same handler used by the global tap
                    custom_handle_new_trigger(cg_event, cleaned_flags, keycode)
                    # Swallow the event to avoid system beep
                    return None
                else:
                    try:
                        # Prompt requirement to the user
                        from .i18n import t as _t
                        display.setStringValue_(_t('hotkey.overlay.requireModifier', default='Please include at least one modifier (⌘/⌥/⌃/⇧)'))
                    except Exception:
                        pass
                # If no modifier, still swallow to avoid beep – user can try again
                return None
            except Exception:
                # On any error, allow event to pass through (but still try to suppress beep)
                return None

        monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, _local_monitor
        )
        # Keep a strong reference so PyObjC doesn't autorelease it
        setattr(win, '_local_key_monitor', monitor)

        # Ensure monitor is removed when the panel closes
        _orig_close = close_panel

        def _wrapped_close():
            try:
                if hasattr(win, '_local_key_monitor') and getattr(win, '_local_key_monitor') is not None:
                    NSEvent.removeMonitor_(getattr(win, '_local_key_monitor'))
                    setattr(win, '_local_key_monitor', None)
            except Exception:
                pass
            _orig_close()

        # Rebind close_panel to wrapped version
        close_panel = _wrapped_close  # type: ignore
    except Exception:
        pass

def get_modifier_names(flags):
    """Helper to get modifier names as list."""
    modifier_names = []
    if flags & int(NSEventModifierFlagShift):
        modifier_names.append("Shift")
    if flags & int(NSEventModifierFlagControl):
        modifier_names.append("Control")
    if flags & int(NSEventModifierFlagOption):
        modifier_names.append("Option")
    if flags & int(NSEventModifierFlagCommand):
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
    """Global event listener for showing/hiding Bubble and for new trigger assignment."""
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
            # Switcher: only when app is active/visible to avoid global side-effects
            try:
                if SWITCHER_TRIGGER["key"] is not None and SWITCHER_TRIGGER["flags"] is not None:
                    if keycode == SWITCHER_TRIGGER["key"] and (flags & SWITCHER_TRIGGER["flags"]) == SWITCHER_TRIGGER["flags"]:
                        # Require Bubble to be visible/key to cycle (broaden detection to include any Bubble window)
                        is_active = False
                        try:
                            from AppKit import NSApp
                            is_active = bool(NSApp().isActive()) if callable(NSApp) else False
                        except Exception:
                            is_active = False
                        # If NSApp check fails, consider visible/key windows as active
                        if not is_active:
                            try:
                                mw = getattr(app, 'multiwindow_manager', None)
                                if mw and getattr(mw, 'ns_windows', None):
                                    for _wid, _w in list(mw.ns_windows.items()):
                                        try:
                                            if _w.isVisible() or _w.isKeyWindow():
                                                is_active = True
                                                break
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                        if is_active:
                            try:
                                if hasattr(app, 'cycleActiveWindow_'):
                                    app.cycleActiveWindow_(None)
                                    return None
                                # Fallback direct call
                                mw = getattr(app, 'multiwindow_manager', None)
                                if mw and hasattr(mw, 'cycle_active_window'):
                                    mw.cycle_active_window(True)
                                    return None
                            except Exception:
                                pass
            except Exception:
                pass
        elif event_type == kCGEventKeyUp:
            # 任意按键抬起即释放闩锁，允许再次切换
            latch_active[0] = False
        return event
    return listener

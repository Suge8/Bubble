import objc
from AppKit import NSView, NSColor, NSTextField, NSFont, NSBezierPath, NSWindowAbove
from Foundation import NSTimer, NSRunLoop, NSDefaultRunLoopMode, NSThread, NSOperationQueue


class ToastManager:
    """Lightweight toast utility: show a temporary non-blocking message overlay.

    Usage: ToastManager.show(text, parent_view, duration=3.0)
    """

    _current_view = None

    @classmethod
    def show(cls, text: str, parent: NSView, duration: float = 3.0, relative_to: NSView = None):
        # Ensure UI work runs on main thread
        try:
            if not NSThread.isMainThread():
                def _call():
                    try:
                        ToastManager.show(text=text, parent=parent, duration=duration, relative_to=relative_to)
                    except Exception:
                        pass
                try:
                    NSOperationQueue.mainQueue().addOperationWithBlock_(_call)
                except Exception:
                    # best-effort fallback: schedule immediate timer on main loop
                    try:
                        timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
                            0.0, cls, 'dismissTimerFired:', None, False
                        )
                        NSRunLoop.currentRunLoop().addTimer_forMode_(timer, NSDefaultRunLoopMode)
                    except Exception:
                        pass
                return
        except Exception:
            pass
        try:
            if cls._current_view is not None:
                try:
                    cls._current_view.removeFromSuperview()
                except Exception:
                    pass
                cls._current_view = None

            # Container (opaque, high-contrast, always on top)
            width = 360
            height = 32
            frame = parent.bounds()
            x = (frame.size.width - width) / 2
            y = frame.size.height - height - 6  # near top inside parent
            view = NSView.alloc().initWithFrame_(((x, y), (width, height)))
            view.setWantsLayer_(True)
            try:
                # Opaque dark background for maximum visibility
                view.layer().setCornerRadius_(8.0)
                view.layer().setMasksToBounds_(True)
                # Use a near-opaque black with a subtle border for contrast
                view.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.92).CGColor())
                try:
                    view.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.15).CGColor())
                    view.layer().setBorderWidth_(1.0)
                    view.layer().setShadowOpacity_(0.25)
                    view.layer().setShadowRadius_(6.0)
                except Exception:
                    pass
            except Exception:
                pass

            # Label
            label = NSTextField.alloc().initWithFrame_(((12, 5), (width - 24, height - 10)))
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            try:
                label.setTextColor_(NSColor.whiteColor())
            except Exception:
                pass
            try:
                label.setFont_(NSFont.boldSystemFontOfSize_(13))
            except Exception:
                pass
            label.setStringValue_(text or "")
            view.addSubview_(label)

            # Attach to parent on top
            try:
                # Put on the very top; if relative_to provided, stack above it for safety
                parent.addSubview_positioned_relativeTo_(view, NSWindowAbove, relative_to)
            except Exception:
                try:
                    parent.addSubview_(view)
                except Exception:
                    return

            cls._current_view = view
            try:
                # Ensure fully visible (no accidental zero alpha)
                view.setHidden_(False)
                view.setAlphaValue_(1.0)
            except Exception:
                pass

            # Schedule removal
            def _dismiss(_):
                try:
                    if cls._current_view is view:
                        view.removeFromSuperview()
                        cls._current_view = None
                except Exception:
                    cls._current_view = None

            # Use NSTimer so it runs on main run loop
            try:
                timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
                    float(duration or 3.0), cls, 'dismissTimerFired:', None, False
                )
                # store weak ref for which view to dismiss
                view._toast_timer = timer  # type: ignore
                # Use default mode so it ticks during normal interactions
                NSRunLoop.currentRunLoop().addTimer_forMode_(timer, NSDefaultRunLoopMode)
            except Exception:
                # Fallback: immediate removal
                _dismiss(None)

        except Exception:
            # Silently ignore toast rendering issues
            return

    # ObjC-exposed timer callback
    def dismissTimerFired_(self, timer):  # pragma: no cover - trivial bridge
        try:
            if ToastManager._current_view is not None:
                ToastManager._current_view.removeFromSuperview()
                ToastManager._current_view = None
        except Exception:
            ToastManager._current_view = None

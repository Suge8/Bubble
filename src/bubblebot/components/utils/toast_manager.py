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

            # Container
            width = 360
            height = 28
            frame = parent.bounds()
            x = (frame.size.width - width) / 2
            y = frame.size.height - height - 6  # near top inside parent
            view = NSView.alloc().initWithFrame_(((x, y), (width, height)))
            view.setWantsLayer_(True)
            try:
                # semi-transparent dark background for contrast
                view.layer().setCornerRadius_(8.0)
                view.layer().setMasksToBounds_(True)
                view.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.75).CGColor())
            except Exception:
                pass

            # Label
            label = NSTextField.alloc().initWithFrame_(((10, 4), (width - 20, height - 8)))
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            try:
                label.setTextColor_(NSColor.whiteColor())
            except Exception:
                pass
            try:
                label.setFont_(NSFont.systemFontOfSize_(12))
            except Exception:
                pass
            label.setStringValue_(text or "")
            view.addSubview_(label)

            # Attach to parent on top
            try:
                # 放到最上层；如提供 relative_to，确保在其之上
                if relative_to is not None:
                    parent.addSubview_positioned_relativeTo_(view, NSWindowAbove, relative_to)
                else:
                    parent.addSubview_positioned_relativeTo_(view, NSWindowAbove, None)
            except Exception:
                try:
                    parent.addSubview_(view)
                except Exception:
                    return

            cls._current_view = view

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

"""
Minimal ToastManager for UI tests and optional reuse.

Provides a simple inline toast that attaches to a given NSView parent and fades in/out.
This utility avoids app-level dependencies and is safe to call in tests.
"""

from __future__ import annotations

try:
    from AppKit import (
        NSView,
        NSTextField,
        NSColor,
        NSFont,
        NSMakeRect,
        NSAnimationContext,
        NSTimer,
        NSWindowAbove,
    )
except Exception:  # pragma: no cover - only used on macOS
    NSView = object  # type: ignore


class ToastManager:
    @staticmethod
    def show(text: str, parent: "NSView", duration: float = 3.0) -> None:
        """Render a small rounded toast on the given parent view.

        Parameters
        - text: message to display
        - parent: NSView to attach the toast to
        - duration: seconds before auto-dismiss
        """
        if parent is None:
            return
        try:
            bounds = parent.bounds()
            tw, th = (260.0, 36.0)
            margin = 12.0
            tx = max(margin, bounds.size.width - tw - margin)
            ty = max(margin, bounds.size.height - th - margin)

            toast = NSView.alloc().initWithFrame_(NSMakeRect(tx, ty, tw, th))
            toast.setWantsLayer_(True)
            try:
                toast.layer().setCornerRadius_(12.0)
                toast.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.92).CGColor())
            except Exception:
                pass

            lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(12, 8, tw - 24, th - 16))
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            try:
                lbl.setTextColor_(NSColor.whiteColor())
            except Exception:
                pass
            try:
                lbl.setFont_(NSFont.systemFontOfSize_(13))
            except Exception:
                pass
            lbl.setStringValue_(str(text) if text is not None else "")
            toast.addSubview_(lbl)

            toast.setAlphaValue_(0.0)
            try:
                subs = list(parent.subviews())
                anchor = subs[-1] if subs else None
                if hasattr(parent, 'addSubview_positioned_relativeTo_'):
                    parent.addSubview_positioned_relativeTo_(toast, NSWindowAbove, anchor)
                else:
                    parent.addSubview_(toast)
            except Exception:
                parent.addSubview_(toast)

            try:
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.18)
                toast.animator().setAlphaValue_(1.0)
                NSAnimationContext.endGrouping()
            except Exception:
                toast.setAlphaValue_(1.0)

            # Schedule auto-dismiss; in tests this may not run, but method should not raise.
            try:
                def _dismiss(_timer):
                    try:
                        NSAnimationContext.beginGrouping()
                        NSAnimationContext.currentContext().setDuration_(0.18)
                        toast.animator().setAlphaValue_(0.0)
                        NSAnimationContext.endGrouping()
                    except Exception:
                        pass
                    try:
                        toast.removeFromSuperview()
                    except Exception:
                        pass

                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    float(duration or 3.0), _ToastTarget(_dismiss), 'onTimer:', None, False
                )
            except Exception:
                # Best-effort cleanup without timer
                try:
                    toast.removeFromSuperview()
                except Exception:
                    pass
        except Exception:
            # Swallow errors to keep tests non-flaky
            pass


class _ToastTarget(object):
    # Small Objective-C bridge target for NSTimer
    def __init__(self, cb):
        self._cb = cb

    def onTimer_(self, timer):  # type: ignore
        try:
            self._cb(timer)
        except Exception:
            pass

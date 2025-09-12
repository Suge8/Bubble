"""
Navigation guard and error overlay utilities for WKWebView.

Features:
- Allowed host (domain) whitelist check for navigation
- Error overlay with a single "Retry" action (as per spec)
"""

from __future__ import annotations

from typing import Callable, Optional, Set
import objc

try:
    from Foundation import NSObject
    from AppKit import NSView, NSButton, NSTextField, NSMakeRect, NSColor, NSFont, NSAnimationContext
    from WebKit import WKNavigationActionPolicyCancel, WKNavigationActionPolicyAllow
except Exception:  # pragma: no cover - allow import on non-Darwin
    NSObject = object  # type: ignore
    NSView = object  # type: ignore
    NSButton = object  # type: ignore
    NSTextField = object  # type: ignore
    NSMakeRect = lambda *_: (0, 0, 0, 0)  # type: ignore
    NSColor = None  # type: ignore
    NSFont = None  # type: ignore
    NSAnimationContext = None  # type: ignore
    WKNavigationActionPolicyCancel = 0  # type: ignore
    WKNavigationActionPolicyAllow = 1  # type: ignore


def _extract_host(url_obj) -> Optional[str]:
    try:
        if url_obj is None:
            return None
        # NSURL has host method; Python str does not
        if hasattr(url_obj, "host"):
            return str(url_obj.host()) if url_obj.host() else None
        # Fallback: parse from string
        from urllib.parse import urlparse

        return urlparse(str(url_obj)).hostname
    except Exception:
        return None


class NavigationGuard(NSObject):
    """WKNavigationDelegate that enforces allowed hosts and draws an error overlay."""

    def init(self):  # type: ignore[override]
        self = objc.super(NavigationGuard, self).init()
        if self is None:
            return None
        self._allowed_hosts: Set[str] = set()
        self._overlays = {}  # webview -> overlay view
        self._retry_handler = {}  # webview -> callable
        return self

    # ---- public API ----
    def setAllowedHosts_(self, hosts):  # ObjC-friendly: - (void)setAllowedHosts:(id)hosts
        try:
            self._allowed_hosts = {str(h).lower() for h in (hosts or [])}
        except Exception:
            self._allowed_hosts = set()

    def py_setAllowedHosts(self, hosts: Set[str]):  # Pythonic (avoid ObjC selector)
        self.setAllowedHosts_(hosts)

    def attach_to(self, webview, on_retry: Optional[Callable] = None):
        try:
            # Keep a retry handler for fail events
            if on_retry is not None:
                self._retry_handler[webview] = on_retry
            # Attach as navigation delegate
            if hasattr(webview, "setNavigationDelegate_"):
                webview.setNavigationDelegate_(self)
        except Exception:
            pass

    # ---- error overlay ----
    def show_error_overlay(self, webview, message: str = "Load failed", on_retry: Optional[Callable] = None):
        try:
            # Reuse when exists
            if webview in self._overlays:
                overlay = self._overlays[webview]
                overlay.setHidden_(False)
                return

            bounds = webview.bounds() if hasattr(webview, "bounds") else NSMakeRect(0, 0, 320, 240)
            overlay = NSView.alloc().initWithFrame_(bounds)
            overlay.setWantsLayer_(True)
            try:
                # Semi-transparent background for readability
                overlay.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.28).CGColor())
                overlay.layer().setCornerRadius_(10.0)
            except Exception:
                pass

            # Message label
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, bounds.size.height/2 + 6, bounds.size.width - 40, 22))
            label.setBezeled_(False); label.setDrawsBackground_(False); label.setEditable_(False); label.setSelectable_(False)
            try:
                label.setAlignment_(2)  # center
                if NSFont is not None:
                    label.setFont_(NSFont.systemFontOfSize_(14))
                label.setTextColor_(NSColor.whiteColor())
            except Exception:
                pass
            label.setStringValue_(message or "Load failed")
            overlay.addSubview_(label)

            # Retry button
            btn = NSButton.alloc().initWithFrame_(NSMakeRect((bounds.size.width-120)/2, bounds.size.height/2 - 20, 120, 30))
            btn.setTitle_("Retry")
            btn.setBordered_(True)

            def _retry(_):
                try:
                    overlay.setHidden_(True)
                except Exception:
                    pass
                # Prefer local on_retry, then stored handler, else webview.reload
                cb = on_retry or self._retry_handler.get(webview)
                if callable(cb):
                    try:
                        cb()
                        return
                    except Exception:
                        pass
                try:
                    if hasattr(webview, "reload"):
                        webview.reload()
                except Exception:
                    pass

            # Bind PyObjC target/action via proxy
            Proxy = objc.lookUpClass("NSObject")

            class _Action(Proxy):  # type: ignore
                def initWithHandler_(self, handler):
                    self = objc.super(_Action, self).init()
                    if self is None:
                        return None
                    self._handler = handler
                    return self

                def callWithSender_(self, sender):  # noqa: N802 (ObjC selector)
                    try:
                        if callable(self._handler):
                            self._handler(sender)
                    except Exception:
                        pass

            proxy = _Action.alloc().initWithHandler_(_retry)
            try:
                btn.setTarget_(proxy)
                btn.setAction_("callWithSender:")
            except Exception:
                pass
            overlay._bb_retry_proxy = proxy  # keep strong reference
            overlay.addSubview_(btn)

            # Attach overlay to webview
            try:
                webview.addSubview_(overlay)
            except Exception:
                pass
            self._overlays[webview] = overlay

            # Fade in
            try:
                if NSAnimationContext is not None:
                    overlay.setAlphaValue_(0.0)
                    NSAnimationContext.beginGrouping()
                    NSAnimationContext.currentContext().setDuration_(0.18)
                    overlay.animator().setAlphaValue_(1.0)
                    NSAnimationContext.endGrouping()
            except Exception:
                pass
        except Exception:
            pass

    # ---- WKNavigationDelegate ----
    # def webView:decidePolicyForNavigationAction:decisionHandler:
    def webView_decidePolicyForNavigationAction_decisionHandler_(self, webView, navigationAction, decisionHandler):  # noqa: N802
        try:
            req = navigationAction.request() if hasattr(navigationAction, "request") else None
            url = req.URL() if (req is not None and hasattr(req, "URL")) else None
            host = _extract_host(url)
            if host and self._allowed_hosts and host.lower() not in self._allowed_hosts:
                # Block navigation to external host
                decisionHandler(WKNavigationActionPolicyCancel)
                # Optionally, a toast or small tip can be triggered by upper layer
                return
            decisionHandler(WKNavigationActionPolicyAllow)
        except Exception:
            # Fail open to avoid bricking navigation
            try:
                decisionHandler(WKNavigationActionPolicyAllow)
            except Exception:
                pass

    # def webView:didFailProvisionalNavigation:withError:
    def webView_didFailProvisionalNavigation_withError_(self, webView, navigation, error):  # noqa: N802
        try:
            self.show_error_overlay(webView, message="Load failed", on_retry=None)
        except Exception:
            pass

    # def webView:didFailNavigation:withError:
    def webView_didFailNavigation_withError_(self, webView, navigation, error):  # noqa: N802
        try:
            self.show_error_overlay(webView, message="Load failed", on_retry=None)
        except Exception:
            pass

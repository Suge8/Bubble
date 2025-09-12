"""
Suspend policy and WebView suspend/resume helpers.

This module provides a small, testable policy layer for deciding when a
window/webview should be suspended due to inactivity, and helpers to suspend
and resume a WKWebView while preserving minimal session data.

Design goals:
- Pure Python timing/state for easy unit testing
- Defensive integration with PyObjC (all Cocoa calls wrapped in try/except)
- Idempotent helpers: calling suspend/resume multiple times is safe
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
import time


@dataclass
class _WindowState:
    last_activity_ts: float = field(default_factory=lambda: time.time())
    suspended: bool = False


class SuspendPolicy:
    """Track inactivity and decide when to suspend a window/webview.

    Minutes can be set to 0 or None to disable suspension.
    """

    def __init__(self, minutes: Optional[int] = 30) -> None:
        self._minutes: Optional[int] = None
        self._states: Dict[str, _WindowState] = {}
        self.set_timeout_minutes(minutes)

    # ---- configuration ----
    def set_timeout_minutes(self, minutes: Optional[int]) -> None:
        if minutes is None:
            self._minutes = None
            return
        try:
            m = int(minutes)
            if m <= 0:
                # 0 or negative disables suspension
                self._minutes = None
            else:
                self._minutes = m
        except Exception:
            # Invalid input disables suspension rather than crashing
            self._minutes = None

    def get_timeout_minutes(self) -> Optional[int]:
        return self._minutes

    # ---- activity tracking ----
    def note_window_activity(self, window_id: Optional[str]) -> None:
        if not window_id:
            return
        st = self._states.get(window_id)
        if st is None:
            st = _WindowState()
            self._states[window_id] = st
        st.last_activity_ts = time.time()

    def mark_suspended(self, window_id: Optional[str]) -> None:
        if not window_id:
            return
        st = self._states.get(window_id)
        if st is None:
            st = _WindowState()
            self._states[window_id] = st
        st.suspended = True

    def mark_resumed(self, window_id: Optional[str]) -> None:
        if not window_id:
            return
        st = self._states.get(window_id)
        if st is None:
            st = _WindowState()
            self._states[window_id] = st
        st.suspended = False
        st.last_activity_ts = time.time()

    # ---- decision ----
    def should_suspend(self, window_id: Optional[str]) -> bool:
        """Return True if the window should be suspended now.

        Rules:
        - If suspension is disabled: False
        - If no state exists yet: False (not enough info)
        - If already suspended: False (idempotent)
        - Otherwise: inactive for >= minutes threshold
        """
        if self._minutes is None or not window_id:
            return False
        st = self._states.get(window_id)
        if st is None:
            return False
        if st.suspended:
            return False
        try:
            idle_sec = time.time() - float(st.last_activity_ts)
        except Exception:
            return False
        return idle_sec >= (self._minutes * 60)


# ---- WKWebView suspend/resume helpers ----

def _get_current_url(webview) -> Optional[str]:
    try:
        # WKWebView URL retrieval
        url = webview.URL() if hasattr(webview, "URL") else None
        if url is None and hasattr(webview, "url"):
            url = webview.url()
        if url is None:
            return None
        try:
            # NSURL to str
            return str(url.absoluteString())
        except Exception:
            return str(url)
    except Exception:
        return None


def suspend_webview(webview, ai_window) -> None:
    """Lightweight suspend: capture URL and show a lightweight blank page.

    - Store the last URL into ai_window.session_data["_suspend_last_url"].
    - Attempt to stop ongoing loads and replace content with a minimal blank.
    - Idempotent and defensive against missing APIs.
    """
    if webview is None:
        return
    try:
        last_url = _get_current_url(webview)
        if ai_window is not None:
            try:
                ai_window.set_session_data("_suspend_last_url", last_url)
            except Exception:
                # Fallback if helper not available
                try:
                    if getattr(ai_window, "session_data", None) is not None:
                        ai_window.session_data["_suspend_last_url"] = last_url
                except Exception:
                    pass
    except Exception:
        pass

    # Stop and replace content with about:blank like content
    try:
        if hasattr(webview, "stopLoading"):
            webview.stopLoading()
    except Exception:
        pass
    try:
        # Prefer displaying a blank lightweight HTML to free resources
        if hasattr(webview, "loadHTMLString_baseURL_"):
            webview.loadHTMLString_baseURL_("<html><body style='background:transparent'></body></html>", None)
    except Exception:
        pass


def resume_webview(webview, ai_window) -> None:
    """Resume a previously suspended webview by reloading last URL if needed."""
    if webview is None:
        return
    last_url = None
    try:
        if ai_window is not None:
            last_url = ai_window.get_session_data("_suspend_last_url", None)
            if last_url is None:
                # Fallback direct access
                last_url = getattr(getattr(ai_window, "session_data", {}), "get", lambda *_: None)("_suspend_last_url")
    except Exception:
        last_url = None

    # If current URL already valid, do nothing
    try:
        cur = _get_current_url(webview)
    except Exception:
        cur = None

    if not last_url or (cur and cur != "" and cur != "about:blank"):
        # Nothing to do or already on a real page
        return

    # Reload last URL
    try:
        from Foundation import NSURL, NSURLRequest
        if hasattr(webview, "loadRequest_"):
            req = NSURLRequest.requestWithURL_(NSURL.URLWithString_(last_url))
            webview.loadRequest_(req)
            return
    except Exception:
        pass

    # Fallback: try reload
    try:
        if hasattr(webview, "reload"):
            webview.reload()
    except Exception:
        pass


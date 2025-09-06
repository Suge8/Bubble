import platform
import pytest


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="AppKit required on macOS")
def test_page_threshold_toast_trigger(monkeypatch):
    from bubblebot.app import AppDelegate

    delegate = AppDelegate.alloc().init()
    calls = []

    def fake_toast(msg, duration=3.0):
        calls.append(msg)

    monkeypatch.setattr(delegate, 'show_toast', fake_toast)

    # 5 -> 6 triggers once (total pages > 5)
    delegate.notify_page_count_changed(5, 6)
    assert len(calls) == 1

    # staying >5 does not trigger repeatedly
    delegate.notify_page_count_changed(6, 7)
    assert len(calls) == 1

    # Drop back to <=5 then cross to >5 triggers again
    delegate.notify_page_count_changed(7, 5)
    delegate.notify_page_count_changed(5, 6)
    assert len(calls) == 2

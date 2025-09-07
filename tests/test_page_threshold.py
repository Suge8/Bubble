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

    # 4 -> 5 triggers once (crossing to >4)
    delegate.notify_page_count_changed(4, 5)
    assert len(calls) == 1

    # staying >4 does not trigger repeatedly
    delegate.notify_page_count_changed(5, 6)
    assert len(calls) == 1

    # Drop back to <=4 then cross to >4 triggers again
    delegate.notify_page_count_changed(6, 4)
    delegate.notify_page_count_changed(4, 5)
    assert len(calls) == 2

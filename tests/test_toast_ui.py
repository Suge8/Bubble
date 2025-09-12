import platform
import pytest


@pytest.mark.skipif(platform.system().lower() != "darwin", reason="AppKit required on macOS")
def test_toast_manager_show_no_exception():
    from AppKit import NSView, NSMakeRect
    from bubble.components.utils.toast_manager import ToastManager

    parent = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 80))
    # Should not raise
    ToastManager.show(text="测试提示", parent=parent, duration=0.2)

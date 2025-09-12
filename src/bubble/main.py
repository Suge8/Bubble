# Python libraries
import argparse
import sys
import signal
import os as _os
import builtins as _builtins
from Foundation import NSBundle

from AppKit import NSApplication, NSApp, NSApplicationActivationPolicyRegular

# Local libraries.
from .constants import (
    APP_TITLE,
    LAUNCHER_TRIGGER,
    LAUNCHER_TRIGGER_MASK,
    PERMISSION_CHECK_EXIT,
)
from .app import (
    AppDelegate,
    NSApplication
)
from .launcher import (
    check_permissions,
    ensure_accessibility_permissions,
)
from .health_checks import (
    health_check_decorator
)
from .components import (
    HomepageManager,
    NavigationController,
    MultiWindowManager,
    PlatformManager
)

# 日志精简（默认隐藏 DEBUG 行；BB_DEBUG=1 时显示）
_orig_print_main = _builtins.print
def _main_print(*args, **kwargs):
    if _os.environ.get('BB_DEBUG') == '1':
        return _orig_print_main(*args, **kwargs)
    if not args:
        return
    s = str(args[0])
    if s.startswith('DEBUG:'):
        return
    return _orig_print_main(*args, **kwargs)
print = _main_print

# 统一使用 NSApp.run() 的事件循环
exit_requested = False  # 为向后兼容保留（不再主动轮询）

def signal_handler(sig, frame):
    """保留简单的退出处理；开发期直接关闭终端亦可结束进程。"""
    print(f"\n检测到信号 {sig}，正在退出 Bubble...")
    try:
        app = NSApplication.sharedApplication()
        app.terminate_(None)
    except Exception:
        # 无法优雅退出时直接中断
        import os
        os._exit(0)


def _is_packaged_app() -> bool:
    """检测是否运行在打包的 .app 环境中。"""
    try:
        if getattr(sys, 'frozen', False):
            return True
        bundle = NSBundle.mainBundle()
        if bundle is not None:
            bp = str(bundle.bundlePath())
            return bool(bp and bp.endswith('.app'))
    except Exception:
        pass
    return False

# Main executable for running the application from the command line.
@health_check_decorator
def main():
    print("DEBUG: main() 函数开始执行")
    parser = argparse.ArgumentParser(
        description=f"macOS {APP_TITLE} Overlay App - Dedicated window that can be summoned and dismissed with your keyboard shortcut."
    )
    # Autolauncher flags removed (3.1)
    parser.add_argument(
        "--check-permissions",
        action="store_true",
        help="Check Accessibility permissions only"
    )
    parser.add_argument(
        "--capturable",
        action="store_true",
        help="Dev only: make windows capturable in screen recording"
    )
    args = parser.parse_args()
    
    # 设置信号处理器：仅在终端开发模式下响应 Ctrl+C；打包版忽略 Ctrl+C
    try:
        if _is_packaged_app():
            # 打包 .app：忽略 SIGINT，避免从终端运行时误触 Ctrl+C 退出
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        else:
            # 仅当交互式终端时启用 Ctrl+C 退出
            if sys.stdin and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                signal.signal(signal.SIGINT, signal_handler)
            else:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
        # 依旧响应 SIGTERM 以支持系统关停
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass

    # Autolauncher actions removed (3.1)

    if args.check_permissions:
        is_trusted = check_permissions(ask=False)
        print("Permissions granted:", is_trusted)
        sys.exit(0 if is_trusted else PERMISSION_CHECK_EXIT)

    # 暂时跳过权限检查，避免阻塞
    print("DEBUG: 跳过权限检查，继续启动应用...")
    # check_permissions()
    # # Ensure permissions before proceeding
    # ensure_accessibility_permissions()

    # Default behavior: run the app and inform user of startup options
    print()
    print(f"Starting macOS {APP_TITLE} overlay.")
    # Autolauncher messaging removed (3.1)
    
    # Dev-only: allow screen/window recording to capture our windows
    # by lowering level and allowing window sharing (opt-in via flag).
    if args.capturable:
        try:
            _os.environ["BB_CAPTURABLE"] = "1"
            print("DEBUG: Capturable mode enabled via --capturable")
        except Exception:
            pass

    # 初始化应用组件
    print("DEBUG: 开始初始化应用组件...")
    homepage_manager = HomepageManager.alloc().init()
    navigation_controller = NavigationController.alloc().init()
    multiwindow_manager = MultiWindowManager.alloc().init()
    platform_manager = PlatformManager()
    print("DEBUG: 应用组件初始化完成")

    # 创建应用和委托
    print("DEBUG: 创建应用和委托...")
    app = NSApplication.sharedApplication()
    # 预先设置为前台 App，避免启动阶段菜单栏为灰色、无法激活
    try:
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    except Exception:
        pass
    delegate = AppDelegate.alloc().init()
    print(f"DEBUG: 应用对象创建完成: {app}")
    print(f"DEBUG: 委托对象创建完成: {delegate}")

    # 设置组件依赖关系
    delegate.setHomepageManager_(homepage_manager)
    delegate.setNavigationController_(navigation_controller)
    delegate.setMultiwindowManager_(multiwindow_manager)
    delegate.setPlatformManager_(platform_manager)
    navigation_controller.set_app_delegate(delegate)
    print("DEBUG: 组件依赖关系设置完成")

    # 启动应用
    app.setDelegate_(delegate)
    print("DEBUG: 应用委托设置完成")

    print("Bubble 初始化完成，启动主页...")

    # 统一使用 Cocoa 事件循环（生产/开发一致）
    app.run()

if __name__ == "__main__":
    # Execute the decorated main function.
    main()

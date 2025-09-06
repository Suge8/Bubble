# Python libraries
import argparse
import sys
import signal

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
    install_startup,
    uninstall_startup
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
import os as _os
import builtins as _builtins
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
    print(f"\n检测到信号 {sig}，正在退出 BubbleBot...")
    try:
        app = NSApplication.sharedApplication()
        app.terminate_(None)
    except Exception:
        # 无法优雅退出时直接中断
        import os
        os._exit(0)

# Main executable for running the application from the command line.
@health_check_decorator
def main():
    print("DEBUG: main() 函数开始执行")
    parser = argparse.ArgumentParser(
        description=f"macOS {APP_TITLE} Overlay App - Dedicated window that can be summoned and dismissed with your keyboard shortcut."
    )
    parser.add_argument(
        "--install-startup",
        action="store_true",
        help=f"Install {APP_TITLE} to run at login",
    )
    parser.add_argument(
        "--uninstall-startup",
        action="store_true",
        help=f"Uninstall {APP_TITLE} from running at login",
    )
    parser.add_argument(
        "--check-permissions",
        action="store_true",
        help="Check Accessibility permissions only"
    )
    args = parser.parse_args()
    
    # 设置信号处理器（可选）。生产/开发均统一使用 NSApp.run()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.install_startup:
        install_startup()
        return

    if args.uninstall_startup:
        uninstall_startup()
        return

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
    print()
    print(f"To run at login, use:      {APP_TITLE.lower()} --install-startup")
    print(f"To remove from login, use: {APP_TITLE.lower()} --uninstall-startup")
    print()
    
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

    print("BubbleBot初始化完成，启动主页...")

    # 统一使用 Cocoa 事件循环（生产/开发一致）
    app.run()

if __name__ == "__main__":
    # Execute the decorated main function.
    main()

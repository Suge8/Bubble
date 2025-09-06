#!/usr/bin/env python3
"""
测试 Ctrl+C 退出功能的简化版本
在新终端中运行此脚本来测试退出功能是否正常工作
"""

import sys
import signal
import os
import threading
import time
sys.path.insert(0, 'src')

# 全局标志，用于控制应用退出
should_exit = False

def signal_handler(sig, frame):
    """处理终端 Ctrl+C 信号"""
    global should_exit
    print(f"\n✅ 收到终端信号 {sig}，正在退出...")
    should_exit = True
    # 强制退出，不等待 NSApplication
    os._exit(0)

# 必须在导入 AppKit 之前设置信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 设置信号为可中断模式
signal.alarm(0)

from AppKit import *
from Foundation import NSObject
import objc

class QuickTestDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("✅ 快速测试应用启动")
        print("📋 测试说明：")
        print("   - 这是一个简化的测试版本")
        print("   - 按 Ctrl+C 应该能立即退出")
        print("   - 按 Cmd+Q 也能退出")
        print("   - 如果卡住，说明退出机制有问题")
        
        # 创建简单窗口
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(300, 300, 400, 200),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("BubbleBot 退出测试")
        
        # 添加标签
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 80, 300, 40))
        label.setStringValue_("按 Ctrl+C 或 Cmd+Q 测试退出功能")
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(NSTextAlignmentCenter)
        window.contentView().addSubview_(label)
        
        # 显示窗口
        NSApp.activateIgnoringOtherApps_(True)
        window.makeKeyAndOrderFront_(None)
        
        # 启动自动退出计时器（10秒后自动退出）
        def auto_exit():
            time.sleep(10)
            print("\n⏰ 10秒测试时间到，自动退出")
            os._exit(0)
        
        threading.Thread(target=auto_exit, daemon=True).start()
        print("⏰ 10秒后将自动退出")

def main():
    print("🚀 启动退出功能测试...")
    print("💡 提示：在新终端中运行，测试 Ctrl+C 是否能正常退出")
    
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    
    delegate = QuickTestDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n✅ KeyboardInterrupt 异常捕获成功")
        os._exit(0)
    except Exception as e:
        print(f"\n❌ 出现异常: {e}")
        os._exit(1)

if __name__ == "__main__":
    main()
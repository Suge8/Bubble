#!/usr/bin/env python3
"""
真正可以响应终端 Ctrl+C 的测试版本
使用定时器方式而不是 app.run() 阻塞方式
"""

import sys
import signal
import os
import time
import threading
sys.path.insert(0, 'src')

# 退出标志
exit_requested = False

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global exit_requested
    print(f"\n✅ 收到信号 {sig}，准备退出...")
    exit_requested = True

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

from AppKit import *
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode
import objc

class NonBlockingDelegate(NSObject):
    def __init__(self):
        objc.super(NonBlockingDelegate, self).__init__()
        self.window = None
        self.timer = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("🔧 应用启动，创建窗口...")
        
        # 创建窗口
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, 500, 300),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setTitle_("可响应 Ctrl+C 的测试窗口")
        
        # 添加标签
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 120, 400, 60))
        label.setStringValue_("✅ 测试窗口\n现在在终端按 Ctrl+C 应该能正常退出")
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(NSTextAlignmentCenter)
        self.window.contentView().addSubview_(label)
        
        # 显示窗口
        NSApp.activateIgnoringOtherApps_(True)
        self.window.makeKeyAndOrderFront_(None)
        
        # 创建定时器，定期检查退出标志
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.1,  # 每100ms检查一次
            self,
            'checkExitStatus:',
            None,
            True
        )
        
        print("📋 窗口已显示，现在可以在终端尝试 Ctrl+C")
    
    def checkExitStatus_(self, timer):
        """定期检查是否需要退出"""
        global exit_requested
        if exit_requested:
            print("🔄 检测到退出请求，正在清理...")
            if self.timer:
                self.timer.invalidate()
            NSApp.terminate_(None)

def main():
    global exit_requested
    
    print("🚀 启动非阻塞测试...")
    print("💡 这个版本应该能响应终端的 Ctrl+C")
    
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    
    delegate = NonBlockingDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    # 启动自动退出定时器
    def auto_exit():
        global exit_requested
        time.sleep(15)  # 15秒后自动退出
        if not exit_requested:
            print("\n⏰ 15秒测试时间到，自动退出")
            exit_requested = True
            time.sleep(0.2)  # 等待检查循环
            os._exit(0)
    
    threading.Thread(target=auto_exit, daemon=True).start()
    
    try:
        # 不使用 app.run()，而是手动运行事件循环
        print("📡 启动事件循环...")
        while not exit_requested:
            # 处理事件，但不阻塞
            NSApp.activateIgnoringOtherApps_(True)
            run_loop = NSRunLoop.currentRunLoop()
            run_loop.runMode_beforeDate_(NSDefaultRunLoopMode, 
                                       NSDate.dateWithTimeIntervalSinceNow_(0.1))
            
            # 检查退出条件
            if exit_requested:
                break
                
        print("✅ 正常退出事件循环")
        
    except KeyboardInterrupt:
        print("\n✅ 捕获到 KeyboardInterrupt")
        exit_requested = True
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        exit_requested = True
    
    print("🔚 程序结束")
    os._exit(0)

if __name__ == "__main__":
    main()
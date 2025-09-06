#!/usr/bin/env python3
"""
详细调试版本 - 找出窗口不显示和图标问题的根本原因
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
from WebKit import *
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode, NSDate
import objc

class DetailedDebugDelegate(NSObject):
    def __init__(self):
        objc.super(DetailedDebugDelegate, self).__init__()
        self.window = None
        self.timer = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("=" * 60)
        print("🔧 开始详细调试 BubbleBot 窗口和图标问题")
        print("=" * 60)
        
        # 1. 检查应用状态
        print("\n1️⃣ 检查应用初始状态:")
        print(f"   - NSApp: {NSApp}")
        print(f"   - 激活策略: {NSApp.activationPolicy()}")
        print(f"   - 是否激活: {NSApp.isActive()}")
        print(f"   - 是否隐藏: {NSApp.isHidden()}")
        
        # 2. 设置应用图标 - 尝试多种方法
        print("\n2️⃣ 设置应用图标:")
        self._set_application_icon()
        
        # 3. 获取屏幕信息
        print("\n3️⃣ 屏幕信息:")
        main_screen = NSScreen.mainScreen()
        print(f"   - 主屏幕: {main_screen}")
        if main_screen:
            frame = main_screen.frame()
            visible_frame = main_screen.visibleFrame()
            print(f"   - 屏幕尺寸: {frame.size.width} x {frame.size.height}")
            print(f"   - 可见区域: {visible_frame}")
        
        # 4. 创建窗口 - 使用安全的位置和设置
        print("\n4️⃣ 创建窗口:")
        self._create_window()
        
        # 5. 显示窗口
        print("\n5️⃣ 显示窗口:")
        self._show_window()
        
        # 6. 验证窗口状态
        print("\n6️⃣ 验证窗口状态:")
        self._verify_window_status()
        
        # 7. 启动检查定时器
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            2.0, self, 'periodicCheck:', None, True
        )
        
        print("\n✅ 调试初始化完成")
        print("📋 请观察:")
        print("   - Dock 中是否有 BubbleBot 图标？")
        print("   - 屏幕上是否有任何窗口？")
        print("   - 如果没有，查看上面的调试信息")
    
    def _set_application_icon(self):
        """设置应用图标 - 多种尝试"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试多个可能的路径
        icon_paths = [
            os.path.join(current_dir, "src/bubblebot/logo/icon.icns"),
            os.path.join(current_dir, "src/bubblebot/logo/logo_white.png"),
            os.path.join(current_dir, "src/bubblebot/logo/logo_black.png"),
        ]
        
        for i, icon_path in enumerate(icon_paths, 1):
            print(f"   尝试 {i}: {icon_path}")
            if os.path.exists(icon_path):
                print(f"     ✅ 文件存在")
                try:
                    app_icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
                    if app_icon:
                        NSApp.setApplicationIconImage_(app_icon)
                        print(f"     ✅ 图标设置成功")
                        break
                    else:
                        print(f"     ❌ 无法创建 NSImage")
                except Exception as e:
                    print(f"     ❌ 设置失败: {e}")
            else:
                print(f"     ❌ 文件不存在")
        else:
            print("   ⚠️ 所有图标路径都失败，使用默认图标")
    
    def _create_window(self):
        """创建窗口 - 使用保守设置"""
        # 使用屏幕中央位置
        main_screen = NSScreen.mainScreen()
        if main_screen:
            screen_frame = main_screen.visibleFrame()
            # 计算屏幕中央位置
            x = (screen_frame.size.width - 550) / 2 + screen_frame.origin.x
            y = (screen_frame.size.height - 580) / 2 + screen_frame.origin.y
        else:
            x, y = 200, 200  # 默认位置
        
        window_rect = NSMakeRect(x, y, 550, 580)
        print(f"   窗口位置: x={x}, y={y}, w=550, h=580")
        
        # 先尝试标准窗口，确保能看见
        print("   使用标准窗口样式（调试模式）")
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        if self.window:
            print("   ✅ 窗口对象创建成功")
            self.window.setTitle_("BubbleBot 调试窗口")
            
            # 设置窗口属性
            self.window.setLevel_(NSNormalWindowLevel)  # 先用普通级别
            self.window.setOpaque_(True)  # 不透明，确保可见
            self.window.setBackgroundColor_(NSColor.whiteColor())
            
            # 添加简单内容
            content_view = self.window.contentView()
            
            # 添加大号标签
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 250, 450, 100))
            label.setStringValue_("🔧 BubbleBot 调试窗口\n\n如果你能看到这个窗口，\n说明基本显示功能正常！")
            label.setEditable_(False)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setAlignment_(NSTextAlignmentCenter)
            label.setFont_(NSFont.systemFontOfSize_(16))
            content_view.addSubview_(label)
            
            print("   ✅ 窗口内容设置完成")
        else:
            print("   ❌ 窗口对象创建失败")
    
    def _show_window(self):
        """显示窗口"""
        if not self.window:
            print("   ❌ 窗口对象为空，无法显示")
            return
        
        print("   激活应用...")
        NSApp.activateIgnoringOtherApps_(True)
        
        print("   显示窗口...")
        self.window.makeKeyAndOrderFront_(None)
        
        print("   ✅ 显示命令已执行")
    
    def _verify_window_status(self):
        """验证窗口状态"""
        if not self.window:
            print("   ❌ 窗口对象为空")
            return
        
        print(f"   - 窗口是否可见: {self.window.isVisible()}")
        print(f"   - 窗口是否为关键窗口: {self.window.isKeyWindow()}")
        print(f"   - 窗口是否为主窗口: {self.window.isMainWindow()}")
        print(f"   - 窗口透明度: {self.window.alphaValue()}")
        print(f"   - 窗口级别: {self.window.level()}")
        print(f"   - 窗口框架: {self.window.frame()}")
        
        print(f"   - 应用是否激活: {NSApp.isActive()}")
        print(f"   - 应用是否隐藏: {NSApp.isHidden()}")
    
    def periodicCheck_(self, timer):
        """定期检查"""
        global exit_requested
        if exit_requested:
            print("🔄 检测到退出请求，正在关闭...")
            if self.timer:
                self.timer.invalidate()
            NSApp.terminate_(None)
            return
        
        # 每2秒输出一次状态
        print(f"\n⏰ 定期检查 - 窗口可见: {self.window.isVisible() if self.window else 'N/A'}")

def main():
    global exit_requested
    
    print("🚀 启动详细调试模式...")
    print("💡 这个版本会显示所有调试信息，帮助找出问题")
    
    # 设置应用
    app = NSApplication.sharedApplication()
    print(f"🔧 NSApplication 对象: {app}")
    
    # 设置激活策略
    print("🔧 设置激活策略...")
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    print(f"   激活策略设置为: {app.activationPolicy()}")
    
    # 创建委托
    delegate = DetailedDebugDelegate.alloc().init()
    app.setDelegate_(delegate)
    print(f"🔧 委托对象: {delegate}")
    
    # 启动自动退出
    def auto_exit():
        global exit_requested
        time.sleep(60)  # 60秒后自动退出
        if not exit_requested:
            print("\n⏰ 60秒调试时间到，自动退出")
            exit_requested = True
    
    threading.Thread(target=auto_exit, daemon=True).start()
    
    try:
        print("🔧 启动事件循环...")
        
        # 手动触发 applicationDidFinishLaunching
        print("🔧 手动触发 applicationDidFinishLaunching...")
        delegate.applicationDidFinishLaunching_(None)
        
        # 手动事件循环
        while not exit_requested:
            run_loop = NSRunLoop.currentRunLoop()
            run_loop.runMode_beforeDate_(NSDefaultRunLoopMode, 
                                       NSDate.dateWithTimeIntervalSinceNow_(0.1))
            if exit_requested:
                break
                
        print("✅ 正常退出调试")
        
    except KeyboardInterrupt:
        print("\n✅ 捕获到 KeyboardInterrupt")
        exit_requested = True
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        exit_requested = True
    
    print("🔚 调试结束")

if __name__ == "__main__":
    main()
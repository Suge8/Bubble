#!/usr/bin/env python3
"""
测试窗口显示和 logo 的完整版本
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

class WindowTestDelegate(NSObject):
    def __init__(self):
        objc.super(WindowTestDelegate, self).__init__()
        self.window = None
        self.webview = None
        self.timer = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("🎈 开始测试 BubbleBot 窗口显示...")
        
        # 设置应用图标
        print("📷 设置应用图标...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "src/bubblebot/logo/icon.icns")
        if os.path.exists(icon_path):
            app_icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
            if app_icon:
                NSApp.setApplicationIconImage_(app_icon)
                print(f"✅ 应用图标设置成功")
            else:
                print(f"❌ 无法加载图标文件")
        else:
            print(f"⚠️ 图标文件不存在: {icon_path}")
        
        # 创建无边框浮动窗口（原始设计）
        print("🔧 创建无边框浮动窗口...")
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(500, 200, 550, 580),
            NSBorderlessWindowMask | NSResizableWindowMask,  # 无边框
            NSBackingStoreBuffered,
            False
        )
        
        # 设置窗口属性
        self.window.setLevel_(NSFloatingWindowLevel)  # 浮动级别
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces |
            NSWindowCollectionBehaviorStationary
        )
        
        # 透明窗口设置
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        
        # 防止出现在截图中
        self.window.setSharingType_(NSWindowSharingNone)
        
        # 创建圆角内容视图
        content_view = NSView.alloc().initWithFrame_(self.window.contentView().bounds())
        content_view.setWantsLayer_(True)
        content_view.layer().setCornerRadius_(15.0)
        content_view.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
        self.window.setContentView_(content_view)
        
        # 创建 WebView
        config = WKWebViewConfiguration.alloc().init()
        config.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
        
        webview_bounds = content_view.bounds()
        # 为拖拽区域留出空间
        drag_height = 30
        webview_frame = NSMakeRect(0, 0, webview_bounds.size.width, webview_bounds.size.height - drag_height)
        
        self.webview = WKWebView.alloc().initWithFrame_configuration_(webview_frame, config)
        self.webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 设置用户代理
        safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        self.webview.setCustomUserAgent_(safari_user_agent)
        
        content_view.addSubview_(self.webview)
        
        # 创建拖拽区域
        drag_area = NSView.alloc().initWithFrame_(
            NSMakeRect(0, webview_bounds.size.height - drag_height, webview_bounds.size.width, drag_height)
        )
        drag_area.setWantsLayer_(True)
        drag_area.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.9, 0.9, 0.9, 0.8).CGColor())
        content_view.addSubview_(drag_area)
        
        # 添加关闭按钮
        close_button = NSButton.alloc().initWithFrame_(NSMakeRect(5, 5, 20, 20))
        close_button.setBordered_(False)
        close_button.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("xmark.circle.fill", None))
        close_button.setTarget_(self)
        close_button.setAction_("closeWindow:")
        drag_area.addSubview_(close_button)
        
        # 添加标题标签
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(30, 5, 200, 20))
        title_label.setStringValue_("🎈 BubbleBot - 测试版")
        title_label.setEditable_(False)
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setFont_(NSFont.systemFontOfSize_(12))
        drag_area.addSubview_(title_label)
        
        # 加载测试内容
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>BubbleBot 窗口显示测试</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0; 
                    padding: 30px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    min-height: calc(100vh - 60px);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }
                h1 { font-size: 2em; margin-bottom: 15px; }
                .status {
                    background: rgba(76, 217, 100, 0.2);
                    border: 1px solid rgba(76, 217, 100, 0.5);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                .feature {
                    background: rgba(255,255,255,0.1);
                    padding: 10px;
                    border-radius: 8px;
                    margin: 10px 0;
                    text-align: left;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="status">
                    ✅ BubbleBot 窗口显示成功！
                </div>
                <h1>🎈 BubbleBot 测试</h1>
                
                <div class="feature">🔹 无边框透明窗口 - 已实现</div>
                <div class="feature">🔹 浮动级别始终置顶 - 已实现</div>
                <div class="feature">🔹 圆角设计 - 已实现</div>
                <div class="feature">🔹 拖拽区域 - 已实现</div>
                <div class="feature">🔹 应用图标 - 已设置</div>
                <div class="feature">🔹 Ctrl+C 退出 - 已修复</div>
                
                <p style="font-size: 14px; margin-top: 20px; opacity: 0.9;">
                    如果你能看到这个美观的悬浮窗口，<br>
                    说明窗口显示问题已经完全解决！
                </p>
            </div>
        </body>
        </html>
        """
        
        self.webview.loadHTMLString_baseURL_(html_content, None)
        
        # 显示窗口
        print("🚀 显示窗口...")
        NSApp.activateIgnoringOtherApps_(True)
        self.window.makeKeyAndOrderFront_(None)
        
        # 创建定时器检查退出状态
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.5, self, 'checkExitStatus:', None, True
        )
        
        print("✅ 窗口显示完成！")
        print("📋 检查项目：")
        print("   - 是否能看到无边框的悬浮窗口？")
        print("   - 窗口是否有圆角效果？")
        print("   - 应用图标是否正确显示在 Dock 中？")
        print("   - 拖拽区域是否可以移动窗口？")
        print("   - Ctrl+C 是否能正常退出？")
    
    def checkExitStatus_(self, timer):
        """检查退出状态"""
        global exit_requested
        if exit_requested:
            print("🔄 检测到退出请求，正在关闭...")
            if self.timer:
                self.timer.invalidate()
            NSApp.terminate_(None)
    
    def closeWindow_(self, sender):
        """关闭窗口"""
        print("🔄 用户点击关闭按钮")
        global exit_requested
        exit_requested = True

def main():
    global exit_requested
    
    print("🚀 启动 BubbleBot 窗口显示测试...")
    print("💡 这个版本测试原始设计的窗口显示效果")
    
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    
    delegate = WindowTestDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    # 启动自动退出定时器
    def auto_exit():
        global exit_requested
        time.sleep(30)  # 30秒后自动退出
        if not exit_requested:
            print("\n⏰ 30秒测试时间到，自动退出")
            exit_requested = True
            time.sleep(0.5)
            os._exit(0)
    
    threading.Thread(target=auto_exit, daemon=True).start()
    
    try:
        # 手动事件循环
        while not exit_requested:
            run_loop = NSRunLoop.currentRunLoop()
            run_loop.runMode_beforeDate_(NSDefaultRunLoopMode, 
                                       NSDate.dateWithTimeIntervalSinceNow_(0.1))
            if exit_requested:
                break
                
        print("✅ 正常退出测试")
        
    except KeyboardInterrupt:
        print("\n✅ 捕获到 KeyboardInterrupt")
        exit_requested = True
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        exit_requested = True
    
    print("🔚 测试结束")
    os._exit(0)

if __name__ == "__main__":
    main()
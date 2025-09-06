#!/usr/bin/env python3
"""
BubbleBot 窗口显示修复版本
临时修复版本，专门解决窗口不显示的问题
"""

import sys
sys.path.insert(0, 'src')

from AppKit import *
from WebKit import *
from Foundation import NSObject
import objc

class FixedAppDelegate(NSObject):
    def __init__(self):
        objc.super(FixedAppDelegate, self).__init__()
        self.window = None
        self.webview = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("🔧 开始创建修复版BubbleBot窗口...")
        
        # 设置应用激活策略
        print("🔧 设置应用激活策略...")
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
        # 创建窗口
        print("🔧 创建主窗口...")
        window_rect = NSMakeRect(100, 100, 550, 580)  # 改变位置，避免可能的位置问题
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,  # 使用标准窗口样式
            NSBackingStoreBuffered,
            False
        )
        
        # 设置窗口基本属性
        self.window.setTitle_("BubbleBot - 修复版")
        self.window.setLevel_(NSNormalWindowLevel)  # 使用正常窗口级别
        
        # 不设置透明度，使用标准背景
        self.window.setOpaque_(True)
        self.window.setBackgroundColor_(NSColor.whiteColor())
        
        # 创建WebView配置
        print("🔧 创建WebView...")
        config = WKWebViewConfiguration.alloc().init()
        config.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
        
        # 创建WebView
        content_bounds = self.window.contentView().bounds()
        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            content_bounds,
            config
        )
        self.webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 设置用户代理
        safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        self.webview.setCustomUserAgent_(safari_user_agent)
        
        # 将WebView添加到窗口
        self.window.contentView().addSubview_(self.webview)
        
        # 加载简单的HTML内容
        print("🔧 加载HTML内容...")
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>BubbleBot 修复版</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    min-height: 100vh;
                    box-sizing: border-box;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    max-width: 400px;
                    margin: 0 auto;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                h1 { 
                    color: white; 
                    margin-bottom: 20px; 
                    font-size: 2.5em;
                    margin-top: 0;
                }
                p { 
                    color: rgba(255,255,255,0.9); 
                    line-height: 1.6; 
                    margin-bottom: 30px;
                }
                textarea {
                    width: 100%;
                    height: 120px;
                    padding: 15px;
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    resize: vertical;
                    outline: none;
                    box-sizing: border-box;
                    background: rgba(255,255,255,0.9);
                    color: #333;
                }
                textarea:focus {
                    background: rgba(255,255,255,1);
                }
                .success {
                    background: rgba(76, 217, 100, 0.2);
                    border: 1px solid rgba(76, 217, 100, 0.5);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">
                    ✅ 窗口显示成功！
                </div>
                <h1>🎈 BubbleBot</h1>
                <p>恭喜！窗口现在可以正常显示了。<br>这说明问题已经得到解决。</p>
                <textarea placeholder="在这里输入你的消息..." autofocus></textarea>
                <p style="font-size: 12px; opacity: 0.8; margin-top: 20px;">
                    窗口显示修复版本<br>
                    现在可以看到这个窗口了！
                </p>
            </div>
            <script>
                // 自动聚焦到文本区域
                document.querySelector('textarea').focus();
            </script>
        </body>
        </html>
        """
        
        self.webview.loadHTMLString_baseURL_(html_content, None)
        
        # 显示窗口
        print("🔧 显示窗口...")
        NSApp.activateIgnoringOtherApps_(True)
        self.window.makeKeyAndOrderFront_(None)
        
        print("🔧 窗口显示完成！")
        print("🔧 如果你能看到一个紫色渐变背景的窗口，说明问题已经解决")

def main():
    print("🔧 启动BubbleBot修复版...")
    
    app = NSApplication.sharedApplication()
    delegate = FixedAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    print("🔧 开始运行应用...")
    app.run()

if __name__ == "__main__":
    main()
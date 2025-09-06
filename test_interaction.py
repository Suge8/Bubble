#!/usr/bin/env python3
"""
简化的窗口交互测试工具
用于诊断 BubbleBot 的窗口交互问题
"""

import objc
from AppKit import *
from WebKit import *

class TestWindow(NSWindow):
    def canBecomeKeyWindow(self):
        return True
    
    def canBecomeMainWindow(self):
        return True
    
    def acceptsFirstResponder(self):
        return True

class TestAppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("=== 创建测试窗口 ===")
        
        # 创建标准窗口
        window_rect = NSMakeRect(100, 100, 600, 400)
        window_style = (NSWindowStyleMaskTitled | 
                       NSWindowStyleMaskClosable | 
                       NSWindowStyleMaskResizable)
        
        self.window = TestWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            window_style,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setTitle_("BubbleBot 交互测试")
        
        # 关键设置：确保窗口能接收事件
        self.window.setLevel_(NSNormalWindowLevel)  # 普通级别
        self.window.setIgnoresMouseEvents_(False)   # 不忽略鼠标事件
        self.window.setAcceptsMouseMovedEvents_(True)  # 接受鼠标移动
        self.window.setOpaque_(True)  # 不透明
        self.window.setBackgroundColor_(NSColor.windowBackgroundColor())
        
        print(f"窗口配置:")
        print(f"  - 级别: {self.window.level()}")
        print(f"  - 忽略鼠标: {self.window.ignoresMouseEvents()}")
        print(f"  - 不透明: {self.window.isOpaque()}")
        print(f"  - 可成为关键窗口: {self.window.canBecomeKeyWindow()}")
        
        # 创建简单的WebView
        config = WKWebViewConfiguration.alloc().init()
        config.preferences().setJavaScriptEnabled_(True)
        
        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            ((0, 0), (600, 400)),
            config
        )
        
        self.webview.setUIDelegate_(self)
        self.webview.setNavigationDelegate_(self)
        
        # 加载测试HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>交互测试</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 20px; 
                    background: #f0f0f0;
                }
                .test-button {
                    background: #007AFF;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    margin: 10px;
                    display: block;
                }
                .test-button:hover {
                    background: #0051D5;
                }
                .test-input {
                    width: 300px;
                    padding: 10px;
                    font-size: 14px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    margin: 10px;
                }
                .result {
                    background: #e8f5e8;
                    padding: 10px;
                    margin: 10px;
                    border-radius: 5px;
                    display: none;
                }
            </style>
        </head>
        <body>
            <h1>🧪 BubbleBot 交互测试</h1>
            <p>如果你能看到这个页面但无法点击，说明存在事件传递问题。</p>
            
            <button class="test-button" onclick="testClick()">点击测试按钮</button>
            <input type="text" class="test-input" placeholder="在这里输入测试文字" onchange="testInput(this.value)">
            
            <div id="result" class="result">
                <strong>✅ 交互正常！</strong> 窗口事件处理工作正常。
            </div>
            
            <script>
                function testClick() {
                    console.log('按钮被点击了！');
                    document.getElementById('result').style.display = 'block';
                    alert('按钮点击成功！事件处理正常。');
                }
                
                function testInput(value) {
                    console.log('输入值：', value);
                    if (value) {
                        document.getElementById('result').style.display = 'block';
                        document.getElementById('result').innerHTML = 
                            '<strong>✅ 输入成功！</strong> 你输入了：' + value;
                    }
                }
                
                // 页面加载完成时的调试信息
                window.addEventListener('load', function() {
                    console.log('页面加载完成，准备测试交互');
                });
                
                // 监听点击事件（包括失败的点击）
                document.addEventListener('click', function(e) {
                    console.log('检测到点击事件：', e.target);
                });
            </script>
        </body>
        </html>
        """
        
        self.webview.loadHTMLString_baseURL_(html_content, None)
        self.window.setContentView_(self.webview)
        
        # 显示窗口
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        
        print("=== 窗口显示完成 ===")
        print("请尝试：")
        print("1. 点击窗口标题栏的控制按钮（关闭、最小化）")
        print("2. 点击页面中的蓝色按钮")
        print("3. 在输入框中输入文字")
        print("4. 拖拽窗口移动")
        
        # 检查窗口状态
        print(f"\n窗口状态:")
        print(f"  - 可见: {self.window.isVisible()}")
        print(f"  - 关键窗口: {self.window.isKeyWindow()}")
        print(f"  - 主窗口: {self.window.isMainWindow()}")
    
    def webView_didFinishNavigation_(self, webView, navigation):
        """页面加载完成"""
        print("WebView 页面加载完成")
        
        # 确保页面可交互
        script = """
        console.log('注入交互检查脚本');
        document.body.style.pointerEvents = 'auto';
        """
        webView.evaluateJavaScript_completionHandler_(script, None)
    
    def applicationShouldTerminateAfterLastWindowClosed_(self, application):
        return True

def main():
    print("启动 BubbleBot 交互测试工具...")
    
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    
    delegate = TestAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    print("开始运行应用...")
    app.run()

if __name__ == '__main__':
    main()
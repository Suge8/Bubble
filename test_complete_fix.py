#!/usr/bin/env python3
"""
最简化的窗口交互测试
完全重建事件处理系统
"""

import objc
from AppKit import *
from WebKit import *

class WorkingWindow(NSWindow):
    def canBecomeKeyWindow(self):
        return True
    
    def canBecomeMainWindow(self):
        return True
    
    def acceptsFirstResponder(self):
        return True

class WorkingDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("=== 创建完全可交互的测试窗口 ===")
        
        # 创建窗口 - 使用最基本的配置
        window_rect = NSMakeRect(200, 200, 800, 600)
        window_style = (NSWindowStyleMaskTitled | 
                       NSWindowStyleMaskClosable | 
                       NSWindowStyleMaskResizable |
                       NSWindowStyleMaskMiniaturizable)
        
        self.window = WorkingWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            window_style,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setTitle_("BubbleBot 交互修复测试")
        
        # 最重要的设置 - 确保事件传递
        self.window.setLevel_(NSNormalWindowLevel)  # 普通级别
        self.window.setIgnoresMouseEvents_(False)   # 不忽略鼠标
        self.window.setOpaque_(True)                # 不透明
        self.window.setBackgroundColor_(NSColor.windowBackgroundColor())
        
        print(f"窗口创建:")
        print(f"  - 级别: {self.window.level()}")
        print(f"  - 忽略鼠标: {self.window.ignoresMouseEvents()}")
        print(f"  - 透明度: {self.window.alphaValue()}")
        print(f"  - 不透明: {self.window.isOpaque()}")
        
        # 创建 WebView - 最简配置
        config = WKWebViewConfiguration.alloc().init()
        preferences = config.preferences()
        preferences.setJavaScriptEnabled_(True)
        
        webview_frame = ((0, 0), (800, 600))
        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            webview_frame, config
        )
        
        self.webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 加载测试页面
        html = """<!DOCTYPE html>
        <html>
        <head>
            <title>交互修复测试</title>
            <style>
                body { 
                    font-family: system-ui, -apple-system; 
                    margin: 40px; 
                    background: #f8f9fa; 
                }
                .test-area {
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }
                h1 { color: #1d1d1f; }
                .big-button {
                    background: linear-gradient(135deg, #007AFF, #5856D6);
                    color: white;
                    border: none;
                    padding: 20px 40px;
                    font-size: 18px;
                    font-weight: 600;
                    border-radius: 12px;
                    cursor: pointer;
                    margin: 15px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0,122,255,0.3);
                }
                .big-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,122,255,0.4);
                }
                .big-button:active {
                    transform: translateY(0px);
                    box-shadow: 0 2px 10px rgba(0,122,255,0.3);
                }
                input, textarea {
                    width: 100%;
                    padding: 15px;
                    font-size: 16px;
                    border: 2px solid #e5e5e7;
                    border-radius: 8px;
                    margin: 10px 0;
                    outline: none;
                    transition: border-color 0.3s;
                }
                input:focus, textarea:focus {
                    border-color: #007AFF;
                    box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
                }
                .status {
                    background: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    display: none;
                    border: 1px solid #c3e6cb;
                }
                .counter {
                    background: #007AFF;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 20px;
                    display: inline-block;
                    font-weight: bold;
                    margin: 10px;
                }
            </style>
        </head>
        <body>
            <div class="test-area">
                <h1>🔧 BubbleBot 交互修复测试</h1>
                <p>如果这个页面的交互正常工作，说明窗口事件处理已修复：</p>
                
                <div class="counter">点击次数: <span id="clickCount">0</span></div>
                
                <button class="big-button" onclick="testClick()" onmousedown="buttonDown()" onmouseup="buttonUp()">
                    🎯 大按钮点击测试
                </button>
                
                <button class="big-button" onclick="changeColor()" style="background: linear-gradient(135deg, #34C759, #30D158);">
                    🌈 改变背景颜色
                </button>
                
                <div style="margin: 20px 0;">
                    <input type="text" id="testInput" placeholder="输入测试文字（实时反馈）" 
                           oninput="inputChange()" onclick="inputClick()" onfocus="inputFocus()">
                    <textarea placeholder="多行文本测试区域" rows="3" 
                              oninput="textareaChange()" onclick="textareaClick()"></textarea>
                </div>
                
                <div id="status" class="status"></div>
                
                <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; font-size: 14px; color: #666;">
                    <strong>测试说明：</strong><br>
                    ✅ 如果按钮有悬停效果和点击反馈 = 鼠标事件正常<br>
                    ✅ 如果输入框能正常输入和获得焦点 = 键盘事件正常<br>
                    ✅ 如果窗口标题栏按钮可点击 = 系统事件正常
                </div>
            </div>
            
            <script>
                let clickCount = 0;
                let colors = ['#f8f9fa', '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0'];
                let colorIndex = 0;
                
                function testClick() {
                    clickCount++;
                    document.getElementById('clickCount').textContent = clickCount;
                    showStatus('✅ 按钮点击成功！次数：' + clickCount);
                    console.log('按钮点击事件触发，总次数：', clickCount);
                }
                
                function buttonDown() {
                    console.log('鼠标按下事件');
                    event.target.style.transform = 'scale(0.95)';
                }
                
                function buttonUp() {
                    console.log('鼠标松开事件');
                    event.target.style.transform = 'scale(1)';
                }
                
                function changeColor() {
                    colorIndex = (colorIndex + 1) % colors.length;
                    document.body.style.backgroundColor = colors[colorIndex];
                    showStatus('🌈 背景颜色已改变');
                }
                
                function inputChange() {
                    const value = event.target.value;
                    showStatus('⌨️ 输入检测：' + value);
                }
                
                function inputClick() {
                    showStatus('🖱️ 输入框被点击');
                }
                
                function inputFocus() {
                    showStatus('🎯 输入框获得焦点');
                }
                
                function textareaChange() {
                    showStatus('📝 文本区域内容变化');
                }
                
                function textareaClick() {
                    showStatus('📄 文本区域被点击');
                }
                
                function showStatus(message) {
                    const status = document.getElementById('status');
                    status.textContent = message;
                    status.style.display = 'block';
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                }
                
                // 全局事件监听
                document.addEventListener('click', function(e) {
                    console.log('全局点击事件：', e.target.tagName, e.target.type);
                });
                
                document.addEventListener('mouseover', function(e) {
                    if (e.target.tagName === 'BUTTON') {
                        console.log('按钮悬停');
                    }
                });
                
                // 页面加载完成
                console.log('测试页面加载完成，交互系统就绪');
                showStatus('🚀 页面加载完成，开始测试交互！');
            </script>
        </body>
        </html>"""
        
        self.webview.loadHTMLString_baseURL_(html, None)
        self.window.setContentView_(self.webview)
        
        # 显示窗口
        self.window.center()
        self.window.makeKeyAndOrderFront_(None)
        
        NSApp.activateIgnoringOtherApps_(True)
        
        print("=== 窗口显示完成 ===")
        print(f"可见: {self.window.isVisible()}")
        print(f"关键窗口: {self.window.isKeyWindow()}")
        print("如果窗口出现但无法交互，说明存在根本性的事件阻塞问题")
    
    def applicationShouldTerminateAfterLastWindowClosed_(self, application):
        return True

def main():
    print("启动 BubbleBot 交互修复测试...")
    print("这个版本完全重建了事件处理系统")
    
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    
    delegate = WorkingDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    print("启动应用...")
    app.run()

if __name__ == '__main__':
    main()
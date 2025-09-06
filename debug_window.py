#!/usr/bin/env python3
"""
窗口调试脚本
用于诊断BubbleBot窗口显示问题
"""

import sys
import objc
from AppKit import *
from WebKit import *
from Quartz import *

def test_window_creation():
    """测试窗口创建和显示"""
    try:
        print("开始测试窗口创建...")
        
        # 创建应用
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
        # 创建简单的测试窗口
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100, 100, 400, 300),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("测试窗口")
        
        # 添加简单文本
        text_field = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 50, 300, 50))
        text_field.setStringValue_("如果您看到这个窗口，说明窗口创建正常")
        text_field.setEditable_(False)
        text_field.setBezeled_(False)
        text_field.setDrawsBackground_(False)
        
        window.contentView().addSubview_(text_field)
        
        # 显示窗口
        window.makeKeyAndOrderFront_(None)
        app.activateIgnoringOtherApps_(True)
        
        print("测试窗口已创建并显示")
        print("窗口是否可见:", window.isVisible())
        print("窗口是否是主窗口:", window.isKeyWindow())
        
        # 短暂显示后关闭
        import time
        time.sleep(3)
        
        window.close()
        print("测试窗口已关闭")
        
        return True
        
    except Exception as e:
        print(f"窗口创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webview_creation():
    """测试WebView创建"""
    try:
        print("开始测试WebView创建...")
        
        # 创建WebView配置
        config = WKWebViewConfiguration.alloc().init()
        config.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
        
        # 创建WebView
        webview = WKWebView.alloc().initWithFrame_configuration_(
            ((0, 0), (400, 300)),
            config
        )
        
        print("WebView创建成功")
        
        # 测试加载简单HTML
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>WebView测试页面</h1></body>
        </html>
        """
        webview.loadHTMLString_baseURL_(html, None)
        print("HTML内容已加载到WebView")
        
        return True
        
    except Exception as e:
        print(f"WebView创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_permissions():
    """检查权限状态"""
    try:
        print("检查权限状态...")
        
        # 检查辅助功能权限
        try:
            from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
            is_trusted = AXIsProcessTrustedWithOptions(None)
            print(f"辅助功能权限: {'已授权' if is_trusted else '未授权'}")
        except Exception as e:
            print(f"无法检查辅助功能权限: {e}")
        
        # 检查应用激活策略
        app = NSApplication.sharedApplication()
        activation_policy = app.activationPolicy()
        policies = {
            0: "NSApplicationActivationPolicyRegular",
            1: "NSApplicationActivationPolicyAccessory", 
            2: "NSApplicationActivationPolicyProhibited"
        }
        print(f"应用激活策略: {policies.get(activation_policy, '未知')}")
        
        return True
        
    except Exception as e:
        print(f"权限检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*50)
    print("BubbleBot 窗口显示问题诊断")
    print("="*50)
    
    # 检查权限
    check_permissions()
    print()
    
    # 测试WebView创建
    test_webview_creation()
    print()
    
    # 测试窗口创建
    test_window_creation()
    print()
    
    print("诊断完成")

if __name__ == "__main__":
    main()
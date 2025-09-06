#!/usr/bin/env python3
"""
窗口显示问题诊断和修复测试
"""

import sys
sys.path.insert(0, 'src')

from AppKit import *
from Foundation import NSObject
import objc

class WindowTestDelegate(NSObject):
    def __init__(self):
        objc.super(WindowTestDelegate, self).__init__()
        self.window = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("🔧 开始窗口显示测试...")
        
        # 设置应用激活策略
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        print(f"🔧 应用激活策略: {NSApp.activationPolicy()}")
        
        # 创建窗口 - 使用与BubbleBot相同的配置
        print("🔧 创建窗口...")
        window_rect = NSMakeRect(500, 200, 550, 580)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            NSBorderlessWindowMask | NSResizableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        
        print(f"🔧 窗口创建完成: {self.window}")
        
        # 设置窗口属性
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
        )
        
        # 测试1: 完全透明的窗口（BubbleBot当前设置）
        print("🔧 测试1: 透明窗口配置...")
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        
        # 创建内容视图
        content_view = NSView.alloc().initWithFrame_(self.window.contentView().bounds())
        content_view.setWantsLayer_(True)
        content_view.layer().setCornerRadius_(15.0)
        content_view.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
        self.window.setContentView_(content_view)
        
        # 添加测试标签
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 250, 450, 50))
        label.setStringValue_("测试 - 透明窗口配置")
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(NSTextAlignmentCenter)
        content_view.addSubview_(label)
        
        # 显示窗口
        print("🔧 显示窗口...")
        print(f"🔧 窗口是否不透明: {self.window.isOpaque()}")
        print(f"🔧 窗口背景颜色: {self.window.backgroundColor()}")
        print(f"🔧 窗口透明度: {self.window.alphaValue()}")
        
        # 尝试显示
        NSApp.activateIgnoringOtherApps_(True)
        self.window.orderFront_(None)
        self.window.makeKeyAndOrderFront_(None)
        
        print(f"🔧 窗口是否可见: {self.window.isVisible()}")
        print(f"🔧 窗口是否为关键窗口: {self.window.isKeyWindow()}")
        
        # 5秒后测试不透明窗口配置
        self.performSelector_withObject_afterDelay_("testOpaqueWindow:", None, 5.0)
    
    def testOpaqueWindow_(self, sender):
        print("\n🔧 测试2: 不透明窗口配置...")
        
        # 修改为不透明配置
        self.window.setOpaque_(True)
        self.window.setBackgroundColor_(NSColor.whiteColor())
        
        # 更新标签
        content_view = self.window.contentView()
        label = content_view.subviews()[0]  # 获取之前添加的标签
        label.setStringValue_("测试 - 不透明窗口配置")
        
        print(f"🔧 窗口是否不透明: {self.window.isOpaque()}")
        print(f"🔧 窗口背景颜色: {self.window.backgroundColor()}")
        print(f"🔧 窗口是否可见: {self.window.isVisible()}")
        
        # 重新显示
        self.window.orderFront_(None)
        self.window.makeKeyAndOrderFront_(None)
        
        print("🔧 如果第二次能看到窗口，说明透明度设置有问题")

def main():
    print("🔧 开始窗口显示诊断...")
    
    app = NSApplication.sharedApplication()
    delegate = WindowTestDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    print("🔧 启动应用...")
    app.run()

if __name__ == "__main__":
    main()
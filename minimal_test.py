#!/usr/bin/env python3
"""
最小化测试 - 验证窗口显示是否正常
"""

import sys
sys.path.insert(0, 'src')

from AppKit import *
from Foundation import NSObject
import objc

class MinimalDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("🔧 最小化测试开始...")
        
        # 设置应用策略
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
        # 创建标准窗口
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, 400, 300),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("BubbleBot 最小化测试")
        window.setBackgroundColor_(NSColor.whiteColor())
        
        # 添加简单标签
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 130, 300, 40))
        label.setStringValue_("✅ 如果你能看到这个窗口，说明显示正常！")
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(NSTextAlignmentCenter)
        window.contentView().addSubview_(label)
        
        # 显示窗口
        NSApp.activateIgnoringOtherApps_(True)
        window.makeKeyAndOrderFront_(None)
        
        print("🔧 窗口应该已经显示")
        print("🔧 如果看不到窗口，请检查Dock栏是否有Python图标")

def main():
    app = NSApplication.sharedApplication()
    delegate = MinimalDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()
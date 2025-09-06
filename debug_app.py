#!/usr/bin/env python3
"""
简化的调试版本，用于诊断BubbleBot启动问题
"""

import sys
sys.path.insert(0, 'src')

from AppKit import *
from Foundation import NSObject
import objc

class DebugAppDelegate(NSObject):
    def __init__(self):
        objc.super(DebugAppDelegate, self).__init__()
        self.window = None
    
    def applicationDidFinishLaunching_(self, notification):
        print("🔧 开始创建调试窗口...")
        
        # 创建简单窗口
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100, 100, 400, 300),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setTitle_("BubbleBot Debug Window")
        self.window.setBackgroundColor_(NSColor.whiteColor())
        
        print("🔧 窗口创建完成，准备显示...")
        
        # 显示窗口
        self.window.makeKeyAndOrderFront_(None)
        
        print("🔧 窗口显示完成！")
        print("🔧 如果你能看到一个白色窗口，说明基础功能正常")

def debug_main():
    print("🔧 开始调试模式...")
    
    app = NSApplication.sharedApplication()
    delegate = DebugAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    print("🔧 准备启动应用...")
    app.run()

if __name__ == "__main__":
    debug_main()
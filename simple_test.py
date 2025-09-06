#!/usr/bin/env python3
"""
简化测试脚本 - 最小化BubbleBot启动逻辑
"""

import sys
import objc
from AppKit import *
from WebKit import *

def main():
    print("开始创建最简单的窗口...")
    
    try:
        # 创建应用
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
        # 创建窗口
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(500, 200, 550, 580),
            NSBorderlessWindowMask | NSResizableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        
        # 设置窗口属性
        window.setLevel_(NSFloatingWindowLevel)
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
        
        # 创建内容视图
        content_view = NSView.alloc().initWithFrame_(window.contentView().bounds())
        content_view.setWantsLayer_(True)
        content_view.layer().setCornerRadius_(15.0)
        content_view.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
        window.setContentView_(content_view)
        
        # 添加一个简单的标签
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 250, 450, 50))
        label.setStringValue_("BubbleBot测试窗口 - 如果你看到这个，窗口显示正常")
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(NSTextAlignmentCenter)
        content_view.addSubview_(label)
        
        print("窗口创建完成，准备显示...")
        
        # 显示窗口
        app.activateIgnoringOtherApps_(True)
        window.makeKeyAndOrderFront_(None)
        
        print(f"窗口状态: 可见={window.isVisible()}, 主窗口={window.isKeyWindow()}")
        print("窗口已显示，应用将保持运行...")
        
        # 运行应用
        app.run()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
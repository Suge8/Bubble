#!/usr/bin/env python3
"""
最简单的窗口测试 - 排除所有复杂因素
"""

import sys
import signal
import os
sys.path.insert(0, 'src')

def signal_handler(sig, frame):
    print(f"\n收到信号 {sig}，退出...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

from AppKit import *
from Foundation import NSObject
import objc

print("🚀 最简单窗口测试开始...")

# 创建应用
app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

print(f"✅ 应用创建成功: {app}")

# 设置图标
icon_path = "/Users/sugeh/Documents/Project/Bubble-Bot/src/bubblebot/logo/icon.icns"
if os.path.exists(icon_path):
    app_icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
    if app_icon:
        app.setApplicationIconImage_(app_icon)
        print("✅ 应用图标设置成功")
    else:
        print("❌ 图标加载失败")
else:
    print(f"❌ 图标文件不存在: {icon_path}")

# 创建标准窗口（保证可见）
print("🔧 创建标准窗口...")
window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    NSMakeRect(100, 100, 400, 300),
    NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    False
)

window.setTitle_("BubbleBot 简单测试")
window.setBackgroundColor_(NSColor.redColor())  # 使用红色背景，确保可见

print(f"✅ 窗口创建成功: {window}")

# 添加标签
label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 130, 300, 40))
label.setStringValue_("🔴 如果你看到红色窗口，说明显示正常！")
label.setEditable_(False)
label.setBezeled_(False)
label.setDrawsBackground_(False)
label.setAlignment_(NSTextAlignmentCenter)
label.setFont_(NSFont.systemFontOfSize_(14))
window.contentView().addSubview_(label)

# 激活应用并显示窗口
print("🚀 激活应用...")
app.activateIgnoringOtherApps_(True)

print("🚀 显示窗口...")
window.makeKeyAndOrderFront_(None)

print("✅ 显示命令完成")
print(f"📊 窗口状态: 可见={window.isVisible()}, 关键窗口={window.isKeyWindow()}")
print(f"📊 应用状态: 激活={app.isActive()}, 隐藏={app.isHidden()}")

print("🔍 请检查:")
print("   1. 屏幕上是否有红色窗口？")
print("   2. Dock 中是否有 BubbleBot 图标？")
print("   3. 如果都没有，请告诉我")

# 简单的运行循环
print("⏰ 运行 10 秒后自动退出...")
import time
time.sleep(10)
print("🔚 测试结束")
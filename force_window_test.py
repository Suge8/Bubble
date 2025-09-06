#!/usr/bin/env python3
"""
强制显示窗口测试 - 尝试所有可能的显示方法
"""

import sys
import signal
import os
import time
sys.path.insert(0, 'src')

def signal_handler(sig, frame):
    print(f"\n收到信号 {sig}，退出...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

from AppKit import *
from Foundation import NSObject
import objc

print("🚀 强制显示窗口测试...")

# 创建应用
app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

# 获取屏幕信息
main_screen = NSScreen.mainScreen()
screen_frame = main_screen.frame()
print(f"📺 屏幕尺寸: {screen_frame.size.width} x {screen_frame.size.height}")

# 计算屏幕中央位置
window_width = 500
window_height = 400
x = (screen_frame.size.width - window_width) / 2
y = (screen_frame.size.height - window_height) / 2

print(f"📍 窗口位置: x={x}, y={y}")

# 创建醒目的窗口
window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    NSMakeRect(x, y, window_width, window_height),
    NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
    NSBackingStoreBuffered,
    False
)

window.setTitle_("🔴 BubbleBot 强制测试 - 你应该能看到我！")
window.setBackgroundColor_(NSColor.redColor())

# 强制设置为最高级别
window.setLevel_(NSFloatingWindowLevel + 100)  # 极高优先级
print(f"🔝 窗口级别设置为: {window.level()}")

# 添加大型标签
label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 160, 400, 80))
label.setStringValue_("🚨 紧急测试窗口 🚨\n\n如果你看到这个红色窗口，\n请立即按 Ctrl+C")
label.setEditable_(False)
label.setBezeled_(False)
label.setDrawsBackground_(False)
label.setAlignment_(NSTextAlignmentCenter)
label.setFont_(NSFont.boldSystemFontOfSize_(18))
label.setTextColor_(NSColor.whiteColor())
window.contentView().addSubview_(label)

# 设置图标
icon_path = "/Users/sugeh/Documents/Project/Bubble-Bot/src/bubblebot/logo/icon.icns"
if os.path.exists(icon_path):
    app_icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
    if app_icon:
        app.setApplicationIconImage_(app_icon)
        print("✅ 应用图标已设置")

# 尝试所有可能的激活和显示方法
print("🔥 尝试所有显示方法...")

# 方法1: 基本显示
print("   方法1: makeKeyAndOrderFront")
window.makeKeyAndOrderFront_(None)

# 方法2: 强制激活
print("   方法2: 强制激活应用")
app.activateIgnoringOtherApps_(True)

# 方法3: 置前窗口
print("   方法3: orderFront")
window.orderFront_(None)

# 方法4: 强制关键窗口
print("   方法4: makeKeyWindow")
window.makeKeyWindow()

# 方法5: 确保不隐藏
print("   方法5: unhide应用")
app.unhide_(None)

# 方法6: 重复激活
for i in range(3):
    app.activateIgnoringOtherApps_(True)
    window.makeKeyAndOrderFront_(None)
    time.sleep(0.1)

print("✅ 所有显示方法已尝试")
print(f"📊 最终状态:")
print(f"   - 窗口可见: {window.isVisible()}")
print(f"   - 关键窗口: {window.isKeyWindow()}")
print(f"   - 主窗口: {window.isMainWindow()}")
print(f"   - 应用激活: {app.isActive()}")
print(f"   - 应用隐藏: {app.isHidden()}")
print(f"   - 窗口级别: {window.level()}")

print("\n🔍 重要！请仔细检查:")
print("   1. 你的屏幕上是否有任何红色窗口？")
print("   2. Dock 中是否有新的图标（不是火箭）？")
print("   3. 是否有任何弹窗或通知？")
print("   4. 检查所有桌面空间")
print("   5. 检查菜单栏是否有新项目")

print("\n⏰ 等待 15 秒，请仔细观察...")
time.sleep(15)
print("🔚 测试结束")
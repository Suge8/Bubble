#!/usr/bin/env python3
"""
使用系统对话框测试 - 绕过窗口限制
"""

import sys
import os
import signal
sys.path.insert(0, 'src')

def signal_handler(sig, frame):
    print(f"\n收到信号 {sig}，退出...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

from AppKit import *
from Foundation import NSObject
import objc

print("🚀 使用系统对话框测试...")

# 创建应用
app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

# 设置图标
icon_path = "/Users/sugeh/Documents/Project/Bubble-Bot/src/bubblebot/logo/icon.icns"
if os.path.exists(icon_path):
    app_icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
    if app_icon:
        app.setApplicationIconImage_(app_icon)
        print("✅ 应用图标已设置")

# 激活应用
app.activateIgnoringOtherApps_(True)

print("🔔 显示系统对话框...")

# 使用系统警告对话框
alert = NSAlert.alloc().init()
alert.setMessageText_("🎈 BubbleBot 测试成功！")
alert.setInformativeText_("""如果你看到这个对话框，说明：

✅ PyObjC 工作正常
✅ 应用图标已设置
✅ 基本显示功能正常

但是窗口可能被 macOS 安全策略阻止了。

请检查：
• 系统偏好设置 > 隐私与安全性 > 辅助功能
• 添加 Terminal 或 Python 的权限

然后重新测试 BubbleBot。""")

alert.addButtonWithTitle_("好的，我明白了")
alert.addButtonWithTitle_("取消")

# 设置图标
if app_icon:
    alert.setIcon_(app_icon)

print("📋 请查看屏幕上的对话框...")
result = alert.runModal()

if result == NSAlertFirstButtonReturn:
    print("✅ 用户点击了确定")
else:
    print("❌ 用户点击了取消")

print("🔚 测试完成")
print("💡 如果你看到了带有 BubbleBot 图标的对话框，")
print("   说明图标设置成功，只是窗口被阻止了。")
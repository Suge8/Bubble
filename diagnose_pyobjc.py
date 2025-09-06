#!/usr/bin/env python3
"""
诊断 PyObjC 安装和权限问题
"""

import sys
import os

print("🔧 PyObjC 诊断开始...")
print("=" * 50)

# 1. 检查 Python 版本
print(f"🐍 Python 版本: {sys.version}")
print(f"🐍 Python 可执行文件: {sys.executable}")

# 2. 检查虚拟环境
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("✅ 在虚拟环境中运行")
else:
    print("⚠️ 不在虚拟环境中运行")

# 3. 检查 PyObjC 模块
print("\n📦 检查 PyObjC 模块:")
modules_to_check = [
    'objc',
    'Foundation',
    'AppKit',
    'WebKit',
    'Quartz'
]

for module in modules_to_check:
    try:
        __import__(module)
        print(f"   ✅ {module} - 已安装")
    except ImportError as e:
        print(f"   ❌ {module} - 缺失: {e}")

# 4. 检查 NSApplication 创建
print("\n🔧 测试 NSApplication 创建:")
try:
    from AppKit import NSApplication
    app = NSApplication.sharedApplication()
    print(f"   ✅ NSApplication 创建成功: {app}")
    print(f"   📊 激活策略: {app.activationPolicy()}")
except Exception as e:
    print(f"   ❌ NSApplication 创建失败: {e}")

# 5. 检查屏幕信息
print("\n📺 检查屏幕信息:")
try:
    from AppKit import NSScreen
    screens = NSScreen.screens()
    print(f"   📊 屏幕数量: {len(screens)}")
    
    main_screen = NSScreen.mainScreen()
    if main_screen:
        frame = main_screen.frame()
        print(f"   📊 主屏幕尺寸: {frame.size.width} x {frame.size.height}")
    else:
        print("   ❌ 无法获取主屏幕")
except Exception as e:
    print(f"   ❌ 屏幕检查失败: {e}")

# 6. 检查窗口创建权限
print("\n🪟 测试窗口创建:")
try:
    from AppKit import NSWindow, NSWindowStyleMaskTitled, NSBackingStoreBuffered
    from Foundation import NSMakeRect
    
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(100, 100, 200, 200),
        NSWindowStyleMaskTitled,
        NSBackingStoreBuffered,
        False
    )
    
    if window:
        print(f"   ✅ 窗口对象创建成功: {window}")
        print(f"   📊 窗口类型: {type(window)}")
    else:
        print("   ❌ 窗口对象创建失败")
        
except Exception as e:
    print(f"   ❌ 窗口创建测试失败: {e}")

# 7. 检查文件权限
print("\n📁 检查图标文件:")
icon_path = "/Users/sugeh/Documents/Project/Bubble-Bot/src/bubblebot/logo/icon.icns"
if os.path.exists(icon_path):
    print(f"   ✅ 图标文件存在: {icon_path}")
    file_size = os.path.getsize(icon_path)
    print(f"   📊 文件大小: {file_size} bytes")
    print(f"   📊 文件权限: {oct(os.stat(icon_path).st_mode)}")
else:
    print(f"   ❌ 图标文件不存在: {icon_path}")

# 8. 系统信息
print("\n💻 系统信息:")
import platform
print(f"   📊 操作系统: {platform.system()} {platform.release()}")
print(f"   📊 机器类型: {platform.machine()}")

# 9. 进程信息
print("\n🔄 进程信息:")
print(f"   📊 进程 ID: {os.getpid()}")
print(f"   📊 用户 ID: {os.getuid()}")

print("\n" + "=" * 50)
print("🔚 诊断完成")
print("\n💡 如果所有项目都显示 ✅，但窗口仍不显示，")
print("   可能是 macOS 安全策略阻止了 Python 应用显示窗口。")
print("   请检查 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能")
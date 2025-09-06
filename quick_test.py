#!/usr/bin/env python3
"""
快速测试 BubbleBot 应用启动
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_import():
    """测试基础导入功能"""
    try:
        # 测试基础模块导入
        from bubblebot.main import main
        from bubblebot.app import AppDelegate
        from bubblebot.components import MultiWindowManager
        
        print("✅ 所有核心模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_app_delegate_init():
    """测试AppDelegate初始化"""
    try:
        from bubblebot.app import AppDelegate
        delegate = AppDelegate.alloc().init()
        
        # 检查重要属性
        assert hasattr(delegate, 'ai_selector'), "ai_selector属性缺失"
        assert hasattr(delegate, 'setHomepageManager_'), "setHomepageManager_方法缺失"
        assert hasattr(delegate, 'setNavigationController_'), "setNavigationController_方法缺失"
        assert hasattr(delegate, 'setMultiwindowManager_'), "setMultiwindowManager_方法缺失"
        
        print("✅ AppDelegate初始化成功")
        return True
    except Exception as e:
        print(f"❌ AppDelegate初始化失败: {e}")
        return False

def test_multiwindow_manager_init():
    """测试MultiWindowManager初始化"""
    try:
        from bubblebot.components import MultiWindowManager
        manager = MultiWindowManager.alloc().init()
        
        print("✅ MultiWindowManager初始化成功")
        return True
    except Exception as e:
        print(f"❌ MultiWindowManager初始化失败: {e}")
        return False

def test_component_integration():
    """测试组件集成"""
    try:
        from bubblebot.app import AppDelegate
        from bubblebot.components import HomepageManager, NavigationController, MultiWindowManager
        
        # 创建所有组件
        delegate = AppDelegate.alloc().init()
        homepage_manager = HomepageManager.alloc().init()
        navigation_controller = NavigationController.alloc().init()
        multiwindow_manager = MultiWindowManager.alloc().init()
        
        # 设置组件
        delegate.setHomepageManager_(homepage_manager)
        delegate.setNavigationController_(navigation_controller)
        delegate.setMultiwindowManager_(multiwindow_manager)
        
        print("✅ 组件集成测试成功")
        return True
    except Exception as e:
        print(f"❌ 组件集成测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🧪 BubbleBot 快速测试")
    print("=" * 40)
    
    tests = [
        ("基础模块导入", test_basic_import),
        ("AppDelegate初始化", test_app_delegate_init),
        ("MultiWindowManager初始化", test_multiwindow_manager_init),
        ("组件集成", test_component_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        if test_func():
            passed += 1
    
    print(f"\n🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用组件可以正常工作。")
        
        # 尝试权限检查
        try:
            print("\n🔐 测试权限检查...")
            from bubblebot.launcher import check_permissions
            result = check_permissions(ask=False)
            print(f"✅ 权限检查完成，当前状态: {'已授予' if result else '未授予'}")
        except Exception as e:
            print(f"❌ 权限检查失败: {e}")
        
        return 0
    else:
        print("⚠️ 有测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit(main())
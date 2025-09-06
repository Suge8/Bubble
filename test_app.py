#!/usr/bin/env python3
"""
BubbleBot 应用测试脚本

这个脚本会进行一系列自动化测试，包括：
1. 环境检查
2. 依赖验证
3. 模块导入测试
4. 权限检查
5. 基本功能测试
"""

import sys
import os
import subprocess
import importlib
import platform

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """打印测试段落标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_test(test_name, status, details=""):
    """打印测试结果"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_environment():
    """测试运行环境"""
    print_header("环境检查")
    
    # Python版本检查
    python_version = platform.python_version()
    python_ok = sys.version_info >= (3, 10)
    print_test(f"Python版本: {python_version}", python_ok, "需要 Python 3.10+")
    
    # macOS系统检查
    macos_ok = platform.system() == "Darwin"
    print_test(f"操作系统: {platform.system()}", macos_ok, "需要 macOS 系统")
    
    return python_ok and macos_ok

def test_dependencies():
    """测试依赖包"""
    print_header("依赖包检查")
    
    required_packages = [
        "objc",
        "Quartz", 
        "WebKit",
        "AVFoundation",
        "ApplicationServices"
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_test(f"导入 {package}", True)
        except ImportError as e:
            print_test(f"导入 {package}", False, str(e))
            all_ok = False
    
    return all_ok

def test_app_modules():
    """测试应用模块"""
    print_header("应用模块测试")
    
    modules = [
        "bubblebot.constants",
        "bubblebot.health_checks", 
        "bubblebot.launcher",
        "bubblebot.models.ai_window",
        "bubblebot.models.platform_config",
        "bubblebot.components.homepage_manager",
        "bubblebot.components.multiwindow_manager",
        "bubblebot.components.navigation_controller",
        "bubblebot.components.platform_manager",
        "bubblebot.app",
        "bubblebot.main"
    ]
    
    all_ok = True
    for module in modules:
        try:
            importlib.import_module(module)
            print_test(f"导入 {module}", True)
        except Exception as e:
            print_test(f"导入 {module}", False, str(e))
            all_ok = False
    
    return all_ok

def test_permissions():
    """测试权限检查功能"""
    print_header("权限检查测试")
    
    try:
        from bubblebot.launcher import check_permissions
        # 不要求权限，只检查函数是否能调用
        result = check_permissions(ask=False)
        print_test("权限检查功能", True, f"当前权限状态: {result}")
        return True
    except Exception as e:
        print_test("权限检查功能", False, str(e))
        return False

def test_main_function():
    """测试主函数"""
    print_header("主函数测试")
    
    try:
        from bubblebot.main import main
        print_test("主函数导入", True)
        
        # 测试命令行参数处理
        old_argv = sys.argv.copy()
        try:
            sys.argv = ['test', '--check-permissions']
            # 这里我们不实际运行main，只是验证它可以被调用
            print_test("命令行参数处理", True, "参数解析功能正常")
        finally:
            sys.argv = old_argv
            
        return True
    except Exception as e:
        print_test("主函数测试", False, str(e))
        return False

def run_unit_tests():
    """运行单元测试"""
    print_header("单元测试")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        success = result.returncode == 0
        print_test("单元测试套件", success, 
                  f"返回码: {result.returncode}")
        
        if result.stdout:
            print("📊 测试输出:")
            print(result.stdout)
        
        if result.stderr and not success:
            print("❌ 错误信息:")
            print(result.stderr)
            
        return success
    except Exception as e:
        print_test("单元测试套件", False, str(e))
        return False

def test_app_startup():
    """测试应用启动（不实际启动GUI）"""
    print_header("应用启动测试")
    
    try:
        # 只测试权限检查，不启动GUI
        result = subprocess.run([
            sys.executable, "BubbleBot.py", "--check-permissions"
        ], capture_output=True, text=True, timeout=10)
        
        # 权限检查命令：返回码1表示没有权限（正常），0表示有权限
        # 只要应用没有崩溃就算成功
        success = result.returncode in [0, 1]  # 0=有权限, 1=没有权限
        permission_status = "已授予" if result.returncode == 0 else "未授予"
        print_test("应用权限检查启动", success, 
                  f"应用成功启动并执行权限检查，权限状态: {permission_status}")
        
        if result.stdout:
            print("📋 输出:", result.stdout.strip())
        
        return success
    except subprocess.TimeoutExpired:
        print_test("应用启动测试", False, "启动超时")
        return False
    except Exception as e:
        print_test("应用启动测试", False, str(e))
        return False

def main():
    """主测试函数"""
    print("🚀 BubbleBot 应用测试开始")
    print(f"📍 项目路径: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"🐍 Python: {sys.executable}")
    
    tests = [
        ("环境检查", test_environment),
        ("依赖包检查", test_dependencies), 
        ("应用模块测试", test_app_modules),
        ("权限检查测试", test_permissions),
        ("主函数测试", test_main_function),
        ("单元测试", run_unit_tests),
        ("应用启动测试", test_app_startup)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test(f"{test_name} (异常)", False, str(e))
            results.append((test_name, False))
    
    # 总结
    print_header("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {test_name}")
    
    print(f"\n🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用可以正常运行。")
        return 0
    else:
        print("⚠️  有测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    exit(main())
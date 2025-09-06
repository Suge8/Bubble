"""
BubbleBot组件模块

该模块包含BubbleBot应用的各种组件，包括主页管理器、导航控制器、多窗口管理器等。
"""

from .homepage_manager import HomepageManager
from .navigation_controller import NavigationController
from .multiwindow_manager import MultiWindowManager
from .platform_manager import PlatformManager

__all__ = ['HomepageManager', 'NavigationController', 'MultiWindowManager', 'PlatformManager']
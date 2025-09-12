"""
数据模型包

定义多窗口 AI 平台管理系统的数据结构，包括：
- 平台配置模型
- 窗口实例模型
- 用户配置模型
"""

from .platform_config import PlatformConfig, AIServiceConfig
from .ai_window import AIWindow, WindowState

__all__ = [
    'PlatformConfig',
    'AIServiceConfig', 
    'AIWindow',
    'WindowState'
]

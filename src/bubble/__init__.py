"""
Bubble - macOS智能AI助手应用

支持多AI窗口并行使用的现代化AI助手

-- Sai Praveen 
"""

import os

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ABOUT_DIR = os.path.join(DIRECTORY, "about")

def _read_about_file(fname, default=""):
    """读取about目录下的配置文件"""
    try:
        with open(os.path.join(ABOUT_DIR, fname)) as f:
            return f.read().strip()
    except Exception:
        return default

__version__ = _read_about_file("version.txt", "0.0.1")
__author__ = _read_about_file("author.txt", "Sai Praveen")

__all__ = ["main"]

from .main import main  

# 允许通过 "from bubble import main" 导入

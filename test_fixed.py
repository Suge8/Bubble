#!/usr/bin/env python3
"""
简单测试，直接运行修复后的BubbleBot主代码
"""

import sys
import os
sys.path.insert(0, 'src')

from bubblebot.main import main

if __name__ == "__main__":
    print("🔧 运行修复后的BubbleBot...")
    main()
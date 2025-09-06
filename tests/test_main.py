"""
测试应用主逻辑
"""
import unittest
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bubblebot.main import main


class TestMain(unittest.TestCase):
    """测试主函数"""

    def test_main_import(self):
        """测试主函数可以正确导入"""
        self.assertTrue(callable(main))


if __name__ == '__main__':
    unittest.main()
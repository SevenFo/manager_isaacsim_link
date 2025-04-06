"""
pytest 配置文件，为测试提供共享的 fixture 和配置
"""

import os
import sys
import pytest
from pathlib import Path

# 添加包根目录到 Python 路径，确保测试可以导入包模块
# 这在开发过程中很有用，但在安装包后运行测试时不是必需的
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest 配置钩子"""
    # 添加一些标记
    config.addinivalue_line("markers", "slow: 标记为缓慢运行的测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line("markers", "unit: 标记为单元测试")


@pytest.fixture(scope="session")
def is_windows():
    """检查当前平台是否为 Windows"""
    return sys.platform == "win32"


@pytest.fixture(scope="session")
def is_admin():
    """检查当前用户是否有管理员权限（仅适用于 Windows）"""
    if sys.platform == "win32":
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.getuid() == 0
        except AttributeError:
            return False

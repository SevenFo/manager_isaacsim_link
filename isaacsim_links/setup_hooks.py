"""
安装和卸载钩子，用于 PEP 517 构建系统。
"""

import sys
import os
import atexit
from setuptools.command.install import install
from setuptools.command.develop import develop

# 导入安装和卸载功能
from .install import install as create_links
from .install import uninstall as remove_links


class CustomInstall(install):
    """自定义安装类，用于在包安装完成后创建符号链接"""

    def run(self):
        # 先执行标准安装
        install.run(self)
        # 安装后创建链接
        print("\n正在为 Isaac Sim 和 Omni 扩展创建符号链接...")
        create_links()


class CustomDevelop(develop):
    """自定义开发模式安装类，用于在包安装完成后创建符号链接"""

    def run(self):
        # 先执行标准开发模式安装
        develop.run(self)
        # 安装后创建链接
        print("\n正在为 Isaac Sim 和 Omni 扩展创建符号链接（开发模式）...")
        create_links()


# 为了在卸载时自动清理链接，我们注册一个卸载脚本
# 通常通过 pip 卸载包会调用这个脚本
def _cleanup():
    """卸载时的清理函数"""
    # 检查是否是在卸载操作中
    if "pip" in sys.argv[0] and ("uninstall" in sys.argv or "remove" in sys.argv):
        try:
            print("\n正在清理 Isaac Sim 和 Omni 扩展的符号链接...")
            remove_links()
        except Exception as e:
            print(f"清理链接时出错: {e}", file=sys.stderr)


# 注册卸载时的清理函数
atexit.register(_cleanup)

# 在包被导入时（如通过 pip show 或其他方式），也可以检测是否在卸载
if "pip" in sys.argv[0] and ("uninstall" in sys.argv or "remove" in sys.argv):
    # 这个方法不太可靠，因为 pip 卸载通常不会直接运行这个模块
    # 但作为额外的保障措施，可以保留它
    try:
        remove_links()
    except Exception:
        # 忽略错误，依赖 atexit 注册的方法
        pass

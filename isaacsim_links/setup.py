#!/usr/bin/env python3
"""
Isaac Sim Links - 为 Isaac Sim 和 Omni 扩展创建 IDE 符号链接的工具
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info

# 获取版本号
sys.path.insert(0, str(Path(__file__).parent / "isaacsim_links"))
from isaacsim_links import __version__

# 读取 README.md 作为长描述
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()


# 创建自定义安装类来集成链接创建功能
class CustomInstall(install):
    def run(self):
        # 先执行常规安装
        install.run(self)
        # 安装后创建链接
        self.execute(
            _post_install,
            (self.install_lib,),
            msg="创建 Isaac Sim 和 Omni 扩展符号链接",
        )


class CustomDevelop(develop):
    def run(self):
        # 先执行常规开发安装
        develop.run(self)
        # 开发模式安装后创建链接
        self.execute(
            _post_install,
            (self.install_lib,),
            msg="创建 Isaac Sim 和 Omni 扩展符号链接 (开发模式)",
        )


def _post_install(install_dir):
    """安装后执行的操作"""
    from isaacsim_links.install import install as create_links_install

    create_links_install()


# 为了在卸载时自动清理链接，我们创建一个卸载脚本
scripts_dir = Path(__file__).parent / "scripts"
scripts_dir.mkdir(exist_ok=True)

uninstall_script_path = scripts_dir / "isaacsim_links_uninstall.py"
with open(uninstall_script_path, "w") as f:
    f.write("""#!/usr/bin/env python3
# 在卸载时自动清理符号链接
import sys
import importlib.util
try:
    # 尝试导入卸载函数
    spec = importlib.util.find_spec('isaacsim_links.install')
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, 'uninstall'):
            print("正在清理 Isaac Sim 和 Omni 扩展的符号链接...")
            module.uninstall()
except Exception as e:
    print(f"清理符号链接失败: {e}", file=sys.stderr)
    print("您可能需要手动运行 'isaacsim-links --remove'", file=sys.stderr)
""")

setup(
    name="isaacsim-links",
    version=__version__,
    description="为 Isaac Sim 和 Omni 扩展创建 IDE 符号链接，改善代码自动补全",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Isaac Sim 用户",
    author_email="your-email@example.com",
    url="https://github.com/yourusername/isaacsim-links",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "isaacsim-links=isaacsim_links.cli:main",
        ],
    },
    # 注册自定义安装命令
    cmdclass={
        "install": CustomInstall,
        "develop": CustomDevelop,
    },
    # 卸载脚本
    scripts=["scripts/isaacsim_links_uninstall.py"],
)

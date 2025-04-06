#!/usr/bin/env python3
"""
在虚拟环境中运行测试的辅助脚本
"""

import os
import sys
import subprocess
import argparse
import platform
import venv
from pathlib import Path


def create_venv(venv_dir, clear=False):
    """创建虚拟环境"""
    print(f"正在创建虚拟环境: {venv_dir}")
    venv.create(venv_dir, with_pip=True, clear=clear)
    print("虚拟环境创建完成")


def get_venv_bin_dir(venv_dir):
    """获取虚拟环境中可执行文件的目录"""
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts")
    else:
        return os.path.join(venv_dir, "bin")


def upgrade_pip(venv_bin_dir):
    """升级 pip 到最新版本"""
    python_cmd = os.path.join(
        venv_bin_dir, "python.exe" if platform.system() == "Windows" else "python"
    )
    print("升级 pip 到最新版本...")
    try:
        subprocess.check_call([python_cmd, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("警告: pip 升级失败，继续使用当前版本")


def install_package(venv_bin_dir, pkg_dir, dev=True):
    """在虚拟环境中安装包"""
    pip_cmd = os.path.join(venv_bin_dir, "pip")

    # 安装测试依赖
    print("安装测试依赖...")
    subprocess.check_call(
        [pip_cmd, "install", "pytest", "pytest-cov", "pytest-mock", "pytest-timeout"]
    )

    # 安装包本身
    print(f"在{'开发' if dev else '标准'}模式下安装 isaacsim-links 包...")
    try:
        if dev:
            # 使用 PEP 517 构建后端来安装，这样可以避免直接使用 setup.py
            subprocess.check_call(
                [
                    pip_cmd,
                    "install",
                    "-e",
                    str(pkg_dir),
                    "--config-settings",
                    "editable_mode=compat",
                ]
            )
        else:
            subprocess.check_call([pip_cmd, "install", str(pkg_dir)])
        return True
    except Exception as e:
        print(f"安装失败: {e}")
        return False


def get_site_packages_dir(venv_bin_dir):
    """获取虚拟环境的 site-packages 目录"""
    python_cmd = os.path.join(venv_bin_dir, "python")
    result = subprocess.check_output(
        [python_cmd, "-c", "import site; print(site.getsitepackages()[0])"]
    )
    return result.decode("utf-8").strip()


def run_tests(venv_bin_dir, args):
    """在虚拟环境中运行测试"""
    pytest_cmd = os.path.join(venv_bin_dir, "pytest")

    # 构建 pytest 命令
    cmd = [pytest_cmd]
    if args.verbose:
        cmd.append("-v")
    if args.coverage:
        cmd.extend(["--cov=isaacsim_links", "--cov-report=term", "--cov-report=html"])
    if args.test_pattern:
        cmd.append(args.test_pattern)

    print(f"运行测试命令: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="在虚拟环境中运行 isaacsim-links 测试")
    parser.add_argument(
        "--venv-dir", default=".venv", help="虚拟环境目录 (默认: .venv)"
    )
    parser.add_argument("--recreate", action="store_true", help="重新创建虚拟环境")
    parser.add_argument(
        "--no-install", action="store_true", help="不要安装包，假设已经安装"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="输出详细的测试信息"
    )
    parser.add_argument("--coverage", action="store_true", help="生成测试覆盖率报告")
    parser.add_argument("--test-pattern", default=None, help="仅运行匹配此模式的测试")
    parser.add_argument(
        "--no-dev", action="store_true", help="使用标准模式安装，而不是开发模式"
    )

    args = parser.parse_args()

    # 获取脚本和包的路径
    script_dir = Path(__file__).parent
    venv_dir = script_dir / args.venv_dir

    # 创建虚拟环境（如果需要）
    if not venv_dir.exists() or args.recreate:
        create_venv(venv_dir, clear=args.recreate)

    # 获取虚拟环境中可执行文件的目录
    venv_bin_dir = get_venv_bin_dir(venv_dir)

    # 升级 pip
    upgrade_pip(venv_bin_dir)

    # 安装包（如果需要）
    if not args.no_install:
        success = install_package(venv_bin_dir, script_dir, dev=not args.no_dev)
        if not success:
            print("安装失败，无法继续运行测试")
            return 1

    # 运行测试
    return run_tests(venv_bin_dir, args)


if __name__ == "__main__":
    sys.exit(main())

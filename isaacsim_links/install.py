"""
安装钩子：自动在包安装时创建符号链接
"""

import os
import sys
from pathlib import Path
from .core import create_links, remove_links


def post_install():
    """安装后运行 - 创建符号链接"""
    # 安装时才创建链接，避免在开发环境中误触发
    if os.environ.get("ISAACSIM_LINKS_SKIP_INSTALL_HOOK") == "1":
        print("ISAACSIM_LINKS_SKIP_INSTALL_HOOK=1，跳过安装钩子")
        return

    print("执行安装后钩子：创建符号链接...")
    try:
        count = create_links()
        if count > 0:
            print(f"已创建 {count} 个符号链接")
        else:
            print("没有创建新的符号链接")
    except Exception as e:
        print(f"警告：安装时创建符号链接失败：{e}", file=sys.stderr)
        print("请手动运行：isaacsim-links --create", file=sys.stderr)


def pre_uninstall():
    """卸载前运行 - 清理符号链接"""
    # 卸载时才清理链接
    if os.environ.get("ISAACSIM_LINKS_SKIP_UNINSTALL_HOOK") == "1":
        print("ISAACSIM_LINKS_SKIP_UNINSTALL_HOOK=1，跳过卸载钩子")
        return

    print("执行卸载前钩子：清理符号链接...")
    try:
        count = remove_links()
        print(f"已清理 {count} 个符号链接")
    except Exception as e:
        print(f"警告：卸载时清理符号链接失败：{e}", file=sys.stderr)


# 如果安装或卸载脚本直接运行此脚本
if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command == "install":
        post_install()
    elif command == "uninstall":
        pre_uninstall()
    else:
        print(f"未知命令：{command}, 请使用 'install' 或 'uninstall'", file=sys.stderr)
        sys.exit(1)

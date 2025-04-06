"""
安装和卸载钩子
"""

import sys
from .core import create_links, remove_links


def install():
    """安装钩子，创建符号链接"""
    print("正在创建 Isaac Sim 和 Omni 扩展的符号链接...")
    try:
        count = create_links()
        print(f"\n成功创建/更新了 {count} 个链接")
        print("安装完成！现在可以在 IDE 中获得更好的代码补全支持。")
        print("提示: 您可能需要重启 IDE 或重新加载 Python 语言服务器以使更改生效。")
    except Exception as e:
        print(f"安装过程中发生错误: {e}", file=sys.stderr)
        print("请尝试手动运行 'isaacsim-links --create'", file=sys.stderr)
        return 1
    return 0


def uninstall():
    """卸载钩子，删除符号链接"""
    print("正在清理 Isaac Sim 和 Omni 扩展的符号链接...")
    try:
        count = remove_links()
        print(f"\n成功清理了 {count} 个链接")
        print("卸载完成！所有之前创建的符号链接已被移除。")
    except Exception as e:
        print(f"卸载过程中发生错误: {e}", file=sys.stderr)
        print("请尝试手动运行 'isaacsim-links --remove'", file=sys.stderr)
        return 1
    return 0

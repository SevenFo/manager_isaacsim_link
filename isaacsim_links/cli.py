#!/usr/bin/env python3
"""
Isaac Sim 链接管理工具命令行入口
"""

import argparse
import sys
from .core import create_links, remove_links


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="为 Isaac Sim 和 Omni 扩展创建/删除 IDE 符号链接以改善自动补全。"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="创建符号链接。")
    group.add_argument("--remove", action="store_true", help="删除之前创建的符号链接。")

    args = parser.parse_args()

    if args.create:
        create_links()
    elif args.remove:
        remove_links()


if __name__ == "__main__":
    main()

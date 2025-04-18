#!/usr/bin/env python3
"""
Isaac Sim 链接管理命令行工具
"""

import argparse
import sys
from isaacsim_links import core
from isaacsim_links.logger import logger


def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(
        description="为 Isaac Sim 和 Omni 扩展创建/删除 IDE 符号链接以改善自动补全"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="创建符号链接")
    group.add_argument("--remove", action="store_true", help="删除之前创建的符号链接")

    args = parser.parse_args()

    try:
        if args.create:
            core.create_links()
        elif args.remove:
            core.remove_links()
    except Exception as e:
        import traceback

        logger.error(f"发生错误: {e.__class__.__name__} {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

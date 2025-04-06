#!/usr/bin/env python3
"""
在卸载时自动清理符号链接的脚本
"""

import sys
import importlib


def main():
    """尝试导入并运行卸载功能"""
    try:
        # 尝试导入卸载函数
        from isaacsim_links.install import uninstall

        print("正在清理 Isaac Sim 和 Omni 扩展的符号链接...")
        uninstall()
        print("清理完成！")
    except ImportError:
        # 如果包已经被部分卸载，可能无法导入
        # 使用 importlib.util 尝试直接加载模块
        import importlib.util

        try:
            # 尝试找到安装模块
            spec = importlib.util.find_spec("isaacsim_links.install")
            if spec is not None:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "uninstall"):
                    print("正在清理 Isaac Sim 和 Omni 扩展的符号链接...")
                    module.uninstall()
                    print("清理完成！")
                else:
                    print("找不到卸载函数。")
            else:
                print("找不到安装模块。")
        except Exception as e:
            print(f"清理符号链接失败: {e}", file=sys.stderr)
            print("您可能需要手动运行 'isaacsim-links --remove'", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"清理符号链接失败: {e}", file=sys.stderr)
        print("您可能需要手动运行 'isaacsim-links --remove'", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

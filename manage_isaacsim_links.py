import os
import sys
import platform
import argparse
import json
from pathlib import Path
import shutil  # For potentially removing non-empty dirs if needed (use with caution)

# --- 配置 ---
# !! 修改为你环境中的实际路径 !!
ISAACSIM_SITE_PACKAGES = Path(
    "C:/Users/hp/miniforge3/envs/env_isaacsim/Lib/site-packages/isaacsim_test"
)
EXTS_DIR = ISAACSIM_SITE_PACKAGES.parent / "isaacsim_test" / "exts"  # 推断 exts 路径
LINK_RECORD_FILE = ISAACSIM_SITE_PACKAGES / "ide_symlink_record.json"
# -------------


def create_symlink_safely(source: Path, link_path: Path, links_created_record: set):
    """安全地创建符号链接并记录"""
    if not source.exists():
        print(f"  - 源路径不存在，跳过: {source}")
        return False

    if link_path.is_symlink() or link_path.exists() or link_path.is_file():
        # 检查是否是之前脚本创建的链接
        if str(link_path) in load_record():
            print(f"  - 清理旧链接: {link_path}")
            try:
                if link_path.is_symlink():
                    link_path.unlink()  # Preferred way for pathlib to remove links
                elif link_path.is_dir():
                    # Be cautious about removing directories not created as links
                    # For simplicity, we only remove if it was recorded as a link path
                    os.rmdir(link_path)  # Only if empty, might fail otherwise
                else:
                    os.remove(link_path)
            except OSError as e:
                print(f"  - 清理旧链接失败: {link_path}, 原因: {e}", file=sys.stderr)
                # Continue even if cleanup fails, maybe link creation will fix it
        elif link_path.exists():  # Exists but wasn't created by us
            print(f"  - 目标路径已存在但非脚本创建，跳过: {link_path}")
            return False

    print(f"  - 创建链接: {link_path} -> {source}")
    try:
        # 确保父目录存在
        link_path.parent.mkdir(parents=True, exist_ok=True)
        # 创建符号链接
        os.symlink(source, link_path, target_is_directory=source.is_dir())
        links_created_record.add(str(link_path))
        # 记录父目录以便清理时考虑 (可选，使清理更彻底)
        # links_created_record.add(str(link_path.parent))
        return True
    except OSError as e:
        print(f"  - 错误：创建链接失败: {e}", file=sys.stderr)
        if platform.system() == "Windows":
            print(
                "  - Windows提示: 请确保以管理员身份运行，或已启用开发人员模式。",
                file=sys.stderr,
            )
        return False
    except Exception as e:
        print(f"  - 发生意外错误: {e}", file=sys.stderr)
        return False


def create_links():
    """遍历 exts 目录并创建符号链接"""
    if not EXTS_DIR.is_dir():
        print(f"错误: Isaac Sim 'exts' 目录未找到: {EXTS_DIR}", file=sys.stderr)
        sys.exit(1)

    if platform.system() == "Windows" and not is_admin():
        print(
            "警告: 在 Windows 上创建符号链接通常需要管理员权限或开发人员模式。",
            file=sys.stderr,
        )
        print("脚本将继续尝试，但可能会失败。")

    print(f"在 '{ISAACSIM_SITE_PACKAGES}' 中为 '{EXTS_DIR}' 下的扩展创建符号链接...")
    created_links = load_record()  # Start with existing record if any
    newly_created_count = 0

    for item in EXTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("isaacsim."):  # 假设扩展都以此开头
            ext_name = item.name
            print(f"处理扩展: {ext_name}")

            # 构造目标导入路径部分 (e.g., 'core.prims' from 'isaacsim.core.prims')
            relative_import_parts = ext_name.split(".")[1:]
            if not relative_import_parts:
                print(f"  - 无法解析相对路径，跳过: {ext_name}")
                continue
            relative_import_path = Path(*relative_import_parts)  # core/prims

            # 构造实际代码的源路径 (假设结构)
            # e.g., exts/isaacsim.core.prims/isaacsim/core/prims
            internal_code_subpath = Path("isaacsim") / relative_import_path
            actual_code_path = item / internal_code_subpath

            # 检查实际代码路径是否存在 __init__.py 或 .py 文件
            if not actual_code_path.exists():
                # 尝试另一种常见模式：代码直接在扩展目录下
                # e.g., exts/isaacsim.someext/someext.py or exts/isaacsim.someext/__init__.py
                potential_py_file = item / (relative_import_parts[-1] + ".py")
                potential_init_file = item / "__init__.py"
                if item.is_dir() and potential_init_file.exists():
                    actual_code_path = item  # Link the whole extension dir
                    print(f"  - 找到模式 2: 代码在 {actual_code_path} (__init__.py)")
                elif potential_py_file.exists():
                    actual_code_path = potential_py_file  # Link the .py file
                    print(f"  - 找到模式 3: 代码在 {actual_code_path} (.py)")
                else:
                    print(f"  - 假设的代码路径未找到或无效，跳过: {actual_code_path}")
                    print(f"  - (请确认 '{ext_name}' 内的代码结构是否符合预期)")
                    continue
            elif (
                not (
                    actual_code_path.is_dir()
                    and (actual_code_path / "__init__.py").exists()
                )
                and not actual_code_path.is_file()
            ):
                print(f"  - 假设的代码路径不是有效的包或模块，跳过: {actual_code_path}")
                continue
            else:
                print(f"  - 找到模式 1: 代码在 {actual_code_path}")

            # 构造符号链接的目标路径
            # e.g., site-packages/isaacsim/core/prims
            target_link_path = ISAACSIM_SITE_PACKAGES / relative_import_path

            if create_symlink_safely(actual_code_path, target_link_path, created_links):
                newly_created_count += 1

    if (
        newly_created_count > 0 or len(created_links) > 0
    ):  # Save even if only cleanup happened
        save_record(created_links)
    print(f"\n完成。创建/更新了 {newly_created_count} 个链接。")
    print("请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。")


# (is_admin, save_record, load_record functions remain the same as before)
def is_admin():
    """检查 Windows 下是否具有管理员权限"""
    if platform.system() == "Windows":
        try:
            # This method might not be reliable across all Windows setups
            # A more robust check might involve trying a privileged operation
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:  # Catch potential errors like ImportError or AttributeError
            print("无法准确判断管理员权限，假设权限不足。")
            return False
        # Alternative naive check: Try writing to a protected location (not recommended)
    # On non-Windows, UID 0 typically means root/admin
    try:
        return os.getuid() == 0
    except AttributeError:  # os.getuid() not available on standard Windows python
        return False  # Assume not admin if we can't check


def save_record(links_created):
    """将创建的链接记录保存到文件"""
    print(f"记录链接状态到: {LINK_RECORD_FILE}")
    try:
        # Store as list for consistent ordering in JSON
        link_list = sorted(list(links_created))
        with open(LINK_RECORD_FILE, "w") as f:
            json.dump(link_list, f, indent=4)
    except IOError as e:
        print(f"错误：无法写入记录文件 {LINK_RECORD_FILE}: {e}", file=sys.stderr)


def load_record():
    """从文件加载已创建的链接记录"""
    if not LINK_RECORD_FILE.exists():
        return set()
    try:
        with open(LINK_RECORD_FILE, "r") as f:
            # Ensure items loaded are strings, handle potential type issues if file was manually edited
            data = json.load(f)
            if isinstance(data, list):
                return set(str(item) for item in data)
            else:
                # Handle older format if it was just a set saved incorrectly
                print(f"警告：记录文件格式非预期 (非列表)，尝试转换。", file=sys.stderr)
                return set(str(item) for item in data)

    except (IOError, json.JSONDecodeError) as e:
        print(f"警告：无法读取或解析记录文件 {LINK_RECORD_FILE}: {e}", file=sys.stderr)
        return set()
    except Exception as e:  # Catch other potential errors during loading
        print(f"加载记录时发生未知错误: {e}", file=sys.stderr)
        return set()


def is_directory_empty(dir_path: Path) -> bool:
    """检查目录是否为空 (忽略常见的系统隐藏文件)"""
    # More robust check might be needed depending on OS and hidden files
    try:
        # Basic check: list directory contents
        items = list(dir_path.iterdir())
        # Example: Ignore .DS_Store on macOS
        if platform.system() == "Darwin":
            items = [item for item in items if item.name != ".DS_Store"]
        # Example: Ignore Thumbs.db on Windows (less common now)
        if platform.system() == "Windows":
            items = [item for item in items if item.name.lower() != "thumbs.db"]

        return len(items) == 0
    except FileNotFoundError:
        return False  # Directory doesn't exist, so it's "empty" in a way
    except OSError as e:
        print(f"    - 检查目录 '{dir_path}' 是否为空时出错: {e}", file=sys.stderr)
        return False  # Assume not empty if we can't check


def remove_links():
    """根据记录文件删除创建的符号链接及其可能产生的空父目录"""
    print(f"正在根据记录文件 '{LINK_RECORD_FILE}' 删除符号链接...")
    links_to_remove = load_record()

    if not links_to_remove:
        print("记录文件为空或未找到，无需删除。")
        return

    if platform.system() == "Windows" and not is_admin():
        print(
            "警告: 在 Windows 上删除符号链接或目录可能需要管理员权限。", file=sys.stderr
        )

    removed_count = 0
    failed_to_remove = set()  # 保留未能成功处理的记录
    anomalies = set()  # 记录存在但非预期的链接

    # 按路径深度反向排序，优先处理深层路径
    sorted_paths = sorted(
        list(links_to_remove), key=lambda p: len(Path(p).parts), reverse=True
    )

    for link_str in sorted_paths:
        link_path = Path(link_str)
        parent_dir = link_path.parent
        removed_this_iteration = False
        is_anomaly = False

        print(f"\n处理记录: {link_path}")

        try:
            # 1. 检查路径是否存在以及是否是符号链接
            if link_path.is_symlink():
                print(f"  - 是符号链接，尝试删除...")
                link_path.unlink()
                print(f"    - 成功删除符号链接。")
                removed_this_iteration = True
                removed_count += 1
            elif link_path.exists():
                # 2. 路径存在，但不是符号链接 - 这是异常情况
                print(f"  - 警告：路径存在但不是符号链接。")
                print(f"    - 保留此路径，并在记录中标记为异常。")
                is_anomaly = True
                anomalies.add(link_str)
                failed_to_remove.add(link_str)  # 保留异常记录
            else:
                # 3. 路径不存在 - 认为已删除或从未成功创建
                print(f"  - 路径不存在，无需删除。")
                removed_this_iteration = True  # 视为已成功处理

            # 4. 如果是异常情况，跳过父目录清理
            if is_anomaly:
                continue

            # 5. 如果成功删除或路径本就不存在，尝试清理空的父目录 (***移除 processed_parents 检查***)
            if removed_this_iteration:
                print(f"  - 尝试向上清理空的父目录，从 {parent_dir} 开始...")
                current_parent = parent_dir
                # 防止无限循环或超出预期范围
                while (
                    current_parent.exists()
                    and current_parent != ISAACSIM_SITE_PACKAGES
                    and current_parent != current_parent.parent
                ):
                    print(f"    - 检查目录是否为空: {current_parent}")
                    if is_directory_empty(current_parent):
                        try:
                            print(f"      - 目录为空，尝试删除...")
                            current_parent.rmdir()
                            print(f"        - 成功删除空目录。")
                            # 删除成功后，将 current_parent 移到上一级继续检查
                            parent_before_rm = current_parent
                            current_parent = current_parent.parent
                            print(f"        - 移动到上一级目录检查: {current_parent}")
                        except OSError as e:
                            print(
                                f"      - 删除空目录 '{current_parent}' 失败: {e}",
                                file=sys.stderr,
                            )
                            # 如果删除失败（可能权限问题或瞬间文件出现），停止这条分支的清理
                            break
                        except Exception as e_parent:
                            print(
                                f"      - 清理父目录 '{current_parent}' 时发生意外错误: {e_parent}",
                                file=sys.stderr,
                            )
                            break  # 停止清理
                    else:
                        print(f"      - 目录非空，停止向上清理。")
                        # 目录非空，没有必要再检查它的父级了，停止这条分支
                        break
                print(f"  - 父目录向上清理完成或中止。")

        except OSError as e:
            print(
                f"  - 错误：处理路径 '{link_path}' 时发生 OS 错误: {e}", file=sys.stderr
            )
            failed_to_remove.add(link_str)
        except Exception as e:
            print(
                f"  - 错误：处理路径 '{link_path}' 时发生意外错误: {e}", file=sys.stderr
            )
            failed_to_remove.add(link_str)

    # --- 总结和记录文件处理 ---
    print("\n--- 删除操作总结 ---")
    print(f"处理记录条目数: {len(links_to_remove)}")
    # Correct calculation: Total processed = Successfully removed symlinks + Non-existent paths
    processed_successfully_count = removed_count + (
        len(links_to_remove) - len(failed_to_remove) - len(anomalies)
    )
    print(
        f"成功删除或确认不存在的符号链接数: {processed_successfully_count}"
    )  # More accurate count
    print(f"检测到异常 (存在但非符号链接) 数: {len(anomalies)}")
    print(f"处理失败或保留的记录数: {len(failed_to_remove)}")

    if not failed_to_remove:
        print("\n所有记录的链接已成功处理。正在删除记录文件...")
        try:
            if LINK_RECORD_FILE.exists():
                LINK_RECORD_FILE.unlink()
                print("记录文件已删除。")
            else:
                print("记录文件不存在，无需删除。")
        except OSError as e:
            print(f"警告：无法删除记录文件 {LINK_RECORD_FILE}: {e}", file=sys.stderr)
    else:
        print("\n部分链接未能删除或被标记为异常，更新记录文件以保留这些条目。")
        save_record(failed_to_remove)  # 保存未能处理的记录

    if failed_to_remove:
        print("\n以下记录未能成功移除或被标记为异常，已保留在记录文件中:")
        for item in sorted(list(failed_to_remove)):
            print(f"  - {item}")
        print("请检查上述错误信息或手动处理这些路径。")


def main():
    parser = argparse.ArgumentParser(
        description="为 Isaac Sim 扩展创建/删除 IDE 符号链接以改善自动补全。"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="创建符号链接。")
    group.add_argument("--remove", action="store_true", help="删除之前创建的符号链接。")

    args = parser.parse_args()

    # 检查基础路径是否存在
    if not ISAACSIM_SITE_PACKAGES.is_dir():
        print(
            f"错误: Isaac Sim site-packages 目录未找到: {ISAACSIM_SITE_PACKAGES}",
            file=sys.stderr,
        )
        print("请编辑脚本顶部的 'ISAACSIM_SITE_PACKAGES' 变量。")
        sys.exit(1)
    # 确保 EXTS_DIR 也存在 (主要用于 create，但 remove 可能也需要参考)
    if args.create and not EXTS_DIR.is_dir():
        print(f"错误: Isaac Sim 'exts' 目录未找到: {EXTS_DIR}", file=sys.stderr)
        print("请确认 Isaac Sim 安装结构或编辑脚本中的 'EXTS_DIR'。")
        sys.exit(1)

    if args.create:
        # Make sure create_links is defined/copied from previous version
        if "create_links" in globals() and callable(globals()["create_links"]):
            create_links()
        else:
            print("错误：create_links 函数未定义。")
    elif args.remove:
        remove_links()


if __name__ == "__main__":
    main()

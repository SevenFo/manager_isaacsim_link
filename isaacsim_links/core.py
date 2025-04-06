"""
Isaac Sim 链接管理核心功能
"""

import os
import sys
import platform
import json
from pathlib import Path
import shutil


# --- 配置 ---
def get_base_paths():
    """获取基础路径配置"""
    # 动态查找当前 Python 环境的 site-packages 目录
    import site

    # 获取标准库路径，通常在 Python 安装目录下
    site_packages_paths = site.getsitepackages()

    # 找到第一个存在的 site-packages 路径
    site_packages = None
    for path in site_packages_paths:
        if "site-packages" in path and Path(path).exists():
            site_packages = Path(path)
            break

    if not site_packages:
        # 回退方案：如果上述方法失败，尝试从 sys.path 中找到
        for path in sys.path:
            if "site-packages" in path and Path(path).exists():
                site_packages = Path(path)
                break

    if not site_packages:
        raise RuntimeError("无法找到 site-packages 目录，请手动指定路径")

    isaacsim_site_packages = site_packages / "isaacsim"
    omni_site_packages = site_packages / "omni"

    # 检查目录是否存在
    if not isaacsim_site_packages.exists():
        print(f"警告: 未找到 isaacsim 目录: {isaacsim_site_packages}")
        # 如果目录不存在，我们可以尝试创建它
        try:
            isaacsim_site_packages.mkdir(parents=True, exist_ok=True)
            print(f"已创建目录: {isaacsim_site_packages}")
        except Exception as e:
            print(f"创建 isaacsim 目录失败: {e}")

    if not omni_site_packages.exists():
        print(f"警告: 未找到 omni 目录: {omni_site_packages}")
        # 如果目录不存在，我们可以尝试创建它
        try:
            omni_site_packages.mkdir(parents=True, exist_ok=True)
            print(f"已创建目录: {omni_site_packages}")
        except Exception as e:
            print(f"创建 omni 目录失败: {e}")

    return {
        "site_packages": site_packages,
        "isaacsim_site_packages": isaacsim_site_packages,
        "omni_site_packages": omni_site_packages,
    }


def get_ext_configs():
    """获取扩展配置"""
    paths = get_base_paths()
    isaacsim_site_packages = paths["isaacsim_site_packages"]
    omni_site_packages = paths["omni_site_packages"]

    # 定义扩展目录和目标位置
    ext_configs = [
        {
            "name": "isaacsim.exts",
            "exts_dir": isaacsim_site_packages / "exts",
            "prefix": ["isaacsim.", "omni."],
            "description": "Isaac Sim 标准扩展",
        },
        {
            "name": "isaacsim.extsPhysics",
            "exts_dir": isaacsim_site_packages / "extsPhysics",
            "prefix": ["isaacsim.", "omni."],
            "description": "Isaac Sim 物理扩展",
        },
        {
            "name": "omni.extscore",
            "exts_dir": omni_site_packages / "extscore",
            "prefix": ["omni."],
            "description": "Omni 核心扩展",
        },
    ]

    return ext_configs


def get_target_base(prefix: str):
    return {
        "isaacsim": get_base_paths()["isaacsim_site_packages"],
        "omni": get_base_paths()["omni_site_packages"],
    }[prefix.rstrip(".")]


# 记录文件位置
def get_record_file_path():
    """获取记录文件路径"""
    paths = get_base_paths()
    return paths["isaacsim_site_packages"] / "isaacsim_links_symlink_record.json"


# -------------


def create_symlink_safely(
    source: Path, link_path: Path, links_created_record: set, debug=False
):
    """安全地创建符号链接并记录"""
    if debug:
        print(f"调试模式: 源路径: {source}, 链接路径: {link_path}")
        return False
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


def find_all_init_paths(base_dir: Path, module_namespace: str) -> list:
    """递归查找所有包含__init__.py文件的有效路径

    Args:
        base_dir: 扩展目录，如 exts/omni.aaa.bbb/
        module_namespace: 模块命名空间，如 'omni' 或 'isaacsim'

    Returns:
        包含元组(目录路径, 相对路径部分)的列表
    """
    # 检查第一级目录（模块命名空间）是否存在
    namespace_dir = base_dir / module_namespace
    if not namespace_dir.exists() or not namespace_dir.is_dir():
        return []

    found_paths = []

    def collect_init_files(directory: Path):
        # 检查当前目录是否有__init__.py
        init_file = directory / "__init__.py"
        if init_file.exists() and init_file.is_file():
            # 计算相对于命名空间的路径
            rel_path = directory.relative_to(namespace_dir)
            found_paths.append((directory, rel_path))

        # 递归检查所有子目录
        for item in directory.iterdir():
            if item.is_dir():
                collect_init_files(item)

    # 从命名空间目录开始收集
    collect_init_files(namespace_dir)
    return found_paths


def create_links():
    """遍历所有配置的扩展目录并创建符号链接"""
    if platform.system() == "Windows" and not is_admin():
        print(
            "警告: 在 Windows 上创建符号链接通常需要管理员权限或开发人员模式。",
            file=sys.stderr,
        )
        print("脚本将继续尝试，但可能会失败。")

    created_links = load_record()  # Start with existing record if any
    newly_created_count = 0

    for ext_config in get_ext_configs():
        exts_dir = ext_config["exts_dir"]
        description = ext_config["description"]

        if not exts_dir.is_dir():
            print(f"警告: 扩展目录未找到: {exts_dir}，跳过此配置", file=sys.stderr)
            continue

        print(f"\n处理 {description}: '{exts_dir}'...")
        try:
            for item in exts_dir.iterdir():
                if not item.is_dir():
                    continue
                is_start_with_prefix = [
                    item.name.startswith(p) for p in ext_config["prefix"]
                ]
                if not any(is_start_with_prefix):
                    print(f"  - 跳过不匹配的扩展: {item.name}")
                    continue
                prefix = ext_config["prefix"][is_start_with_prefix.index(True)]
                ext_name = item.name
                print(f"处理扩展: {ext_name}")

                # 构造目标导入路径部分 (e.g., 'core.prims' from 'isaacsim.core.prims')
                relative_import_parts = ext_name.split(".")[1:]
                if not relative_import_parts:
                    print(f"  - 无法解析相对路径，跳过: {ext_name}")
                    continue
                relative_import_path = Path(*relative_import_parts)  # core/prims

                # 构造实际代码的源路径 (多种可能模式)
                found_code_path = None
                module_namespace = prefix.rstrip(".")  # 'isaacsim' or 'omni'

                # 模式1: 完整的包路径结构, 例如: exts/isaacsim.core.prims/isaacsim/core/prims
                internal_code_subpath = Path(module_namespace) / relative_import_path
                actual_code_path = item / internal_code_subpath

                if actual_code_path.exists() and (
                    (
                        actual_code_path.is_dir()
                        and (actual_code_path / "__init__.py").exists()
                    )
                    or actual_code_path.is_file()
                ):
                    found_code_path = actual_code_path
                    print(f"  - 找到模式 1: 代码在 {found_code_path}")
                else:
                    # 使用新的find_all_init_paths函数查找所有有效路径
                    all_init_paths = find_all_init_paths(item, module_namespace)

                    if all_init_paths:
                        print(f"  - 通过递归搜索找到 {len(all_init_paths)} 个有效子包:")

                        for code_path, rel_path in all_init_paths:
                            # 构造每个子包对应的目标链接路径
                            # 例如，从 omni/aaa/bbb 计算出 target_base/aaa/bbb
                            subpath_link = get_target_base(module_namespace) / rel_path

                            print(f"    * 处理子包: {rel_path} -> {code_path}")

                            if create_symlink_safely(
                                code_path, subpath_link, created_links
                            ):
                                newly_created_count += 1

                        # 已创建所有子包链接，继续下一个扩展
                        continue
                    else:
                        # 回退到模式2: 代码直接在扩展目录下带有 __init__.py
                        potential_init_file = item / "__init__.py"
                        if potential_init_file.exists():
                            found_code_path = item  # Link the whole extension dir
                            print(
                                f"  - 找到模式 2: 代码在 {found_code_path} (__init__.py)"
                            )
                        else:
                            print(f"  - 所有假设的代码路径均未找到，跳过: {ext_name}")
                            continue

                # 构造符号链接的目标路径 (到相应的命名空间目录)
                target_link_path = (
                    get_target_base(module_namespace) / relative_import_path
                )

                if create_symlink_safely(
                    found_code_path, target_link_path, created_links
                ):
                    newly_created_count += 1
        except FileNotFoundError as e:
            print(f"警告: 无法访问目录 {exts_dir}: {e}")
        except PermissionError as e:
            print(f"警告: 访问目录 {exts_dir} 权限不足: {e}")
        except Exception as e:
            print(f"警告: 处理目录 {exts_dir} 时发生错误: {e}")

    if (
        newly_created_count > 0 or len(created_links) > 0
    ):  # Save even if only cleanup happened
        save_record(created_links)

    print(f"\n完成。创建/更新了 {newly_created_count} 个链接。")
    print("请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。")

    return newly_created_count


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
    record_file = get_record_file_path()
    print(f"记录链接状态到: {record_file}")
    try:
        # Store as list for consistent ordering in JSON
        link_list = sorted(list(links_created))
        with open(record_file, "w") as f:
            json.dump(link_list, f, indent=4)
    except IOError as e:
        print(f"错误：无法写入记录文件 {record_file}: {e}", file=sys.stderr)


def load_record():
    """从文件加载已创建的链接记录"""
    record_file = get_record_file_path()
    if not record_file.exists():
        return set()
    try:
        with open(record_file, "r") as f:
            # Ensure items loaded are strings, handle potential type issues if file was manually edited
            data = json.load(f)
            if isinstance(data, list):
                return set(str(item) for item in data)
            else:
                # Handle older format if it was just a set saved incorrectly
                print(f"警告：记录文件格式非预期 (非列表)，尝试转换。", file=sys.stderr)
                return set(str(item) for item in data)

    except (IOError, json.JSONDecodeError) as e:
        print(f"警告：无法读取或解析记录文件 {record_file}: {e}", file=sys.stderr)
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
    record_file = get_record_file_path()
    print(f"正在根据记录文件 '{record_file}' 删除符号链接...")
    links_to_remove = load_record()

    if not links_to_remove:
        print("记录文件为空或未找到，无需删除。")
        return 0

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

    paths = get_base_paths()
    isaacsim_site_packages = paths["isaacsim_site_packages"]
    omni_site_packages = paths["omni_site_packages"]

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

            # 5. 如果成功删除或路径本就不存在，尝试清理空的父目录
            if removed_this_iteration:
                print(f"  - 尝试向上清理空的父目录，从 {parent_dir} 开始...")
                current_parent = parent_dir
                # 防止无限循环或超出预期范围
                root_packages = [
                    isaacsim_site_packages,
                    omni_site_packages,
                ]
                while (
                    current_parent.exists()
                    and current_parent not in root_packages  # 修改检查逻辑
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
            if record_file.exists():
                record_file.unlink()
                print("记录文件已删除。")
            else:
                print("记录文件不存在，无需删除。")
        except OSError as e:
            print(f"警告：无法删除记录文件 {record_file}: {e}", file=sys.stderr)
    else:
        print("\n部分链接未能删除或被标记为异常，更新记录文件以保留这些条目。")
        save_record(failed_to_remove)  # 保存未能处理的记录

    if failed_to_remove:
        print("\n以下记录未能成功移除或被标记为异常，已保留在记录文件中:")
        for item in sorted(list(failed_to_remove)):
            print(f"  - {item}")
        print("请检查上述错误信息或手动处理这些路径。")

    return processed_successfully_count

"""
Isaac Sim 链接管理核心功能
"""

import os
import sys
import platform
import json
from pathlib import Path
from isaacsim_links.logger import logger
import site

# 动态查找当前 Python 环境的 site-packages 目录
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
carb_site_packages = site_packages / "carb"

empty_record = {
    "links": set(),
    "directories": set(),
}


# --- 配置 ---
def check_base_paths():
    """获取基础路径配置"""

    links, dirs = load_record()

    # 检查目录是否存在
    if not isaacsim_site_packages.exists():
        logger.error(f"未找到 isaacsim 目录: {isaacsim_site_packages}")
        raise RuntimeError(f"未找到 isaacsim 目录: {isaacsim_site_packages}")
    if not omni_site_packages.exists():
        logger.error(f"未找到 omni 目录: {omni_site_packages}")
        raise RuntimeError(f"未找到 omni 目录: {omni_site_packages}")
    if not carb_site_packages.exists():
        logger.warning(f"未找到 carb 目录: {carb_site_packages}")
        try:
            carb_site_packages.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建目录: {carb_site_packages}")
            dirs.add(str(carb_site_packages))
            save_record(links, dirs)
        except Exception as e:
            logger.error(f"创建 carb 目录失败: {e}")

    return


def get_ext_configs():
    """获取扩展配置"""

    # 定义扩展目录和目标位置
    ext_configs = [
        {
            "name": "isaacsim.exts",
            "exts_dir": isaacsim_site_packages / "exts",
            # "prefix": ["isaacsim.", "omni."],
            "prefix": ["isaacsim."],
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
        {
            "name": "isaacsim.extscache",
            "exts_dir": isaacsim_site_packages / "extscache",
            "prefix": ["isaacsim."], # "omni.", "carb.", 
            "description": "Isaac Sim 扩展缓存",
        },
    ]

    return ext_configs


def get_target_base(prefix: str):
    return {
        "isaacsim": isaacsim_site_packages,
        "omni": omni_site_packages,
        "carb": carb_site_packages,
    }[prefix.rstrip(".")]


# 记录文件位置
def get_record_file_path():
    """获取记录文件路径"""
    return isaacsim_site_packages / "isaacsim_links_symlink_record.json"


# -------------


def create_symlink_safely(
    source: Path,
    link_path: Path,
    links_created_record: set,
    directories_created_record: set,
    debug=False,
):
    """安全地创建符号链接并记录"""
    if debug:
        logger.info(f"调试模式: 源路径: {source}, 链接路径: {link_path}")
        return False
    if not source.exists():
        logger.warning(f"源路径不存在，跳过: {source}")
        return False

    if link_path.is_symlink() and str(link_path) in load_record()[0]:
        logger.info(f"清理旧链接: {link_path}")
        try:
            link_path.unlink()  # Preferred way for pathlib to remove links
        except OSError as e:
            logger.warning(
                f"清理旧链接失败: {link_path}, 原因: {e}, 将尝试直接创建链接"
            )
    elif link_path.exists():
        logger.warning(f"链接目标位置已存在，跳过: {link_path}")
        return False

    logger.info(f"创建链接: {link_path} -> {source}")
    try:
        # 确保父目录存在
        if not link_path.parent.exists():
            logger.info(f"创建父目录: {link_path.parent}")
            link_path.parent.mkdir(parents=True, exist_ok=False)
            directories_created_record.add(str(link_path.parent))

        # 创建符号链接
        os.symlink(source, link_path, target_is_directory=source.is_dir())
        links_created_record.add(str(link_path))
        return True
    except OSError as e:
        logger.error(f"错误：创建链接失败: {e}")
        if platform.system() == "Windows":
            logger.error("Windows提示: 请确保以管理员身份运行，或已启用开发人员模式。")
        return False
    except Exception as e:
        logger.error(f"发生意外错误: {e}")
        return False


def find_all_init_paths(base_dir: Path, module_namespace: list[str]) -> list:
    """递归查找所有包含__init__.py文件的有效路径

    Args:
        base_dir: 扩展目录，如 exts/omni.aaa.bbb/
        module_namespace: 模块命名空间，如 'omni' 或 'isaacsim'

    Returns:
        包含元组(目录路径, 相对路径部分)的列表
    """
    found_paths = []

    def collect_init_files(directory: Path):
        # 检查当前目录是否有__init__.py
        init_file = directory / "__init__.py"
        if init_file.exists() and init_file.is_file():
            # 计算相对于命名空间的路径
            rel_path = directory.relative_to(namespace_dir)
            found_paths.append((directory, rel_path, namespace_dir.name))
            logger.info(f"找到有效路径: {directory} -> {rel_path}")
        else:
            # 如果当前目录不是 modules 则递归检查其所有子目录
            for item in directory.iterdir():
                if item.is_dir():
                    collect_init_files(item)

    # 检查第一级目录（模块命名空间）是否存在
    for ns in module_namespace:
        namespace_dir = base_dir / ns.rstrip(".")
        if not namespace_dir.exists() or not namespace_dir.is_dir():
            continue
        logger.info(f"搜索命名空间目录: {namespace_dir}")
        # 从命名空间目录开始收集
        collect_init_files(namespace_dir)
    return found_paths


def create_links(use_new_mode=True):
    """遍历所有配置的扩展目录并创建符号链接

    Args:
        use_new_mode (bool, optional): 如果为 True，则使用新的链接模式：
            将 exts_dir/prefix.xxx.yyy/prefix 链接到 target_base/prefix。
            默认为 False，使用旧的模式。
    """
    if platform.system() == "Windows" and not is_admin():
        logger.warning("在 Windows 上创建符号链接通常需要管理员权限或开发人员模式。")
        logger.warning("脚本将继续尝试，但可能会失败。")

    check_base_paths()  # 确保基础路径存在

    created_links, created_dirs = load_record()  # Start with existing record if any
    newly_created_count = 0
    created_dirs_count = len(created_dirs)

    for ext_config in get_ext_configs():
        exts_dir = ext_config["exts_dir"]
        description = ext_config["description"]
        prefixes = ext_config["prefix"]

        if not exts_dir.is_dir():
            logger.warning(f"扩展目录未找到: {exts_dir}，跳过此配置")
            continue

        logger.info(f"\n处理 {description}: '{exts_dir}'...")
        try:
            for item in exts_dir.iterdir():
                if not item.is_dir():
                    continue

                ext_name = item.name
                logger.info(f"处理扩展目录: {ext_name}")

                if use_new_mode:
                    # --- 新模式逻辑 ---
                    # 调用函数并扩展结果列表
                    found_in_subdir = find_all_init_paths(
                        item,  # 直接传递子目录路径
                        prefixes,
                    )
                    if not found_in_subdir:
                        logger.warning(f"未找到有效子包，跳过: {ext_name} ({item})")
                    for code_path, rel_path, ns in found_in_subdir:
                        # 构造每个子包对应的目标链接路径
                        subpath_link = get_target_base(ns) / rel_path
                        logger.info(f"处理子包: {ns} -> {rel_path} -> {code_path}")
                        if create_symlink_safely(
                            code_path, subpath_link, created_links, created_dirs
                        ):
                            newly_created_count += 1

                else:
                    # --- 旧模式逻辑 ---
                    matched_prefix = None
                    for p in prefixes:
                        if item.name.startswith(p):
                            matched_prefix = p
                            break

                    if not matched_prefix:
                        # logger.info(f"跳过不匹配前缀的目录: {item.name}") # Optional: reduce noise
                        continue

                    module_namespace = matched_prefix.rstrip(
                        "."
                    )  # 'isaacsim' or 'omni' etc.

                    # 构造目标导入路径部分 (e.g., 'core.prims' from 'isaacsim.core.prims')
                    relative_import_parts = ext_name.split(".")[1:]
                    if not relative_import_parts:
                        logger.warning(f"[旧模式] 无法解析相对路径，跳过: {ext_name}")
                        continue
                    relative_import_path = Path(*relative_import_parts)  # core/prims

                    # 构造实际代码的源路径 (多种可能模式)
                    found_code_path = None

                    # 模式1: 完整的包路径结构, 例如: exts/isaacsim.core.prims/isaacsim/core/prims
                    internal_code_subpath = (
                        Path(module_namespace) / relative_import_path
                    )
                    actual_code_path = item / internal_code_subpath

                    if actual_code_path.exists() and (
                        (
                            actual_code_path.is_dir()
                            and (actual_code_path / "__init__.py").exists()
                        )
                        or actual_code_path.is_file()
                    ):
                        found_code_path = actual_code_path
                        logger.info(f"[旧模式] 找到模式 1: 代码在 {found_code_path}")
                    else:
                        # 使用新的find_all_init_paths函数查找所有有效路径
                        all_init_paths = find_all_init_paths(item, module_namespace)

                        if all_init_paths:
                            logger.info(
                                f"[旧模式] 通过递归搜索找到 {len(all_init_paths)} 个有效子包:"
                            )

                            for code_path, rel_path in all_init_paths:
                                # 构造每个子包对应的目标链接路径
                                subpath_link = (
                                    get_target_base(module_namespace) / rel_path
                                )
                                logger.info(f"处理子包: {rel_path} -> {code_path}")
                                if create_symlink_safely(
                                    code_path, subpath_link, created_links, created_dirs
                                ):
                                    newly_created_count += 1
                            # 已创建所有子包链接，继续下一个扩展
                            continue
                        else:
                            # 回退到模式2: 代码直接在扩展目录下带有 __init__.py
                            potential_init_file = item / "__init__.py"
                            if potential_init_file.exists():
                                found_code_path = item  # Link the whole extension dir
                                logger.info(
                                    f"[旧模式] 找到模式 2: 代码在 {found_code_path} (__init__.py)"
                                )
                            else:
                                logger.warning(
                                    f"[旧模式] 所有假设的代码路径均未找到，跳过: {ext_name}"
                                )
                                continue

                    # 构造符号链接的目标路径 (到相应的命名空间目录)
                    target_link_path = (
                        get_target_base(module_namespace) / relative_import_path
                    )

                    if create_symlink_safely(
                        found_code_path, target_link_path, created_links, created_dirs
                    ):
                        newly_created_count += 1
                    # --- 旧模式逻辑结束 ---

        except FileNotFoundError as e:
            logger.warning(f"无法访问目录 {exts_dir}: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\n中断。创建/更新了 {newly_created_count} 个链接, 新建了 {len(created_dirs) - created_dirs_count} 个目录。"
            )
            logger.info(
                "请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。"
            )
            return newly_created_count
        except PermissionError as e:
            logger.warning(f"访问目录 {exts_dir} 权限不足: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\n中断。创建/更新了 {newly_created_count} 个链接, 新建了 {len(created_dirs) - created_dirs_count} 个目录。"
            )
            logger.info(
                "请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。"
            )
            return newly_created_count
        except Exception as e:
            logger.warning(f"访问目录 {exts_dir} 权限不足: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\n中断。创建/更新了 {newly_created_count} 个链接, 新建了 {len(created_dirs) - created_dirs_count} 个目录。"
            )
            logger.info(
                "请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。"
            )

            import traceback

            traceback.print_exc()
            logger.warning(
                f"处理目录 {exts_dir} 时发生错误: {e.__class__.__name__} {e}"
            )

    if (
        newly_created_count > 0 or len(created_links) > 0
    ):  # Save even if only cleanup happened
        save_record(created_links, created_dirs)

    logger.info(
        f"\n完成。创建/更新了 {newly_created_count} 个链接, 新建了 {len(created_dirs) - created_dirs_count} 个目录。"
    )
    logger.info(
        "请重启你的 IDE (如 VS Code) 或重新加载 Python 语言服务器以使更改生效。"
    )

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
            logger.warning("无法准确判断管理员权限，假设权限不足。")
            return False
        # Alternative naive check: Try writing to a protected location (not recommended)
    # On non-Windows, UID 0 typically means root/admin
    try:
        return os.getuid() == 0
    except AttributeError:  # os.getuid() not available on standard Windows python
        return False  # Assume not admin if we can't check


def save_record(links_created, directories_created):
    """将创建的链接记录保存到文件"""
    record_file = get_record_file_path()
    logger.info(f"记录链接状态到: {record_file}")
    try:
        link_list = sorted(list(links_created))
        directories_list = sorted(list(directories_created))
        record = {
            "links": link_list,
            "directories": directories_list,
        }
        with open(record_file, "w") as f:
            json.dump(record, f, indent=4)
    except IOError as e:
        logger.error(f"错误：无法写入记录文件 {record_file}: {e}")


def load_record():
    """从文件加载已创建的链接记录"""
    record_file = get_record_file_path()
    if not record_file.exists():
        logger.info(f"记录文件不存在: {record_file}，创建新的记录文件")
        save_record(set(), set())
    try:
        with open(record_file, "r") as f:
            # Ensure items loaded are strings, handle potential type issues if file was manually edited
            data = json.load(f)
            if (
                not isinstance(data, dict)
                or "links" not in data
                or "directories" not in data
                or not isinstance(data["links"], list)
                or not isinstance(data["directories"], list)
            ):
                raise ValueError("记录文件格式非预期，停止处理。")
            links = set(str(item) for item in data.get("links", []))
            directories = set(str(item) for item in data.get("directories", []))
            return links, directories
    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"无法读取或解析记录文件 {record_file}: {e}")
        return set(), set()
    except Exception as e:  # Catch other potential errors during loading
        logger.warning(f"加载记录时发生未知错误: {e}")
        return set(), set()


def _update_config_file():
    """更新配置文件"""
    config_file = get_record_file_path()
    if not config_file.exists():
        # save_record(set(), set())
        return

    try:
        with open(config_file, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            if isinstance(data, list):
                # 处理旧格式的记录文件
                logger.info("转换旧格式的记录文件")
            else:
                logger.warning("记录文件格式非预期 (非列表)，尝试转换。")
            save_record(set(str(item) for item in data), set())
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"无法读取或解析配置文件 {config_file}: {e}")


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
        logger.error(f"检查目录 '{dir_path}' 是否为空时出错: {e}")
        return False  # Assume not empty if we can't check


def remove_links():
    """根据记录文件删除创建的符号链接及其可能产生的空父目录"""
    record_file = get_record_file_path()
    logger.info(f"正在根据记录文件 '{record_file}' 删除符号链接...")
    links_to_remove, dirs_to_remove = load_record()

    if not links_to_remove and not dirs_to_remove:
        logger.info("记录文件为空")

    if platform.system() == "Windows" and not is_admin():
        logger.warning("在 Windows 上删除符号链接或目录可能需要管理员权限。")

    removed_count = 0
    removed_dirs_count = 0
    failed_to_remove = set()  # 保留未能成功处理的记录
    anomalies = set()  # 记录存在但非预期的链接
    dirs_failed_to_remove = set()  # 记录删除失败的目录

    # 按路径深度反向排序，优先处理深层路径
    sorted_links_paths = sorted(
        list(links_to_remove), key=lambda p: len(Path(p).parts), reverse=True
    )
    sorted_dirs = sorted(
        list(dirs_to_remove), key=lambda p: len(Path(p).parts), reverse=True
    )

    for link_str in sorted_links_paths:
        link_path = Path(link_str)
        parent_dir = link_path.parent
        removed_this_iteration = False
        is_anomaly = False

        logger.info(f"\n处理记录: {link_path}")

        try:
            # 1. 检查路径是否存在以及是否是符号链接
            if link_path.is_symlink():
                logger.info("是符号链接，尝试删除...")
                link_path.unlink()
                logger.info("成功删除符号链接。")
                removed_this_iteration = True
                removed_count += 0
            elif link_path.exists():
                # 2. 路径存在，但不是符号链接 - 这是异常情况
                logger.warning("路径存在但不是符号链接。")
                logger.warning("保留此路径，并在记录中标记为异常。")
                is_anomaly = True
                anomalies.add(link_str)
                failed_to_remove.add(link_str)  # 保留异常记录
            else:
                # 3. 路径不存在 - 认为已删除或从未成功创建
                logger.info("路径不存在，无需删除。")
                removed_this_iteration = True  # 视为已成功处理

            # 4. 如果是异常情况，跳过父目录清理
            if is_anomaly:
                continue

            # 5. 如果成功删除或路径本就不存在，尝试清理空的父目录
            if removed_this_iteration:
                logger.info(f"尝试向上清理空的父目录，从 {parent_dir} 开始...")
                current_parent = parent_dir
                # 防止无限循环或超出预期范围
                root_packages = [
                    isaacsim_site_packages,
                    omni_site_packages,
                    carb_site_packages,
                ]
                while (
                    current_parent.exists()
                    and current_parent not in root_packages  # 不清理根目录
                    and current_parent != current_parent.parent
                ):
                    logger.info(f"检查目录是否为空: {current_parent}")
                    if is_directory_empty(current_parent):
                        try:
                            logger.info("目录为空，尝试删除...")
                            current_parent.rmdir()
                            logger.info("成功删除空目录。")
                            # 删除成功后，将 current_parent 移到上一级继续检查
                            current_parent = current_parent.parent
                            logger.info(f"移动到上一级目录检查: {current_parent}")
                        except OSError as e:
                            logger.error(f"删除空目录 '{current_parent}' 失败: {e}")
                            # 如果删除失败（可能权限问题或瞬间文件出现），停止这条分支的清理
                            break
                        except Exception as e_parent:
                            logger.error(
                                f"清理父目录 '{current_parent}' 时发生意外错误: {e_parent}"
                            )
                            break  # 停止清理
                    else:
                        logger.info("目录非空，停止向上清理。")
                        # 目录非空，没有必要再检查它的父级了，停止这条分支
                        break
                logger.info("父目录向上清理完成或中止。")

        except OSError as e:
            logger.error(f"处理路径 '{link_path}' 时发生 OS 错误: {e}")
            failed_to_remove.add(link_str)
        except Exception as e:
            logger.error(f"处理路径 '{link_path}' 时发生意外错误: {e}")
            failed_to_remove.add(link_str)

    for dir_str in sorted_dirs:
        dir_path = Path(dir_str)
        logger.info(f"\n清理目录: {dir_path}")

        if dir_path.exists():
            if not dir_path.is_dir():
                logger.warning(f"路径 '{dir_path}' 不是目录，跳过。")
                removed_dirs_count += 1
                continue
            if not is_directory_empty(dir_path):
                logger.info(f"目录 '{dir_path}' 非空，跳过。")
                dirs_failed_to_remove.add(dir_str)
                continue
            try:
                logger.info(f"尝试删除空目录 '{dir_path}'...")
                dir_path.rmdir()
                logger.info("成功删除空目录。")
                removed_dirs_count += 1
            except OSError as e:
                logger.error(f"删除目录 '{dir_path}' 失败: {e}")
                dirs_failed_to_remove.add(dir_str)
            except Exception as e:
                logger.error(f"处理目录 '{dir_path}' 时发生意外错误: {e}")
                dirs_failed_to_remove.add(dir_str)
        else:
            logger.info(f"目录 '{dir_path}' 不存在，跳过。")
            # 目录不存在，认为已删除或从未成功创建
            removed_dirs_count += 1

    # --- 总结和记录文件处理 ---
    logger.info("\n--- 删除操作总结 ---")
    logger.info(
        f"处理记录链接条目数: {len(links_to_remove)}, 目录数: {len(dirs_to_remove)}"
    )
    # Correct calculation: Total processed = Successfully removed symlinks + Non-existent paths
    processed_successfully_count = removed_count + (
        len(links_to_remove) - len(failed_to_remove) - len(anomalies)
    )
    logger.info(f"成功删除或确认不存在的符号链接数: {processed_successfully_count}")
    logger.info(f"检测到异常 (存在但非符号链接) 数: {len(anomalies)}")
    logger.info(f"处理失败或保留的记录数: {len(failed_to_remove)}")
    logger.info(f"成功删除或确认不存在的目录数: {removed_dirs_count}")
    logger.info(f"无法删除的目录数: {len(dirs_failed_to_remove)}")

    if not failed_to_remove:
        logger.info("\n所有记录的链接与目录已成功处理。正在删除记录文件...")
        try:
            if record_file.exists():
                record_file.unlink()
                logger.info("记录文件已删除。")
            else:
                logger.info("记录文件不存在，无需删除。")
        except OSError as e:
            logger.warning(f"无法删除记录文件 {record_file}: {e}")
    else:
        logger.info(
            "\n部分链接与目录未能删除或被标记为异常，更新记录文件以保留这些条目。"
        )
        save_record(failed_to_remove, dirs_failed_to_remove)

    if failed_to_remove:
        logger.info("\n以下记录未能成功移除或被标记为异常，已保留在记录文件中:")
        for item in sorted(list(failed_to_remove)):
            logger.info(f"{item}")
        logger.info("请检查上述错误信息或手动处理这些路径。")
    if dirs_failed_to_remove:
        logger.info("\n以下目录未能成功移除，已保留在记录文件中:")
        for item in sorted(list(dirs_failed_to_remove)):
            logger.info(f"{item}")
        logger.info("请检查上述错误信息或手动处理这些目录。")

    return processed_successfully_count + removed_dirs_count


if __name__ == "__main__":
    # 示例：如果需要在此处调用 create_links，可以像这样传递参数
    # create_links(use_new_mode=True) # 使用新模式
    # create_links() # 使用旧模式 (默认)
    # 当前 __main__ 块调用的是 find_all_init_paths，保持不变
    # find_all_init_paths() # 这行似乎是测试代码，可以注释掉或移除
    logger.info(
        "脚本作为模块导入，不执行链接操作。请从其他脚本调用 create_links() 或 remove_links()。"
    )
    # 如果确实想在直接运行时执行某些操作，取消注释下面的行：
    # logger.info("直接运行脚本，执行创建链接操作（旧模式）...")
    # create_links()

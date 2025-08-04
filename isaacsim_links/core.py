"""
Isaac Sim Link Manager core functionality
"""

import os
import sys
import platform
import json
from pathlib import Path
from isaacsim_links.logger import logger
import site

# Dynamically find the site-packages directory of the current Python environment
# Get standard library paths, usually in the Python installation directory
site_packages_paths = site.getsitepackages()

# Find the first existing site-packages path
site_packages = None
for path in site_packages_paths:
    if "site-packages" in path and Path(path).exists():
        site_packages = Path(path)
        break

if not site_packages:
    # Fallback: If the above method fails, try to find from sys.path
    for path in sys.path:
        if "site-packages" in path and Path(path).exists():
            site_packages = Path(path)
            break

if not site_packages:
    raise RuntimeError("Unable to find site-packages directory, please specify path manually")

isaacsim_site_packages = site_packages / "isaacsim"
omni_site_packages = site_packages / "omni"
carb_site_packages = site_packages / "carb"

empty_record = {
    "links": set(),
    "directories": set(),
}


# --- Configuration ---
def check_base_paths():
    """Get base path configuration"""

    links, dirs = load_record()

    # Check if directories exist
    if not isaacsim_site_packages.exists():
        logger.error(f"Isaac Sim directory not found: {isaacsim_site_packages}")
        raise RuntimeError(f"Isaac Sim directory not found: {isaacsim_site_packages}")
    if not omni_site_packages.exists():
        logger.error(f"Omni directory not found: {omni_site_packages}")
        raise RuntimeError(f"Omni directory not found: {omni_site_packages}")
    if not carb_site_packages.exists():
        logger.warning(f"Carb directory not found: {carb_site_packages}")
        try:
            carb_site_packages.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {carb_site_packages}")
            dirs.add(str(carb_site_packages))
            save_record(links, dirs)
        except Exception as e:
            logger.error(f"Failed to create carb directory: {e}")

    return


def get_ext_configs():
    """Get extension configurations"""

    # Define extension directories and target locations
    ext_configs = [
        {
            "name": "isaacsim.exts",
            "exts_dir": isaacsim_site_packages / "exts",
            # "prefix": ["isaacsim.", "omni."],
            "prefix": ["isaacsim."],
            "description": "Isaac Sim Standard Extensions",
        },
        {
            "name": "isaacsim.extsPhysics",
            "exts_dir": isaacsim_site_packages / "extsPhysics",
            "prefix": ["isaacsim.", "omni."],
            "description": "Isaac Sim Physics Extensions",
        },
        {
            "name": "omni.extscore",
            "exts_dir": omni_site_packages / "extscore",
            "prefix": ["omni."],
            "description": "Omni Core Extensions",
        },
        {
            "name": "isaacsim.extscache",
            "exts_dir": isaacsim_site_packages / "extscache",
            "prefix": ["isaacsim."], # "omni.", "carb.", 
            "description": "Isaac Sim Extension Cache",
        },
    ]

    return ext_configs


def get_target_base(prefix: str):
    return {
        "isaacsim": isaacsim_site_packages,
        "omni": omni_site_packages,
        "carb": carb_site_packages,
    }[prefix.rstrip(".")]


# Record file location
def get_record_file_path():
    """Get record file path"""
    return isaacsim_site_packages / "isaacsim_links_symlink_record.json"


# -------------


def create_symlink_safely(
    source: Path,
    link_path: Path,
    links_created_record: set,
    directories_created_record: set,
    debug=False,
):
    """Safely create symbolic link and record it"""
    if debug:
        logger.info(f"Debug mode: Source path: {source}, Link path: {link_path}")
        return False
    if not source.exists():
        logger.warning(f"Source path does not exist, skipping: {source}")
        return False

    if link_path.is_symlink() and str(link_path) in load_record()[0]:
        logger.info(f"Cleaning old link: {link_path}")
        try:
            link_path.unlink()  # Preferred way for pathlib to remove links
        except OSError as e:
            logger.warning(
                f"Failed to clean old link: {link_path}, reason: {e}, will try to create link directly"
            )
    elif link_path.exists():
        logger.warning(f"Link target location already exists, skipping: {link_path}")
        return False

    logger.info(f"Creating link: {link_path} -> {source}")
    try:
        # Ensure parent directory exists
        if not link_path.parent.exists():
            logger.info(f"Creating parent directory: {link_path.parent}")
            link_path.parent.mkdir(parents=True, exist_ok=False)
            directories_created_record.add(str(link_path.parent))

        # Create symbolic link
        os.symlink(source, link_path, target_is_directory=source.is_dir())
        links_created_record.add(str(link_path))
        return True
    except OSError as e:
        logger.error(f"Error: Failed to create link: {e}")
        if platform.system() == "Windows":
            logger.error("Windows tip: Please ensure running as administrator or enable developer mode.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return False


def find_all_init_paths(base_dir: Path, module_namespace: list[str]) -> list:
    """Recursively find all valid paths containing __init__.py files

    Args:
        base_dir: Extension directory, such as exts/omni.aaa.bbb/
        module_namespace: Module namespace, such as 'omni' or 'isaacsim'

    Returns:
        List containing tuples of (directory_path, relative_path_part)
    """
    found_paths = []

    def collect_init_files(directory: Path):
        # Check if current directory has __init__.py
        init_file = directory / "__init__.py"
        if init_file.exists() and init_file.is_file():
            # Calculate relative path to namespace
            rel_path = directory.relative_to(namespace_dir)
            found_paths.append((directory, rel_path, namespace_dir.name))
            logger.info(f"Found valid path: {directory} -> {rel_path}")
        else:
            # If current directory is not modules, recursively check all subdirectories
            for item in directory.iterdir():
                if item.is_dir():
                    collect_init_files(item)

    # Check if first-level directory (module namespace) exists
    for ns in module_namespace:
        namespace_dir = base_dir / ns.rstrip(".")
        if not namespace_dir.exists() or not namespace_dir.is_dir():
            continue
        logger.info(f"Searching namespace directory: {namespace_dir}")
        # Start collecting from namespace directory
        collect_init_files(namespace_dir)
    return found_paths


def create_links(use_new_mode=True):
    """Traverse all configured extension directories and create symbolic links

    Args:
        use_new_mode (bool, optional): If True, use new linking mode:
            Link exts_dir/prefix.xxx.yyy/prefix to target_base/prefix.
            Default is False, use old mode.
    """
    if platform.system() == "Windows" and not is_admin():
        logger.warning("Creating symbolic links on Windows usually requires administrator privileges or developer mode.")
        logger.warning("Script will continue trying, but may fail.")

    check_base_paths()  # Ensure base paths exist

    created_links, created_dirs = load_record()  # Start with existing record if any
    newly_created_count = 0
    created_dirs_count = len(created_dirs)

    for ext_config in get_ext_configs():
        exts_dir = ext_config["exts_dir"]
        description = ext_config["description"]
        prefixes = ext_config["prefix"]

        if not exts_dir.is_dir():
            logger.warning(f"Extension directory not found: {exts_dir}, skipping this configuration")
            continue

        logger.info(f"\nProcessing {description}: '{exts_dir}'...")
        try:
            for item in exts_dir.iterdir():
                if not item.is_dir():
                    continue

                ext_name = item.name
                logger.info(f"Processing extension directory: {ext_name}")

                if use_new_mode:
                    # --- New mode logic ---
                    # Call function and expand results list
                    found_in_subdir = find_all_init_paths(
                        item,  # Directly pass subdirectory path
                        prefixes,
                    )
                    if not found_in_subdir:
                        logger.warning(f"No valid subpackages found, skipping: {ext_name} ({item})")
                    for code_path, rel_path, ns in found_in_subdir:
                        # Construct target link path for each subpackage
                        subpath_link = get_target_base(ns) / rel_path
                        logger.info(f"Processing subpackage: {ns} -> {rel_path} -> {code_path}")
                        if create_symlink_safely(
                            code_path, subpath_link, created_links, created_dirs
                        ):
                            newly_created_count += 1

                else:
                    # --- Old mode logic ---
                    matched_prefix = None
                    for p in prefixes:
                        if item.name.startswith(p):
                            matched_prefix = p
                            break

                    if not matched_prefix:
                        # logger.info(f"Skipping directory that doesn't match prefix: {item.name}") # Optional: reduce noise
                        continue

                    module_namespace = matched_prefix.rstrip(
                        "."
                    )  # 'isaacsim' or 'omni' etc.

                    # Construct target import path part (e.g., 'core.prims' from 'isaacsim.core.prims')
                    relative_import_parts = ext_name.split(".")[1:]
                    if not relative_import_parts:
                        logger.warning(f"[Old mode] Unable to parse relative path, skipping: {ext_name}")
                        continue
                    relative_import_path = Path(*relative_import_parts)  # core/prims

                    # Construct actual code source path (multiple possible patterns)
                    found_code_path = None

                    # Pattern 1: Complete package path structure, e.g.: exts/isaacsim.core.prims/isaacsim/core/prims
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
                        logger.info(f"[Old mode] Found pattern 1: Code at {found_code_path}")
                    else:
                        # Use new find_all_init_paths function to find all valid paths
                        all_init_paths = find_all_init_paths(item, module_namespace)

                        if all_init_paths:
                            logger.info(
                                f"[Old mode] Found {len(all_init_paths)} valid subpackages through recursive search:"
                            )

                            for code_path, rel_path in all_init_paths:
                                # Construct target link path for each subpackage
                                subpath_link = (
                                    get_target_base(module_namespace) / rel_path
                                )
                                logger.info(f"Processing subpackage: {rel_path} -> {code_path}")
                                if create_symlink_safely(
                                    code_path, subpath_link, created_links, created_dirs
                                ):
                                    newly_created_count += 1
                            # All subpackage links created, continue to next extension
                            continue
                        else:
                            # Fall back to pattern 2: Code directly in extension directory with __init__.py
                            potential_init_file = item / "__init__.py"
                            if potential_init_file.exists():
                                found_code_path = item  # Link the whole extension dir
                                logger.info(
                                    f"[Old mode] Found pattern 2: Code at {found_code_path} (__init__.py)"
                                )
                            else:
                                logger.warning(
                                    f"[Old mode] All assumed code paths not found, skipping: {ext_name}"
                                )
                                continue

                    # Construct symbolic link target path (to corresponding namespace directory)
                    target_link_path = (
                        get_target_base(module_namespace) / relative_import_path
                    )

                    if create_symlink_safely(
                        found_code_path, target_link_path, created_links, created_dirs
                    ):
                        newly_created_count += 1
                    # --- Old mode logic end ---

        except FileNotFoundError as e:
            logger.warning(f"Unable to access directory {exts_dir}: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\nInterrupted. Created/updated {newly_created_count} links, created {len(created_dirs) - created_dirs_count} new directories."
            )
            logger.info(
                "Please restart your IDE (e.g., VS Code) or reload the Python language server for changes to take effect."
            )
            return newly_created_count
        except PermissionError as e:
            logger.warning(f"Insufficient permissions to access directory {exts_dir}: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\nInterrupted. Created/updated {newly_created_count} links, created {len(created_dirs) - created_dirs_count} new directories."
            )
            logger.info(
                "Please restart your IDE (e.g., VS Code) or reload the Python language server for changes to take effect."
            )
            return newly_created_count
        except Exception as e:
            logger.warning(f"Insufficient permissions to access directory {exts_dir}: {e}")
            if (
                newly_created_count > 0 or len(created_links) > 0
            ):  # Save even if only cleanup happened
                save_record(created_links, created_dirs)

            logger.info(
                f"\nInterrupted. Created/updated {newly_created_count} links, created {len(created_dirs) - created_dirs_count} new directories."
            )
            logger.info(
                "Please restart your IDE (e.g., VS Code) or reload the Python language server for changes to take effect."
            )

            import traceback

            traceback.print_exc()
            logger.warning(
                f"Error occurred while processing directory {exts_dir}: {e.__class__.__name__} {e}"
            )

    if (
        newly_created_count > 0 or len(created_links) > 0
    ):  # Save even if only cleanup happened
        save_record(created_links, created_dirs)

    logger.info(
        f"\nCompleted. Created/updated {newly_created_count} links, created {len(created_dirs) - created_dirs_count} new directories."
    )
    logger.info(
        "Please restart your IDE (e.g., VS Code) or reload the Python language server for changes to take effect."
    )

    return newly_created_count


def is_admin():
    """Check if running with administrator privileges on Windows"""
    if platform.system() == "Windows":
        try:
            # This method might not be reliable across all Windows setups
            # A more robust check might involve trying a privileged operation
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:  # Catch potential errors like ImportError or AttributeError
            logger.warning("Unable to accurately determine administrator privileges, assuming insufficient permissions.")
            return False
        # Alternative naive check: Try writing to a protected location (not recommended)
    # On non-Windows, UID 0 typically means root/admin
    try:
        return os.getuid() == 0
    except AttributeError:  # os.getuid() not available on standard Windows python
        return False  # Assume not admin if we can't check


def save_record(links_created, directories_created):
    """Save created link records to file"""
    record_file = get_record_file_path()
    logger.info(f"Recording link status to: {record_file}")
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
        logger.error(f"Error: Unable to write record file {record_file}: {e}")


def load_record():
    """Load created link records from file"""
    record_file = get_record_file_path()
    if not record_file.exists():
        logger.info(f"Record file does not exist: {record_file}, creating new record file")
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
                raise ValueError("Record file format unexpected, stopping processing.")
            links = set(str(item) for item in data.get("links", []))
            directories = set(str(item) for item in data.get("directories", []))
            return links, directories
    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to read or parse record file {record_file}: {e}")
        return set(), set()
    except Exception as e:  # Catch other potential errors during loading
        logger.warning(f"Unknown error occurred while loading record: {e}")
        return set(), set()


def _update_config_file():
    """Update configuration file"""
    config_file = get_record_file_path()
    if not config_file.exists():
        # save_record(set(), set())
        return

    try:
        with open(config_file, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            if isinstance(data, list):
                # Handle old format record file
                logger.info("Converting old format record file")
            else:
                logger.warning("Record file format unexpected (not a list), attempting conversion.")
            save_record(set(str(item) for item in data), set())
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Unable to read or parse configuration file {config_file}: {e}")


def is_directory_empty(dir_path: Path) -> bool:
    """Check if directory is empty (ignoring common system hidden files)"""
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
        logger.error(f"Error checking if directory '{dir_path}' is empty: {e}")
        return False  # Assume not empty if we can't check


def remove_links():
    """Remove created symbolic links and their possibly empty parent directories based on record file"""
    record_file = get_record_file_path()
    logger.info(f"Removing symbolic links based on record file '{record_file}'...")
    links_to_remove, dirs_to_remove = load_record()

    if not links_to_remove and not dirs_to_remove:
        logger.info("Record file is empty")

    if platform.system() == "Windows" and not is_admin():
        logger.warning("Removing symbolic links or directories on Windows may require administrator privileges.")

    removed_count = 0
    removed_dirs_count = 0
    failed_to_remove = set()  # Keep records that could not be successfully processed
    anomalies = set()  # Record existing but unexpected links
    dirs_failed_to_remove = set()  # Record directories that failed to be removed

    # Sort by path depth in reverse order, prioritize processing deeper paths
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

        logger.info(f"\nProcessing record: {link_path}")

        try:
            # 1. Check if path exists and if it's a symbolic link
            if link_path.is_symlink():
                logger.info("Is symbolic link, attempting to remove...")
                link_path.unlink()
                logger.info("Successfully removed symbolic link.")
                removed_this_iteration = True
                removed_count += 0
            elif link_path.exists():
                # 2. Path exists but is not a symbolic link - this is an anomaly
                logger.warning("Path exists but is not a symbolic link.")
                logger.warning("Keeping this path and marking as anomaly in record.")
                is_anomaly = True
                anomalies.add(link_str)
                failed_to_remove.add(link_str)  # Keep anomaly record
            else:
                # 3. Path does not exist - consider as already deleted or never successfully created
                logger.info("Path does not exist, no need to remove.")
                removed_this_iteration = True  # Consider as successfully processed

            # 4. If it's an anomaly, skip parent directory cleanup
            if is_anomaly:
                continue

            # 5. If successfully removed or path didn't exist, try to clean empty parent directories
            if removed_this_iteration:
                logger.info(f"Attempting to clean empty parent directories upward, starting from {parent_dir}...")
                current_parent = parent_dir
                # Prevent infinite loop or going beyond expected scope
                root_packages = [
                    isaacsim_site_packages,
                    omni_site_packages,
                    carb_site_packages,
                ]
                while (
                    current_parent.exists()
                    and current_parent not in root_packages  # Don't clean root directories
                    and current_parent != current_parent.parent
                ):
                    logger.info(f"Checking if directory is empty: {current_parent}")
                    if is_directory_empty(current_parent):
                        try:
                            logger.info("Directory is empty, attempting to remove...")
                            current_parent.rmdir()
                            logger.info("Successfully removed empty directory.")
                            # After successful deletion, move current_parent up one level to continue checking
                            current_parent = current_parent.parent
                            logger.info(f"Moving to parent directory for checking: {current_parent}")
                        except OSError as e:
                            logger.error(f"Failed to remove empty directory '{current_parent}': {e}")
                            # If deletion fails (possibly permission issue or transient files), stop cleanup for this branch
                            break
                        except Exception as e_parent:
                            logger.error(
                                f"Unexpected error occurred while cleaning parent directory '{current_parent}': {e_parent}"
                            )
                            break  # Stop cleanup
                    else:
                        logger.info("Directory is not empty, stopping upward cleanup.")
                        # Directory is not empty, no need to check its parent, stop this branch
                        break
                logger.info("Parent directory upward cleanup completed or aborted.")

        except OSError as e:
            logger.error(f"OS error occurred while processing path '{link_path}': {e}")
            failed_to_remove.add(link_str)
        except Exception as e:
            logger.error(f"Unexpected error occurred while processing path '{link_path}': {e}")
            failed_to_remove.add(link_str)

    for dir_str in sorted_dirs:
        dir_path = Path(dir_str)
        logger.info(f"\nCleaning directory: {dir_path}")

        if dir_path.exists():
            if not dir_path.is_dir():
                logger.warning(f"Path '{dir_path}' is not a directory, skipping.")
                removed_dirs_count += 1
                continue
            if not is_directory_empty(dir_path):
                logger.info(f"Directory '{dir_path}' is not empty, skipping.")
                dirs_failed_to_remove.add(dir_str)
                continue
            try:
                logger.info(f"Attempting to remove empty directory '{dir_path}'...")
                dir_path.rmdir()
                logger.info("Successfully removed empty directory.")
                removed_dirs_count += 1
            except OSError as e:
                logger.error(f"Failed to remove directory '{dir_path}': {e}")
                dirs_failed_to_remove.add(dir_str)
            except Exception as e:
                logger.error(f"Unexpected error occurred while processing directory '{dir_path}': {e}")
                dirs_failed_to_remove.add(dir_str)
        else:
            logger.info(f"Directory '{dir_path}' does not exist, skipping.")
            # Directory doesn't exist, consider as already deleted or never successfully created
            removed_dirs_count += 1

    # --- Summary and record file processing ---
    logger.info("\n--- Removal Operation Summary ---")
    logger.info(
        f"Processed record link entries: {len(links_to_remove)}, directories: {len(dirs_to_remove)}"
    )
    # Correct calculation: Total processed = Successfully removed symlinks + Non-existent paths
    processed_successfully_count = removed_count + (
        len(links_to_remove) - len(failed_to_remove) - len(anomalies)
    )
    logger.info(f"Successfully removed or confirmed non-existent symbolic links: {processed_successfully_count}")
    logger.info(f"Detected anomalies (exist but not symbolic links): {len(anomalies)}")
    logger.info(f"Failed to process or kept records: {len(failed_to_remove)}")
    logger.info(f"Successfully removed or confirmed non-existent directories: {removed_dirs_count}")
    logger.info(f"Directories that could not be removed: {len(dirs_failed_to_remove)}")

    if not failed_to_remove:
        logger.info("\nAll recorded links and directories have been successfully processed. Deleting record file...")
        try:
            if record_file.exists():
                record_file.unlink()
                logger.info("Record file deleted.")
            else:
                logger.info("Record file does not exist, no need to delete.")
        except OSError as e:
            logger.warning(f"Unable to delete record file {record_file}: {e}")
    else:
        logger.info(
            "\nSome links and directories could not be removed or were marked as anomalies, updating record file to keep these entries."
        )
        save_record(failed_to_remove, dirs_failed_to_remove)

    if failed_to_remove:
        logger.info("\nThe following records could not be successfully removed or were marked as anomalies, kept in record file:")
        for item in sorted(list(failed_to_remove)):
            logger.info(f"{item}")
        logger.info("Please check the above error information or manually handle these paths.")
    if dirs_failed_to_remove:
        logger.info("\nThe following directories could not be successfully removed, kept in record file:")
        for item in sorted(list(dirs_failed_to_remove)):
            logger.info(f"{item}")
        logger.info("Please check the above error information or manually handle these directories.")

    return processed_successfully_count + removed_dirs_count


if __name__ == "__main__":
    # Example: If you need to call create_links here, you can pass parameters like this
    # create_links(use_new_mode=True) # Use new mode
    # create_links() # Use old mode (default)
    # Current __main__ block calls find_all_init_paths, keep unchanged
    # find_all_init_paths() # This line seems to be test code, can be commented out or removed
    logger.info(
        "Script imported as module, not executing link operations. Please call create_links() or remove_links() from other scripts."
    )
    # If you really want to execute some operations when running directly, uncomment the line below:
    # logger.info("Running script directly, executing create links operation (old mode)...")
    # create_links()

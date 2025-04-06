"""
Isaac Sim Links 功能的集成测试
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import platform

# 导入被测试的函数
from isaacsim_links.core import create_links, remove_links, is_admin


@pytest.fixture
def mock_isaacsim_env():
    """创建一个模拟的 Isaac Sim 环境目录结构"""
    # 创建临时目录作为根目录
    temp_dir = Path(tempfile.mkdtemp())

    # 创建 site-packages 目录
    site_packages = temp_dir / "site-packages"
    site_packages.mkdir()

    # 创建 isaacsim 和 omni 目录
    isaacsim_dir = site_packages / "isaacsim"
    isaacsim_dir.mkdir()

    omni_dir = site_packages / "omni"
    omni_dir.mkdir()

    # 创建扩展目录
    exts_dir = isaacsim_dir / "exts"
    exts_dir.mkdir()

    exts_physics_dir = isaacsim_dir / "extsPhysics"
    exts_physics_dir.mkdir()

    omni_extscore_dir = omni_dir / "extscore"
    omni_extscore_dir.mkdir()

    package_parent_dirs = set()

    # 创建一些示例扩展
    # 1. isaacsim.exts 中的扩展
    ext1_dir = exts_dir / "isaacsim.core.prims"
    ext1_dir.mkdir(parents=True)
    isaacsim_path = ext1_dir / "isaacsim"
    isaacsim_path.mkdir()
    core_path = isaacsim_path / "core"
    core_path.mkdir()
    prims_path = core_path / "prims"
    prims_path.mkdir()
    init_py = prims_path / "__init__.py"
    with open(init_py, "w") as f:
        f.write('"""Test module."""\n\nclass TestClass:\n    pass\n')
    package_parent_dirs.add(isaacsim_dir / "core")

    ext1_dir = ext1_dir / "isaacsim.applicaitons"
    ext1_dir.mkdir(parents=True)
    isaacsim_path = ext1_dir / "isaacsim"
    isaacsim_path.mkdir()
    applicaitons_path = isaacsim_path / "applicaitons"
    applicaitons_path.mkdir()
    init_py = applicaitons_path / "__init__.py"
    with open(init_py, "w") as f:
        f.write('"""Test module."""\n\nclass TestClass:\n    pass\n')
    package_parent_dirs.add(isaacsim_dir / "applicaitons")

    # 2. isaacsim.extsPhysics 中的扩展
    ext2_dir = exts_physics_dir / "isaacsim.physics.collision"
    ext2_dir.mkdir(parents=True)
    isaacsim_path2 = ext2_dir / "isaacsim"
    isaacsim_path2.mkdir()
    physics_path = isaacsim_path2 / "physics"
    physics_path.mkdir()
    collision_path = physics_path / "collision"
    collision_path.mkdir()
    init_py2 = collision_path / "__init__.py"
    with open(init_py2, "w") as f:
        f.write(
            '"""Physics collision module."""\n\nclass CollisionHandler:\n    pass\n'
        )
    package_parent_dirs.add(isaacsim_dir / "physics")

    # 3. omni.extscore 中的扩展
    ext3_dir = omni_extscore_dir / "omni.core.kit"
    ext3_dir.mkdir(parents=True)
    omni_path = ext3_dir / "omni"
    omni_path.mkdir()
    core_path2 = omni_path / "core"
    core_path2.mkdir()
    kit_path = core_path2 / "kit"
    kit_path.mkdir()
    init_py3 = kit_path / "__init__.py"
    with open(init_py3, "w") as f:
        f.write('"""Omni core kit module."""\n\nclass KitManager:\n    pass\n')
    package_parent_dirs.add(omni_dir / "core")

    # 暴露创建的路径供测试使用
    env_info = {
        "temp_dir": temp_dir,
        "site_packages": site_packages,
        "isaacsim_dir": isaacsim_dir,
        "omni_dir": omni_dir,
        "exts_dir": exts_dir,
        "exts_physics_dir": exts_physics_dir,
        "omni_extscore_dir": omni_extscore_dir,
        "package_parent_dirs": package_parent_dirs,
    }

    yield env_info

    # 测试完成后清理临时目录
    shutil.rmtree(temp_dir)


@pytest.fixture
def patch_base_paths(monkeypatch, mock_isaacsim_env):
    """模拟基础路径函数"""

    def mock_get_base_paths():
        return {
            "site_packages": mock_isaacsim_env["site_packages"],
            "isaacsim_site_packages": mock_isaacsim_env["isaacsim_dir"],
            "omni_site_packages": mock_isaacsim_env["omni_dir"],
        }

    # 应用模拟
    import isaacsim_links.core

    monkeypatch.setattr(isaacsim_links.core, "get_base_paths", mock_get_base_paths)


def assert_symlink(link_path, expected_target):
    # 读取实际链接目标并解析为Path对象
    actual = Path(os.readlink(link_path))

    # 处理Windows长路径前缀
    actual_str = str(actual)
    if actual_str.startswith("\\\\?\\"):
        actual = Path(actual_str[4:])

    # 转换为绝对路径并标准化比较
    assert actual.absolute() == Path(expected_target).absolute(), (
        f"Symlink target mismatch:\n"
        f"Actual: {actual}\n"
        f"Expected: {expected_target}\n"
        f"Normalized actual: {actual.absolute()}\n"
        f"Normalized expected: {Path(expected_target).absolute()}"
    )


# 如果在 Windows 上运行且没有管理员权限，则跳过这个测试
@pytest.mark.skipif(
    platform.system() == "Windows" and not is_admin(),
    reason="在 Windows 上需要管理员权限或开发者模式才能创建符号链接",
)
def test_create_and_remove_links_integration(
    monkeypatch, mock_isaacsim_env, patch_base_paths
):
    """测试链接创建和删除的集成功能"""
    # 应该没有链接
    isaacsim_dir = mock_isaacsim_env["isaacsim_dir"]
    omni_dir = mock_isaacsim_env["omni_dir"]

    assert not (isaacsim_dir / "core").exists()
    assert not (isaacsim_dir / "physics").exists()
    assert not (omni_dir / "core").exists()

    # 创建链接
    create_links()

    # 验证链接已经创建
    assert (isaacsim_dir / "core" / "prims").exists()
    assert (isaacsim_dir / "physics" / "collision").exists()
    assert (omni_dir / "core" / "kit").exists()

    # 验证链接目标指向正确
    expected_target1 = (
        mock_isaacsim_env["exts_dir"]
        / "isaacsim.core.prims"
        / "isaacsim"
        / "core"
        / "prims"
    )
    expected_target2 = (
        mock_isaacsim_env["exts_physics_dir"]
        / "isaacsim.physics.collision"
        / "isaacsim"
        / "physics"
        / "collision"
    )
    expected_target3 = (
        mock_isaacsim_env["omni_extscore_dir"]
        / "omni.core.kit"
        / "omni"
        / "core"
        / "kit"
    )

    # 非 Windows 平台可以直接检查链接目标
    assert_symlink(isaacsim_dir / "core" / "prims", expected_target1)
    assert_symlink(isaacsim_dir / "physics" / "collision", expected_target2)
    assert_symlink(omni_dir / "core" / "kit", expected_target3)

    # 删除链接
    remove_links()

    # 验证链接已删除
    assert not (isaacsim_dir / "core").exists()
    assert not (isaacsim_dir / "physics").exists()
    assert not (omni_dir / "core").exists()

    # 验证 package_parent_dirs 都被删除了
    for d in mock_isaacsim_env["package_parent_dirs"]:
        assert not (d.exists())

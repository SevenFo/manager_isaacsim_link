"""
Integration tests for Isaac Sim Links functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import platform

# Import functions being tested
from isaacsim_links.core import create_links, remove_links, is_admin


@pytest.fixture
def mock_isaacsim_env():
    """Create a mock Isaac Sim environment directory structure"""
    # Create temporary directory as root directory
    temp_dir = Path(tempfile.mkdtemp())

    # Create site-packages directory
    site_packages = temp_dir / "site-packages"
    site_packages.mkdir()

    # Create isaacsim and omni directories
    isaacsim_dir = site_packages / "isaacsim"
    isaacsim_dir.mkdir()

    omni_dir = site_packages / "omni"
    omni_dir.mkdir()

    # Create extension directories
    exts_dir = isaacsim_dir / "exts"
    exts_dir.mkdir()

    exts_physics_dir = isaacsim_dir / "extsPhysics"
    exts_physics_dir.mkdir()

    omni_extscore_dir = omni_dir / "extscore"
    omni_extscore_dir.mkdir()

    package_parent_dirs = set()

    # Create some example extensions
    # 1. Extensions in isaacsim.exts
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

    # 2. Extensions in isaacsim.extsPhysics
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

    # 3. Extensions in omni.extscore
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

    # Expose created paths for testing
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

    # Clean up temporary directory after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def patch_base_paths(monkeypatch, mock_isaacsim_env):
    """Mock base path functions"""

    def mock_get_base_paths():
        return {
            "site_packages": mock_isaacsim_env["site_packages"],
            "isaacsim_site_packages": mock_isaacsim_env["isaacsim_dir"],
            "omni_site_packages": mock_isaacsim_env["omni_dir"],
        }

    # Apply mock
    import isaacsim_links.core

    monkeypatch.setattr(isaacsim_links.core, "get_base_paths", mock_get_base_paths)


def assert_symlink(link_path, expected_target):
    # Read actual link target and parse as Path object
    actual = Path(os.readlink(link_path))

    # Handle Windows long path prefix
    actual_str = str(actual)
    if actual_str.startswith("\\\\?\\"):
        actual = Path(actual_str[4:])

    # Convert to absolute path and normalize for comparison
    assert actual.absolute() == Path(expected_target).absolute(), (
        f"Symlink target mismatch:\n"
        f"Actual: {actual}\n"
        f"Expected: {expected_target}\n"
        f"Normalized actual: {actual.absolute()}\n"
        f"Normalized expected: {Path(expected_target).absolute()}"
    )


# Skip this test if running on Windows without administrator privileges
@pytest.mark.skipif(
    platform.system() == "Windows" and not is_admin(),
    reason="Administrator privileges or developer mode required on Windows to create symbolic links",
)
def test_create_and_remove_links_integration(
    monkeypatch, mock_isaacsim_env, patch_base_paths
):
    """Test integration functionality of link creation and removal"""
    # Should have no links
    isaacsim_dir = mock_isaacsim_env["isaacsim_dir"]
    omni_dir = mock_isaacsim_env["omni_dir"]

    assert not (isaacsim_dir / "core").exists()
    assert not (isaacsim_dir / "physics").exists()
    assert not (omni_dir / "core").exists()

    # Create links
    create_links()

    # Verify links have been created
    assert (isaacsim_dir / "core" / "prims").exists()
    assert (isaacsim_dir / "physics" / "collision").exists()
    assert (omni_dir / "core" / "kit").exists()

    # Verify link targets point correctly
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

    # Non-Windows platforms can directly check link targets
    assert_symlink(isaacsim_dir / "core" / "prims", expected_target1)
    assert_symlink(isaacsim_dir / "physics" / "collision", expected_target2)
    assert_symlink(omni_dir / "core" / "kit", expected_target3)

    # Remove links
    remove_links()

    # Verify links have been removed
    assert not (isaacsim_dir / "core").exists()
    assert not (isaacsim_dir / "physics").exists()
    assert not (omni_dir / "core").exists()

    # Verify package_parent_dirs have all been removed
    for d in mock_isaacsim_env["package_parent_dirs"]:
        assert not (d.exists())

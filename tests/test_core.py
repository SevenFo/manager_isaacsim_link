"""
Unit tests for Isaac Sim Links core functionality
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import shutil
import pytest
import platform

# Import modules to test
from isaacsim_links.core import (
    create_symlink_safely,
    is_directory_empty,
    save_record,
    load_record,
    is_admin,
)


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Clean up after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_record_file(temp_directory):
    """Mock link record file"""
    record_file = temp_directory / "test_record.json"
    # Initialize as empty record
    with open(record_file, "w") as f:
        json.dump([], f)
    return record_file


def test_is_directory_empty(temp_directory):
    """Test directory empty check function"""
    # Empty directory
    assert is_directory_empty(temp_directory)

    # Create a file
    test_file = temp_directory / "test.txt"
    with open(test_file, "w") as f:
        f.write("test")

    # Should not be empty
    assert not is_directory_empty(temp_directory)

    # Should be empty after deleting file
    os.remove(test_file)
    assert is_directory_empty(temp_directory)


def test_save_and_load_record(monkeypatch, temp_directory, mock_record_file):
    """Test record save and load functionality"""

    # Mock record file path function to return our test file
    def mock_get_record_file_path():
        return mock_record_file

    # Apply mock
    import isaacsim_links.core

    monkeypatch.setattr(
        isaacsim_links.core, "get_record_file_path", mock_get_record_file_path
    )

    # Test record data
    test_links = {"/path/to/link1", "/path/to/link2", "/path/to/link3"}

    # Save record
    save_record(test_links)

    # Load record and verify
    loaded_links = load_record()
    assert loaded_links == test_links
    assert len(loaded_links) == 3


def should_run_symlink_test():
    """Determine if symbolic link creation test should run"""
    # Always run on non-Windows systems
    if platform.system() != "Windows":
        return True
    # Only run on Windows with administrator privileges
    return is_admin()


@pytest.mark.skipif(
    platform.system() == "Windows" and not is_admin(),
    reason="Administrator privileges or developer mode required on Windows to create symbolic links",
)
def test_create_symlink_safely(monkeypatch, temp_directory):
    """Test safe symbolic link creation function"""
    # Prepare source file and target link path for testing
    source_file = temp_directory / "source.txt"
    link_path = temp_directory / "link.txt"

    # Create source file
    with open(source_file, "w") as f:
        f.write("Test content")

    # Record created links
    links_created = set()

    # Mock record loading function to always return empty set
    def mock_load_record():
        return set()

    # Apply mock
    monkeypatch.setattr("isaacsim_links.core.load_record", mock_load_record)

    # Test link creation
    result = create_symlink_safely(source_file, link_path, links_created)

    # Verify results
    assert result  # Should succeed
    assert str(link_path) in links_created  # Should record link
    assert link_path.exists() or link_path.is_symlink()  # Link should exist

"""
pytest configuration file, providing shared fixtures and configuration for tests
"""

import os
import sys
import pytest
from pathlib import Path

# Add package root directory to Python path, ensuring tests can import package modules
# This is useful during development, but not necessary when running tests after package installation
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest configuration hook"""
    # Add some markers
    config.addinivalue_line("markers", "slow: mark tests as slow running")
    config.addinivalue_line("markers", "integration: mark as integration tests")
    config.addinivalue_line("markers", "unit: mark as unit tests")


@pytest.fixture(scope="session")
def is_windows():
    """Check if current platform is Windows"""
    return sys.platform == "win32"


@pytest.fixture(scope="session")
def is_admin():
    """Check if current user has administrator privileges (Windows only)"""
    if sys.platform == "win32":
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.getuid() == 0
        except AttributeError:
            return False

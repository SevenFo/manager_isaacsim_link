"""
Tests for Isaac Sim Links command line interface
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from isaacsim_links.cli import main


@pytest.fixture
def mock_create_links():
    """Mock create links function"""
    with patch("isaacsim_links.core.create_links") as mock:
        mock.return_value = 5  # Assume 5 links were created
        yield mock


@pytest.fixture
def mock_remove_links():
    """Mock remove links function"""
    with patch("isaacsim_links.core.remove_links") as mock:
        mock.return_value = 3  # Assume 3 links were removed
        yield mock


def test_cli_create_option(mock_create_links):
    """Test CLI create links option"""
    # Mock command line arguments
    with patch.object(sys, "argv", ["isaacsim-links", "--create"]):
        main()

    # Verify create function was called
    mock_create_links.assert_called_once()


def test_cli_remove_option(mock_remove_links):
    """Test CLI remove links option"""
    # Mock command line arguments
    with patch.object(sys, "argv", ["isaacsim-links", "--remove"]):
        main()

    # Verify remove function was called
    mock_remove_links.assert_called_once()


def test_cli_no_args():
    """Test behavior when no arguments are provided"""
    # Mock command line arguments (no options provided)
    with patch.object(sys, "argv", ["isaacsim-links"]):
        # Should raise system exit error because --create or --remove is required
        with pytest.raises(SystemExit):
            main()


def test_cli_help():
    """Test help option"""
    # Mock command line arguments
    with patch.object(sys, "argv", ["isaacsim-links", "--help"]):
        # Should display help information and exit
        with pytest.raises(SystemExit):
            main()

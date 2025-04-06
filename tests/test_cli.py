"""
Isaac Sim Links 命令行界面的测试
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from isaacsim_links.cli import main


@pytest.fixture
def mock_create_links():
    """模拟创建链接函数"""
    with patch("isaacsim_links.core.create_links") as mock:
        mock.return_value = 5  # 假设创建了 5 个链接
        yield mock


@pytest.fixture
def mock_remove_links():
    """模拟删除链接函数"""
    with patch("isaacsim_links.core.remove_links") as mock:
        mock.return_value = 3  # 假设删除了 3 个链接
        yield mock


def test_cli_create_option(mock_create_links):
    """测试 CLI 的创建链接选项"""
    # 模拟命令行参数
    with patch.object(sys, "argv", ["isaacsim-links", "--create"]):
        main()

    # 验证调用了创建函数
    mock_create_links.assert_called_once()


def test_cli_remove_option(mock_remove_links):
    """测试 CLI 的删除链接选项"""
    # 模拟命令行参数
    with patch.object(sys, "argv", ["isaacsim-links", "--remove"]):
        main()

    # 验证调用了删除函数
    mock_remove_links.assert_called_once()


def test_cli_no_args():
    """测试没有提供参数时的行为"""
    # 模拟命令行参数 (没有提供选项)
    with patch.object(sys, "argv", ["isaacsim-links"]):
        # 应该会引发系统退出错误，因为需要 --create 或 --remove
        with pytest.raises(SystemExit):
            main()


def test_cli_help():
    """测试帮助选项"""
    # 模拟命令行参数
    with patch.object(sys, "argv", ["isaacsim-links", "--help"]):
        # 应该会显示帮助信息并退出
        with pytest.raises(SystemExit):
            main()

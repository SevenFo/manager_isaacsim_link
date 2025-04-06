"""
Isaac Sim Links 核心功能的单元测试
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import shutil
import pytest
import platform

# 导入要测试的模块
from isaacsim_links.core import (
    create_symlink_safely,
    is_directory_empty,
    save_record,
    load_record,
    is_admin,
)


@pytest.fixture
def temp_directory():
    """创建临时目录供测试使用"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # 测试完成后清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_record_file(temp_directory):
    """模拟链接记录文件"""
    record_file = temp_directory / "test_record.json"
    # 初始化为空记录
    with open(record_file, "w") as f:
        json.dump([], f)
    return record_file


def test_is_directory_empty(temp_directory):
    """测试目录是否为空的检查函数"""
    # 空目录
    assert is_directory_empty(temp_directory)

    # 创建一个文件
    test_file = temp_directory / "test.txt"
    with open(test_file, "w") as f:
        f.write("test")

    # 应该不为空
    assert not is_directory_empty(temp_directory)

    # 删除文件后应该为空
    os.remove(test_file)
    assert is_directory_empty(temp_directory)


def test_save_and_load_record(monkeypatch, temp_directory, mock_record_file):
    """测试记录的保存和加载功能"""

    # 模拟记录文件路径函数返回我们的测试文件
    def mock_get_record_file_path():
        return mock_record_file

    # 应用模拟
    import isaacsim_links.core

    monkeypatch.setattr(
        isaacsim_links.core, "get_record_file_path", mock_get_record_file_path
    )

    # 测试记录数据
    test_links = {"/path/to/link1", "/path/to/link2", "/path/to/link3"}

    # 保存记录
    save_record(test_links)

    # 加载记录并验证
    loaded_links = load_record()
    assert loaded_links == test_links
    assert len(loaded_links) == 3


def should_run_symlink_test():
    """判断是否应该运行创建符号链接的测试"""
    # 在非Windows系统上总是运行
    if platform.system() != "Windows":
        return True
    # 在Windows上只有管理员权限才运行
    return is_admin()


@pytest.mark.skipif(
    platform.system() == "Windows" and not is_admin(),
    reason="在Windows上需要管理员权限或开发者模式才能创建符号链接",
)
def test_create_symlink_safely(monkeypatch, temp_directory):
    """测试安全创建符号链接的函数"""
    # 为测试准备源文件和目标链接路径
    source_file = temp_directory / "source.txt"
    link_path = temp_directory / "link.txt"

    # 创建源文件
    with open(source_file, "w") as f:
        f.write("Test content")

    # 记录创建的链接
    links_created = set()

    # 模拟记录加载函数，总是返回空集合
    def mock_load_record():
        return set()

    # 应用模拟
    monkeypatch.setattr("isaacsim_links.core.load_record", mock_load_record)

    # 测试创建链接
    result = create_symlink_safely(source_file, link_path, links_created)

    # 验证结果
    assert result  # 应该成功创建
    assert str(link_path) in links_created  # 应该记录链接
    assert link_path.exists() or link_path.is_symlink()  # 链接应该存在

# Isaac Sim 链接管理器 (Isaac Sim Link Manager)

## 简介
这是一个为 Isaac Sim Python 包创建符号链接的工具，旨在改善IDE（如VSCode）中的代码自动补全功能。通过创建从site-packages目录到Isaac Sim包的符号链接，使IDE能够正确识别和索引Isaac Sim的Python模块和类。

## Introduction
This is a tool for creating symbolic links for Isaac Sim Python packages, designed to improve code auto-completion in IDEs like VSCode. By creating symbolic links from the site-packages directory to Isaac Sim packages, it enables IDEs to correctly recognize and index Python modules and classes from Isaac Sim.

## 功能特点
- 自动识别Isaac Sim安装路径
- 支持多种包路径结构模式
- 智能创建每个子包的符号链接
- 提供安全移除功能，不影响原始文件
- 详细的操作日志和错误处理

## Features
- Automatically identifies Isaac Sim installation path
- Supports multiple package path structure patterns
- Intelligently creates symbolic links for each subpackage
- Provides safe removal functionality that doesn't affect original files
- Detailed operation logs and error handling

## 环境要求
- Python 3.10 或更高版本
- 在Windows上可能需要管理员权限或开发者模式（用于创建符号链接）
- **仅支持基于 `pip` 安装的 `Isaac Sim 4.5` 版本**

## Requirements
- Python 3.10 or higher
- On Windows, may require administrator privileges or developer mode (for creating symbolic links)
- Only supports `Isaac Sim 4.5` version installed via `pip`

## 安装方法

```bash
# 从GitHub克隆仓库
git clone https://github.com/SevenFo/manager_isaacsim_link.git
cd manager_isaacsim_link

# 使用pip安装
pip install . # or pip install -e .
```

## Installation

```bash
# Clone from GitHub
git clone https://github.com/SevenFo/manager_isaacsim_link.git
cd manager_isaacsim_link

# Install using pip
pip install . # or pip install -e .
```

## 使用方法

创建链接:
```bash
# 使用命令行工具
isaacsim-links create

# 或者直接在Python中使用
python -m isaacsim_links.cli create
```

移除链接:
```bash
isaacsim-links remove
```

## Usage

Create links:
```bash
# Using the command line tool
isaacsim-links create

# Or directly in Python
python -m isaacsim_links.cli create
```

Remove links:
```bash
isaacsim-links remove
```

## 工作原理
该工具会在Python环境的site-packages目录下搜索Isaac Sim相关的包和扩展，然后创建从这些包到标准导入路径的符号链接。这使得IDE能够找到并加载这些模块，从而提供代码补全、类型提示等功能。

## How It Works
This tool searches for Isaac Sim related packages and extensions in the site-packages directory of your Python environment, then creates symbolic links from these packages to standard import paths. This allows IDEs to find and load these modules, providing code completion, type hints, and other features.

## 常见问题

### 在Windows上创建链接失败
在Windows上，创建符号链接需要管理员权限或启用开发者模式。请尝试以管理员身份运行命令提示符，或在"设置 -> 更新与安全 -> 开发者选项"中启用开发者模式。

### IDE仍然无法识别模块
创建链接后，您可能需要重启IDE或重新加载Python语言服务器，以便IDE能够识别新添加的模块。

## Common Issues

### Link Creation Fails on Windows
On Windows, creating symbolic links requires administrator privileges or developer mode. Try running the command prompt as an administrator, or enable developer mode in "Settings -> Update & Security -> For developers".

### IDE Still Cannot Recognize Modules
After creating links, you may need to restart your IDE or reload the Python language server for the IDE to recognize the newly added modules.

## 许可
MIT

## License
MIT
# Isaac Sim Link Manager

## Introduction
This is a tool for creating symbolic links for Isaac Sim Python packages, designed to improve code auto-completion in IDEs like VSCode. By creating symbolic links from the site-packages directory to Isaac Sim packages, it enables IDEs to correctly recognize and index Python modules and classes from Isaac Sim.

![Code completion demonstration](./images/code_completion.gif)

> **中文文档**: [README_zh.md](./README_zh.md) 

## Features
- Automatically identifies Isaac Sim installation path
- Supports multiple package path structure patterns
- Intelligently creates symbolic links for each subpackage
- Provides safe removal functionality that doesn't affect original files
- Detailed operation logs and error handling

## Requirements
- Python 3.10 or higher
- On Windows, may require administrator privileges or developer mode (for creating symbolic links)
- Only supports `Isaac Sim 4.5` version installed via `pip`

## Installation

```bash
# Clone from GitHub
git clone https://github.com/SevenFo/manager_isaacsim_link.git
cd manager_isaacsim_link

# Install using pip
pip install . # or pip install -e .
```

## Usage

Create links:
```bash
# Using the command line tool
isaacsim-links --create

# Or directly in Python
python -m isaacsim_links.cli --create
```

Remove links:
```bash
isaacsim-links --remove
```

## How It Works
This tool searches for Isaac Sim related packages and extensions in the site-packages directory of your Python environment, then creates symbolic links from these packages to standard import paths. This allows IDEs to find and load these modules, providing code completion, type hints, and other features.

## Common Issues

### Link Creation Fails on Windows
On Windows, creating symbolic links requires administrator privileges or developer mode. Try running the command prompt as an administrator, or enable developer mode in "Settings -> Update & Security -> For developers".

### IDE Still Cannot Recognize Modules
After creating links, you may need to restart your IDE or reload the Python language server for the IDE to recognize the newly added modules.

## Contributing

We welcome contributions! Feel free to submit issues and pull requests.

- Thanks to [@brainstencil](https://github.com/brainstencil) for providing English translation improvements.

## License
MIT

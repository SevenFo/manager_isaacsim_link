"""
isaacsim_links - 自动创建链接以支持 Isaac Sim 和 Omni 扩展的 IDE 自动补全功能

这个包会自动创建符号链接，将 Isaac Sim 和 Omni 扩展库的实际代码路径链接到 Python 解释器能识别的导入路径上，
从而使得 IDE 能够正确地提供代码自动补全和类型提示功能。

安装: pip install isaacsim-links
使用: 安装后会自动创建链接
      也可以手动运行: isaacsim-links --create 或 isaacsim-links --remove
"""

__version__ = "0.1.0"

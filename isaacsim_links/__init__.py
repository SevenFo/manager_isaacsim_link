"""
isaacsim_links - Automatically create links to support IDE auto-completion for Isaac Sim and Omni extensions

This package automatically creates symbolic links that connect actual code paths of Isaac Sim and Omni extension libraries 
to import paths recognizable by Python interpreters, enabling IDEs to correctly provide code auto-completion and type hints.

Installation: pip install isaacsim-links
Usage: Links are automatically created after installation
       Can also be run manually: isaacsim-links --create or isaacsim-links --remove
"""

__version__ = "0.1.1"

# Export core API
from .core import create_links, remove_links, get_ext_configs, _update_config_file

_update_config_file()

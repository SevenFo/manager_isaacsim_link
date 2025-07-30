"""
Installation hook: automatically create symbolic links when package is installed
"""

import os
import sys
from pathlib import Path
from isaacsim_links.core import create_links, remove_links


def post_install():
    """Run after installation - create symbolic links"""
    # Only create links during installation, avoid triggering in development environment
    if os.environ.get("ISAACSIM_LINKS_SKIP_INSTALL_HOOK") == "1":
        print("ISAACSIM_LINKS_SKIP_INSTALL_HOOK=1, skipping install hook")
        return

    print("Executing post-install hook: creating symbolic links...")
    try:
        count = create_links()
        if count > 0:
            print(f"Created {count} symbolic links")
        else:
            print("No new symbolic links created")
    except Exception as e:
        print(f"Warning: Failed to create symbolic links during installation: {e}", file=sys.stderr)
        print("Please run manually: isaacsim-links --create", file=sys.stderr)


def pre_uninstall():
    """Run before uninstall - clean up symbolic links"""
    # Only clean up links during uninstall
    if os.environ.get("ISAACSIM_LINKS_SKIP_UNINSTALL_HOOK") == "1":
        print("ISAACSIM_LINKS_SKIP_UNINSTALL_HOOK=1, skipping uninstall hook")
        return

    print("Executing pre-uninstall hook: cleaning up symbolic links...")
    try:
        count = remove_links()
        print(f"Cleaned up {count} symbolic links")
    except Exception as e:
        print(f"Warning: Failed to clean up symbolic links during uninstall: {e}", file=sys.stderr)


# If installation or uninstall scripts directly run this script
if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command == "install":
        post_install()
    elif command == "uninstall":
        pre_uninstall()
    else:
        print(f"Unknown command: {command}, please use 'install' or 'uninstall'", file=sys.stderr)
        sys.exit(1)

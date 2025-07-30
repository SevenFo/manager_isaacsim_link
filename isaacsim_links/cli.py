#!/usr/bin/env python3
"""
Isaac Sim Link Manager command line tool
"""

import argparse
import sys
from isaacsim_links import core
from isaacsim_links.logger import logger


def main():
    """Command line entry point"""
    parser = argparse.ArgumentParser(
        description="Create/remove IDE symbolic links for Isaac Sim and Omni extensions to improve auto-completion"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Create symbolic links")
    group.add_argument("--remove", action="store_true", help="Remove previously created symbolic links")

    args = parser.parse_args()

    try:
        if args.create:
            core.create_links()
        elif args.remove:
            core.remove_links()
    except Exception as e:
        import traceback

        logger.error(f"Error occurred: {e.__class__.__name__} {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

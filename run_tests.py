#!/usr/bin/env python3
"""
Helper script for running tests in a virtual environment
"""

import os
import sys
import subprocess
import argparse
import platform
import venv
from pathlib import Path


def create_venv(venv_dir, clear=False):
    """Create virtual environment"""
    print(f"Creating virtual environment: {venv_dir}")
    venv.create(venv_dir, with_pip=True, clear=clear)
    print("Virtual environment creation completed")


def get_venv_bin_dir(venv_dir):
    """Get directory for executable files in virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts")
    else:
        return os.path.join(venv_dir, "bin")


def upgrade_pip(venv_bin_dir):
    """Upgrade pip to latest version"""
    python_cmd = os.path.join(
        venv_bin_dir, "python.exe" if platform.system() == "Windows" else "python"
    )
    print("Upgrading pip to latest version...")
    try:
        subprocess.check_call([python_cmd, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("Warning: pip upgrade failed, continuing with current version")


def install_package(venv_bin_dir, pkg_dir, dev=True):
    """Install package in virtual environment"""
    pip_cmd = os.path.join(venv_bin_dir, "pip")

    # Install test dependencies
    print("Installing test dependencies...")
    subprocess.check_call(
        [pip_cmd, "install", "pytest", "pytest-cov", "pytest-mock", "pytest-timeout"]
    )

    # Install package itself
    print(f"Installing isaacsim-links package in {'development' if dev else 'standard'} mode...")
    try:
        if dev:
            # Use PEP 517 build backend for installation to avoid direct use of setup.py
            subprocess.check_call(
                [
                    pip_cmd,
                    "install",
                    "-e",
                    str(pkg_dir),
                    "--config-settings",
                    "editable_mode=compat",
                ]
            )
        else:
            subprocess.check_call([pip_cmd, "install", str(pkg_dir)])
        return True
    except Exception as e:
        print(f"Installation failed: {e}")
        return False


def get_site_packages_dir(venv_bin_dir):
    """Get site-packages directory of virtual environment"""
    python_cmd = os.path.join(venv_bin_dir, "python")
    result = subprocess.check_output(
        [python_cmd, "-c", "import site; print(site.getsitepackages()[0])"]
    )
    return result.decode("utf-8").strip()


def run_tests(venv_bin_dir, args):
    """Run tests in virtual environment"""
    pytest_cmd = os.path.join(venv_bin_dir, "pytest")

    # Build pytest command
    cmd = [pytest_cmd]
    if args.verbose:
        cmd.append("-v")
    if args.coverage:
        cmd.extend(["--cov=isaacsim_links", "--cov-report=term", "--cov-report=html"])
    if args.test_pattern:
        cmd.append(args.test_pattern)

    print(f"Running test command: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run isaacsim-links tests in virtual environment")
    parser.add_argument(
        "--venv-dir", default=".venv", help="Virtual environment directory (default: .venv)"
    )
    parser.add_argument("--recreate", action="store_true", help="Recreate virtual environment")
    parser.add_argument(
        "--no-install", action="store_true", help="Don't install package, assume already installed"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Output verbose test information"
    )
    parser.add_argument("--coverage", action="store_true", help="Generate test coverage report")
    parser.add_argument("--test-pattern", default=None, help="Only run tests matching this pattern")
    parser.add_argument(
        "--no-dev", action="store_true", help="Install in standard mode instead of development mode"
    )

    args = parser.parse_args()

    # Get script and package paths
    script_dir = Path(__file__).parent
    venv_dir = script_dir / args.venv_dir

    # Create virtual environment (if needed)
    if not venv_dir.exists() or args.recreate:
        create_venv(venv_dir, clear=args.recreate)

    # Get directory for executable files in virtual environment
    venv_bin_dir = get_venv_bin_dir(venv_dir)

    # Upgrade pip
    upgrade_pip(venv_bin_dir)

    # Install package (if needed)
    if not args.no_install:
        success = install_package(venv_bin_dir, script_dir, dev=not args.no_dev)
        if not success:
            print("Installation failed, unable to continue running tests")
            return 1

    # Run tests
    return run_tests(venv_bin_dir, args)


if __name__ == "__main__":
    sys.exit(main())

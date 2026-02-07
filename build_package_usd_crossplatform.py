#!/usr/bin/env python3
"""
build_package_usd_crossplatform.py

- Optionally builds OpenUSD from source using build_scripts/build_usd.py
- Collects the built artifacts (pxr python package, native libs, plugins, resources, LICENSE/NOTICE)
  into a package directory (usd_core/) ready for python -m build.
- Works on both Windows and Linux/macOS.

Usage examples:
  # Build then prepare (default)
  python build_package_usd_crossplatform.py

  # Skip build and use an existing install
  python build_package_usd_crossplatform.py --skip-build
"""
from __future__ import annotations
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# Platform detection
IS_WINDOWS  = sys.platform == "win32"
IS_LINUX    = sys.platform == "linux"
IS_MACOS    = sys.platform == "darwin"

# Platform-specific file extensions
if IS_WINDOWS:
    LIB_EXTS = ['.dll']
    BIN_EXTS = ['.cmd', '.exe']
else:  # Linux/macOS
    LIB_EXTS = ['.so']
    BIN_EXTS = []  # No extension needed on Unix


USD_SRC = Path.cwd() / "OpenUSD"
BUILD_PATH = Path.cwd() / "usd_build"
PKG_PATH = Path.cwd() / "packaged_usd"


def run_cmd(cmd: str, cwd: str|None=None):
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.stderr.write(f"❗Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)


def copy_tree(src: Path, dst: Path):
    if not src.exists():
        print(f"Source not found: {src} (skipping)")
        return
    print(f"Copying: {src} -> {dst}")
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_files_with_ext(src_dirs: Path, dst_dir: Path, exts: list[str]):
    dst_dir.mkdir(parents=True, exist_ok=True)
    if not src_dirs.exists():
        print(f"Source directory not found: {src_dirs} (skipping)")
        return
    for d in src_dirs.iterdir():
        if d.is_file() and d.suffix.lower() in exts:
            shutil.copy(d, dst_dir)


def copy_unix_binaries(src_dir: Path, dst_dir: Path):
    """Copy executable binaries on Unix (no extension check needed)."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir} (skipping)")
        return
    for item in src_dir.iterdir():
        if item.is_file() and item.stat().st_mode & 0o111:  # Check if executable
            shutil.copy(item, dst_dir)


def run_build():
    """Run the OpenUSD build script (build_scripts/build_usd.py)."""
    build_script = USD_SRC / "build_scripts" / "build_usd.py"
    if not build_script.exists():
        raise FileNotFoundError(f"Could not find build_usd.py at {build_script}")

    usd_cmd = [
        sys.executable, str(build_script),
        "--python",
        "--no-python-docs",
        "--no-debug-python",
        "--no-examples",
        "--no-tutorials",
        "--tools",
        "--no-materialx",
        "--usd-imaging",
        "--no-ptex",
        "--no-openvdb",
        "--usdview",
        "--no-zlib",
        "--no-vulkan",
        "--no-materialx",
        "--build-monolithic",
        "--build-variant", 'release',
        str(BUILD_PATH)
    ]


    print(f"Running USD build on {platform.system()}:")
    run_cmd(usd_cmd)


def prepare_package():
    copy_tree(BUILD_PATH / 'lib' / 'python', PKG_PATH / 'site-packages')
    copy_tree(BUILD_PATH / 'lib' / 'usd',    PKG_PATH / 'site-packages' / 'pxr' / 'plugInfo')
    copy_tree(BUILD_PATH / 'plugin' / 'usd', PKG_PATH / 'site-packages' / 'pxr' / 'plugInfo')

    # Copy native libraries (platform-specific extensions)
    copy_files_with_ext(BUILD_PATH / 'lib',  PKG_PATH / 'site-packages' / 'pxr', LIB_EXTS)
    copy_files_with_ext(BUILD_PATH / 'bin',  PKG_PATH / 'site-packages' / 'pxr', LIB_EXTS)

    # Copy binaries (platform-specific)
    if IS_WINDOWS:
        copy_files_with_ext(BUILD_PATH / 'bin', PKG_PATH / 'Scripts', BIN_EXTS)
    else:
        copy_unix_binaries(BUILD_PATH / 'bin', PKG_PATH / 'Scripts')

    shutil.copy(USD_SRC / 'LICENSE.txt', PKG_PATH)
    shutil.copy(USD_SRC / 'NOTICE.txt',  PKG_PATH)
    shutil.copy(USD_SRC / 'README.md',   PKG_PATH)

    # Platform-specific pxr/__init__.py setup
    init_file = PKG_PATH / 'site-packages' / 'pxr' / '__init__.py'
    with open(init_file, 'a') as init_module:
        if IS_WINDOWS:
            init_module.write(r'''
# appended to this file for the Windows PyPI package
import os, sys
dllPath = os.path.split(os.path.realpath(__file__))[0]
if sys.version_info >= (3, 8, 0):
    os.environ['PXR_USD_WINDOWS_DLL_PATH'] = dllPath
# Note that we ALWAYS modify the PATH, even for python-3.8+. This is because:
#    - Anaconda python interpreters are modified to use the old, pre-3.8, PATH-
#      based method of loading dlls
#    - extra calls to os.add_dll_directory won't hurt these anaconda
#      interpreters
#    - similarly, adding the extra PATH entry shouldn't hurt standard python
#      interpreters
#    - there's no canonical/bulletproof way to check for an anaconda interpreter
os.environ['PATH'] = dllPath + os.pathsep + os.environ['PATH']
''')
        else:
            # Linux/macOS: Set library path if needed
            init_module.write(r'''
# appended to this file for the Unix PyPI package
import os, sys
libPath = os.path.split(os.path.realpath(__file__))[0]
if 'LD_LIBRARY_PATH' in os.environ:
    os.environ['LD_LIBRARY_PATH'] = libPath + os.pathsep + os.environ['LD_LIBRARY_PATH']
else:
    os.environ['LD_LIBRARY_PATH'] = libPath
''')


def main():
    run_build()
    prepare_package()

    # build package
    build_package_cmd = [
        sys.executable, '-m', 'build', '--wheel', '--outdir', 'dist',
    ]
    run_cmd(build_package_cmd)


if __name__ == "__main__":
    main()

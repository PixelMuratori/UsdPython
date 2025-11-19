#!/usr/bin/env python3
"""
prepare_package.py

- Optionally builds OpenUSD from source using build_scripts/build_usd.py
- Collects the built artifacts (pxr python package, native libs, plugins, resources, LICENSE/NOTICE)
  into a package directory (usd_core/) ready for python -m build.

Usage examples:
  # Build then prepare (default)
  python prepare_package.py --src C:/dev/OpenUSD --install C:/dev/usd-install

  # Skip build and use an existing install
  python prepare_package.py --src C:/dev/OpenUSD --install C:/dev/usd-install --skip-build
"""
from __future__ import annotations
import glob
import shutil
import subprocess
import sys
import distutils
from pathlib import Path


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
    for d in src_dirs.iterdir():
        if d.is_file() and d.suffix.lower() in exts:
            shutil.copy(d, dst_dir)


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
        "--no-usdview",
        "--no-zlib",
        "--no-vulkan",
        "--no-materialx",
        "--build-monolithic",
        "--build-variant", 'release',
        str(BUILD_PATH)
    ]

    print("Running USD build:")
    run_cmd(usd_cmd)


def prepare_package():
    copy_tree(BUILD_PATH / 'lib' / 'python', PKG_PATH / 'site-packages')
    copy_tree(BUILD_PATH / 'lib' / 'usd',    PKG_PATH / 'site-packages' / 'pxr' / 'plugInfo')
    copy_tree(BUILD_PATH / 'plugin' / 'usd', PKG_PATH / 'site-packages' / 'pxr' / 'plugInfo')

    copy_files_with_ext(BUILD_PATH / 'lib',  PKG_PATH / 'site-packages' / 'pxr', ['.dll'])
    copy_files_with_ext(BUILD_PATH / 'bin',  PKG_PATH / 'site-packages' / 'pxr', ['.dll'])

    copy_files_with_ext(BUILD_PATH / 'bin',  PKG_PATH / 'Scripts', ['.cmd', '', '.exe'])

    copy_files_with_ext(BUILD_PATH / 'bin',  PKG_PATH / 'Scripts', ['.cmd', '', '.exe'])

    shutil.copy(USD_SRC / 'LICENSE.txt', PKG_PATH)
    shutil.copy(USD_SRC / 'NOTICE.txt',  PKG_PATH)
    shutil.copy(USD_SRC / 'README.md',   PKG_PATH)

    with open(PKG_PATH / 'site-packages' / 'pxr' / '__init__.py', 'a') as init_module:
        init_module.write(r'''
# appended to this file for the windows PyPI package
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

def py_distribution_name():
    # Detect Python version
    py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    abi_tag = py_tag  # for compiled extensions, ABI tag is same as python tag

    # Detect platform
    plat_tag = distutils.util.get_platform()

    return f"{py_tag}-{abi_tag}-{plat_tag}"


def rename_wheel_to_platform():
    """
    Rename a universal wheel (py3-none-any) to a platform-specific wheel
    based on current Python version and OS architecture.

    Example:
        usd-1.0.0-py3-none-any.whl
        -> usd-1.0.0-cp39-cp39-win_amd64.whl
    """
    wheel_dir = Path('dist')

    # Find the wheel file
    wheels = glob.glob(str(wheel_dir) + "/*.whl")
    if not wheels:
        raise FileNotFoundError(f"No wheel found in {wheel_dir}")
    if len(wheels) > 1:
        raise RuntimeError(f"Multiple wheels found in {wheel_dir}, cannot auto-rename")

    old_wheel = Path(wheels[0])
    base_name = old_wheel.name.replace("py3-none-any", py_distribution_name())
    new_wheel = wheel_dir / base_name

    # Rename
    shutil.move(old_wheel, new_wheel)
    print(f"Renamed wheel: {old_wheel} → {new_wheel}")
    return new_wheel

def main():
    # run_build()
    # prepare_package()

    dist = Path('dist')
    if dist.exists():
        shutil.rmtree('dist')
    # build package
    build_package_cmd = [
        sys.executable, '-m', 'build', '--wheel', '--outdir', 'dist',
    ]
    run_cmd(build_package_cmd)

    rename_wheel_to_platform()

if __name__ == "__main__":
    main()


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
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_USD_SRC = Path.cwd() / "OpenUSD"
DEFAULT_BUILD_PATH = Path.cwd() / "usd_build"
PKG_DIR = Path.cwd() / "usd_package"


def run_cmd(cmd: str, cwd: str|None=None):
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.stderr.write(f"❗Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)

# ---------------------------
# Build invocation helper
# ---------------------------
def run_build():
    """Run the OpenUSD build script (build_scripts/build_usd.py)."""
    build_script = DEFAULT_USD_SRC / "build_scripts" / "build_usd.py"
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
        str(DEFAULT_BUILD_PATH)
    ]

    print("Running USD build:")
    run_cmd(usd_cmd)


# ---------------------------
# File copy helpers
# ---------------------------
def copy_tree(src: Path, dst: Path):
    if not src.exists():
        print(f"Source not found: {src} (skipping)")
        return
    print(f"Copying: {src} -> {dst}")
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_files_with_ext(src_dirs, dst_dir: Path, exts):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for d in src_dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.suffix.lower() in exts:
                print(f"Copying {f.name} -> {dst_dir}")
                shutil.copy(f, dst_dir)


# ---------------------------
# Main prepare routine
# ---------------------------
def prepare_package(usd_src: Path, install_dir: Path, skip_build: bool, python_exe: str, extra_build_args: list):
    usd_src = usd_src.resolve()
    install_dir = install_dir.resolve()

    print(f"USD source: {usd_src}")
    print(f"Install dir: {install_dir}")
    print(f"Package dir (output): {PKG_DIR.resolve()}")

    # 1) Optionally run build
    if not skip_build:
        # Ensure install dir exists (build will create/install)
        install_dir.mkdir(parents=True, exist_ok=True)
        run_build(usd_src, install_dir, python_exe, extra_build_args)
    else:
        print("Skipping build step (--skip-build). Using existing install at", install_dir)

    # Minimal verification of expected install layout
    expected_pxr = install_dir / "lib" / "python" / "pxr"
    if not expected_pxr.exists():
        # some builds may put pxr under install/lib/pythonX.Y/site-packages/pxr
        alt = None
        for path in install_dir.rglob("pxr"):
            if path.is_dir() and (path / "__init__.py").exists():
                alt = path
                break
        if alt:
            print("Found pxr at alternate location:", alt)
            expected_pxr = alt
        else:
            raise FileNotFoundError("Couldn't find built pxr/ python package in install dir. Checked: " + str(install_dir))

    # 2) Clean target package directory
    if PKG_DIR.exists():
        print("Removing previous package dir:", PKG_DIR)
        shutil.rmtree(PKG_DIR)
    (PKG_DIR / "pxr").mkdir(parents=True, exist_ok=True)

    # 3) Copy pxr python package
    print("Copying pxr python package...")
    copy_tree(expected_pxr, PKG_DIR / "pxr")

    # 4) Copy native libs (Windows .dll, Linux .so, mac .dylib)
    lib_dirs = [install_dir / "bin", install_dir / "lib"]
    print("Copying native libs next to pxr...")
    copy_files_with_ext(lib_dirs, PKG_DIR / "pxr", exts={".dll", ".so", ".dylib", ".pyd"})

    # 5) Copy plugins directory
    plugins_src = install_dir / "plugins"
    if not plugins_src.exists():
        # sometimes plugins live in install/lib/plugins or install/share/...
        alt_plugins = None
        for candidate in install_dir.rglob("plugins"):
            if candidate.is_dir():
                alt_plugins = candidate
                break
        if alt_plugins:
            plugins_src = alt_plugins

    if plugins_src.exists():
        copy_tree(plugins_src, PKG_DIR / "plugins")
    else:
        print("No plugins/ dir found in install (this may be ok).")

    # 6) Copy resources (optional)
    resources_src = install_dir / "resources"
    if resources_src.exists():
        copy_tree(resources_src, PKG_DIR / "resources")

    # 7) Copy license files
    for license_name in ("LICENSE.txt", "LICENSE", "NOTICE.txt", "NOTICE"):
        p = install_dir / license_name
        if p.exists():
            shutil.copy(p, PKG_DIR / (license_name if license_name.endswith(".txt") else license_name + ".txt"))
            print("Copied", license_name)
    print("Prepare complete. Package folder:", PKG_DIR.resolve())


# ---------------------------
# CLI
# ---------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--install", type=Path, default=DEFAULT_BUILD_PATH,
                   help="Path to USD install/build output (where build_usd.py will --install to)")
    p.add_argument("--skip-build", action="store_true", help="Skip running the USD build; use existing install")
    args = p.parse_args()

    print(DEFAULT_USD_SRC, DEFAULT_BUILD_PATH)
    # prepare_package(args.src, args.install, args.skip_build, args.python_exe, args.build_arg)


if __name__ == "__main__":
    run_build()

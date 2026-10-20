import glob
import os
import re
import shutil
import tomllib
from pathlib import Path

TMP_DIRPATH = r"./tmp"
ADDON_SOURCE_DIRNAME = "python_classes"
RESOURCES_DIRNAME = "resources"
VERSION_FILEPATH = os.path.join(Path(__file__).parent.parent.parent, "VERSION")

# Wheels each manifest platform needs: (platform tag prefix, arch suffix, Python tags).
# Blender 4.5/5.0 bundle Python 3.11, 5.1+ bundle 3.13; Blender 5.x has no Intel macOS build.
REQUIRED_WHEELS = {
    "windows-x64": ("win", "amd64", ("cp311", "cp313")),
    "linux-x64": ("manylinux", "x86_64", ("cp311", "cp313")),
    "macos-arm64": ("macosx", "arm64", ("cp311", "cp313")),
    "macos-x64": ("macosx", "x86_64", ("cp311",)),
}


def read_version():
    with open(VERSION_FILEPATH) as f:
        return f.read().strip()


def sync_manifest_version():
    """Sync blender_manifest.toml version with VERSION file."""
    version = read_version().replace("_", ".")
    manifest_path = "blender_manifest.toml"
    with open(manifest_path) as f:
        content = f.read()
    content = re.sub(r'^version = "[^"]+"', f'version = "{version}"', content, flags=re.MULTILINE)
    with open(manifest_path, "w") as f:
        f.write(content)
    print(f"Synced manifest version to {version}")


def sync_pyproject_version(filepath):
    """Sync a pyproject.toml version with VERSION file."""
    version = read_version().replace("_", ".")
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r'^version = "[^"]+"', f'version = "{version}"', content, flags=re.MULTILINE)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Synced {filepath} version to {version}")


def sync_all_versions():
    """Sync all version files with VERSION."""
    sync_manifest_version()
    sync_pyproject_version("pyproject.toml")
    sync_pyproject_version("m_tree/pyproject.toml")


def update_manifest_wheels(manifest_path, wheel_files):
    """Update manifest with wheel paths."""
    with open(manifest_path) as f:
        content = f.read()

    # Format wheel list for TOML
    wheel_list = ",\n    ".join(f'"{whl}"' for whl in wheel_files)
    wheels_toml = f"wheels = [\n    {wheel_list}\n]"

    # Replace existing wheels line
    content = re.sub(r"wheels = \[\]", wheels_toml, content)

    with open(manifest_path, "w") as f:
        f.write(content)
    print(f"Updated manifest with {len(wheel_files)} wheels")


def check_wheels(manifest_path, wheel_files):
    """Fail if a manifest platform lacks a wheel for a Blender Python it must support."""
    with open(manifest_path, "rb") as f:
        platforms = tomllib.load(f)["platforms"]

    # Wheel file names are name-version-python-abi-platform.whl
    built = [Path(whl).stem.split("-") for whl in wheel_files]
    missing = []
    for platform in platforms:
        prefix, arch, pythons = REQUIRED_WHEELS[platform]
        for python in pythons:
            if not any(
                parts[2] == python and parts[4].startswith(prefix) and parts[4].endswith(arch)
                for parts in built
            ):
                missing.append(f"{platform} {python}")

    if missing:
        raise Exception(f"Missing wheels for: {', '.join(missing)}")


def setup_addon_directory():
    sync_all_versions()
    version = read_version()
    addon_dirpath = os.path.join(TMP_DIRPATH, f"modular_tree_{version}")
    root = os.path.join(addon_dirpath, "modular_tree")
    wheels_dir = os.path.join(root, "wheels")
    Path(wheels_dir).mkdir(exist_ok=True, parents=True)

    all_files = os.listdir(".")

    # Copy addon files (excluding backup files like .blend1)
    ignore_patterns = shutil.ignore_patterns("*.blend1", "__pycache__")
    for f in all_files:
        if f.endswith(".py") or f == "blender_manifest.toml":
            shutil.copy2(os.path.join(".", f), root)
        elif f in (ADDON_SOURCE_DIRNAME, RESOURCES_DIRNAME):
            shutil.copytree(os.path.join(".", f), os.path.join(root, f), ignore=ignore_patterns)

    # Copy wheels from downloaded artifacts
    wheel_files = []
    for whl in glob.glob("wheels/**/*.whl", recursive=True):
        shutil.copy2(whl, wheels_dir)
        wheel_files.append(f"./wheels/{os.path.basename(whl)}")
        print(f"Copied wheel: {whl}")

    if not wheel_files:
        list_files(".")
        raise Exception("No wheel files found in wheels/ directory")

    check_wheels("blender_manifest.toml", wheel_files)

    # Update manifest with wheel paths
    update_manifest_wheels(os.path.join(root, "blender_manifest.toml"), wheel_files)

    return addon_dirpath


def create_zip(input_dir, output_dir):
    """Create a zip archive (for manual builds without Blender CLI)."""
    basename = os.path.join(output_dir, Path(input_dir).stem)
    filepath = shutil.make_archive(basename, "zip", input_dir)
    return filepath


def get_addon_root(addon_dirpath):
    """Return the inner addon root directory path."""
    return os.path.join(addon_dirpath, "modular_tree")


def list_files(root_directory):
    excluded_directories = {"dependencies", "build", "__pycache__", ".github", ".git"}
    for root, _, files in os.walk(root_directory):
        should_skip = False
        for exclusion in excluded_directories:
            if exclusion in root:
                should_skip = True
                break
        if should_skip:
            continue

        level = root.replace(root_directory, "").count(os.sep)
        indent = " " * 4 * (level)
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Package the Modular Tree addon")
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Prepare directory only, skip zip creation (for use with Blender CLI)",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Only sync the manifest and pyproject versions with VERSION",
    )
    args = parser.parse_args()

    if args.sync_only:
        sync_all_versions()
        raise SystemExit

    addon_dirpath = setup_addon_directory()

    if args.no_zip:
        # Print the addon root path for Blender CLI to use
        print(f"Addon prepared at: {get_addon_root(addon_dirpath)}")
    else:
        archive_filepath = create_zip(addon_dirpath, TMP_DIRPATH)
        print(f"Created archive: {archive_filepath}")

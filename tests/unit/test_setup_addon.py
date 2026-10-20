"""Tests for the wheel check in the extension packaging script."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parents[2] / ".github" / "scripts" / "setup_addon.py"
_spec = importlib.util.spec_from_file_location("setup_addon", _SCRIPT)
setup_addon = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(setup_addon)

COMPLETE = [
    "./wheels/modular_tree-5.6.0-cp311-cp311-win_amd64.whl",
    "./wheels/modular_tree-5.6.0-cp313-cp313-win_amd64.whl",
    "./wheels/modular_tree-5.6.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
    "./wheels/modular_tree-5.6.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
    "./wheels/modular_tree-5.6.0-cp311-cp311-macosx_11_0_arm64.whl",
    "./wheels/modular_tree-5.6.0-cp313-cp313-macosx_11_0_arm64.whl",
    "./wheels/modular_tree-5.6.0-cp311-cp311-macosx_11_0_x86_64.whl",
]


@pytest.fixture
def manifest(tmp_path):
    path = tmp_path / "blender_manifest.toml"
    path.write_text('platforms = ["windows-x64", "macos-x64", "macos-arm64", "linux-x64"]\n')
    return path


def test_complete_wheel_set_passes(manifest):
    setup_addon.check_wheels(manifest, COMPLETE)


def test_missing_intel_mac_wheel_fails(manifest):
    # 5.5.2 shipped exactly this set, so Intel Macs got no m_tree (#34).
    wheels = [whl for whl in COMPLETE if "macosx_11_0_x86_64" not in whl]
    with pytest.raises(Exception, match="macos-x64 cp311"):
        setup_addon.check_wheels(manifest, wheels)

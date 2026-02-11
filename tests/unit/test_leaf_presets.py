"""Unit tests for leaf species preset data."""

# Import directly from module (path setup in conftest.py)
from leaf_presets import LEAF_PRESETS, LeafPreset, get_leaf_preset_items

EXPECTED_PRESETS = ["OAK", "MAPLE", "BIRCH", "WILLOW", "PINE"]

# Expected values from research.md R4 table
EXPECTED_CONTOUR = {
    "OAK": {"m": 7.0, "a": 1.0, "b": 1.0, "n1": 2.0, "n2": 4.0, "n3": 4.0, "aspect_ratio": 0.7},
    "MAPLE": {"m": 5.0, "a": 1.0, "b": 1.0, "n1": 1.5, "n2": 3.0, "n3": 3.0, "aspect_ratio": 0.95},
    "BIRCH": {"m": 2.0, "a": 1.0, "b": 0.6, "n1": 2.5, "n2": 8.0, "n3": 8.0, "aspect_ratio": 0.6},
    "WILLOW": {
        "m": 2.0,
        "a": 1.0,
        "b": 0.3,
        "n1": 3.0,
        "n2": 10.0,
        "n3": 10.0,
        "aspect_ratio": 0.2,
    },
    "PINE": {
        "m": 2.0,
        "a": 1.0,
        "b": 0.05,
        "n1": 4.0,
        "n2": 20.0,
        "n3": 20.0,
        "aspect_ratio": 0.05,
    },
}

EXPECTED_MARGIN = {
    "OAK": {"margin_type": 4, "tooth_count": 7, "tooth_depth": 0.3},
    "MAPLE": {"margin_type": 4, "tooth_count": 5, "tooth_depth": 0.5},
    "BIRCH": {"margin_type": 1, "tooth_count": 24, "tooth_depth": 0.05},
    "WILLOW": {"margin_type": 0, "tooth_count": 0, "tooth_depth": 0.0},
    "PINE": {"margin_type": 0, "tooth_count": 0, "tooth_depth": 0.0},
}


def test_all_presets_exist():
    """All 5 species presets must exist."""
    for name in EXPECTED_PRESETS:
        assert name in LEAF_PRESETS, f"Missing preset: {name}"


def test_preset_count():
    """Exactly 5 presets should exist."""
    assert len(LEAF_PRESETS) == 5


def test_preset_is_dataclass():
    """All presets should be LeafPreset instances."""
    for name, preset in LEAF_PRESETS.items():
        assert isinstance(preset, LeafPreset), f"{name} is not a LeafPreset"


def test_preset_contour_values():
    """Preset contour parameters must match research.md R4 table."""
    for name, expected in EXPECTED_CONTOUR.items():
        preset = LEAF_PRESETS[name]
        for key, value in expected.items():
            actual = preset.contour[key]
            assert actual == value, f"{name}.contour.{key}: expected {value}, got {actual}"


def test_preset_margin_values():
    """Preset margin parameters must match research.md R4 table."""
    for name, expected in EXPECTED_MARGIN.items():
        preset = LEAF_PRESETS[name]
        for key, value in expected.items():
            actual = preset.margin[key]
            assert actual == value, f"{name}.margin.{key}: expected {value}, got {actual}"


def test_preset_names_valid():
    """Preset names must match expected identifiers."""
    for name, preset in LEAF_PRESETS.items():
        assert preset.name == name, f"Preset name mismatch: {preset.name} != {name}"
        assert isinstance(preset.label, str) and len(preset.label) > 0
        assert isinstance(preset.description, str) and len(preset.description) > 0


def test_preset_has_required_sections():
    """Each preset must have contour, margin, venation, and deformation dicts."""
    for name, preset in LEAF_PRESETS.items():
        assert isinstance(preset.contour, dict), f"{name} missing contour"
        assert isinstance(preset.margin, dict), f"{name} missing margin"
        assert isinstance(preset.venation, dict), f"{name} missing venation"
        assert isinstance(preset.deformation, dict), f"{name} missing deformation"


def test_pine_venation_disabled():
    """Pine should have venation disabled."""
    pine = LEAF_PRESETS["PINE"]
    assert pine.venation["enable_venation"] is False


def test_oak_venation_enabled():
    """Oak should have venation enabled with OPEN type."""
    oak = LEAF_PRESETS["OAK"]
    assert oak.venation["enable_venation"] is True
    assert oak.venation["venation_type"] == 0  # OPEN


# Expected corrected venation values (kill_distance was 100x too large before fix)
EXPECTED_VENATION = {
    "OAK": {
        "kill_distance": 0.03,
        "attraction_distance": 0.08,
        "growth_step_size": 0.01,
    },
    "MAPLE": {
        "kill_distance": 0.025,
        "attraction_distance": 0.08,
        "growth_step_size": 0.01,
    },
    "BIRCH": {
        "kill_distance": 0.03,
        "attraction_distance": 0.08,
        "growth_step_size": 0.01,
    },
    "WILLOW": {
        "kill_distance": 0.04,
        "attraction_distance": 0.08,
        "growth_step_size": 0.01,
    },
}


def test_venation_kill_distance_corrected():
    """kill_distance must be in 0.01-0.1 range (was 100x too large before fix)."""
    for name, expected in EXPECTED_VENATION.items():
        preset = LEAF_PRESETS[name]
        for key, value in expected.items():
            actual = preset.venation[key]
            assert actual == value, f"{name}.venation.{key}: expected {value}, got {actual}"


def test_venation_has_required_params():
    """Venation-enabled presets must have attraction_distance and growth_step_size."""
    for name, preset in LEAF_PRESETS.items():
        if preset.venation.get("enable_venation"):
            assert "attraction_distance" in preset.venation, f"{name} missing attraction_distance"
            assert "growth_step_size" in preset.venation, f"{name} missing growth_step_size"


def test_deformation_values():
    """Spot-check deformation values for species with natural curvature."""
    oak = LEAF_PRESETS["OAK"]
    assert oak.deformation["vein_displacement"] == 0.3
    assert oak.deformation["midrib_curvature"] == 0.1
    assert oak.deformation["edge_curl"] == 0.05

    willow = LEAF_PRESETS["WILLOW"]
    assert willow.deformation["midrib_curvature"] == 0.2
    assert willow.deformation["vein_displacement"] == 0.0


def test_get_leaf_preset_items():
    """get_leaf_preset_items() should return valid Blender EnumProperty items."""
    items = get_leaf_preset_items()
    assert len(items) == 5
    for item in items:
        assert len(item) == 3  # (identifier, label, description)
        assert isinstance(item[0], str)
        assert isinstance(item[1], str)
        assert isinstance(item[2], str)

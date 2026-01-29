"""Tests for tree preset system."""

# Import directly from module (path setup in conftest.py)
from tree_presets import (
    PROPERTY_WRAPPER_PARAMS,
    TREE_PRESETS,
    TreePreset,
    _generate_random_params,
    get_preset_items,
)


class TestTreePreset:
    """Tests for TreePreset dataclass."""

    def test_create_minimal_preset(self):
        """TreePreset can be created with only required fields."""
        preset = TreePreset(
            name="TEST",
            label="Test Tree",
            description="A test preset",
        )
        assert preset.name == "TEST"
        assert preset.label == "Test Tree"
        assert preset.description == "A test preset"
        assert preset.branches == {}
        assert preset.trunk == {}

    def test_create_preset_with_branches(self):
        """TreePreset can be created with branch parameters."""
        preset = TreePreset(
            name="CUSTOM",
            label="Custom",
            description="Custom tree",
            branches={"length": 10, "gravity_strength": 15},
        )
        assert preset.branches == {"length": 10, "gravity_strength": 15}

    def test_to_enum_item(self):
        """to_enum_item returns correct Blender enum tuple format."""
        preset = TreePreset(
            name="OAK",
            label="Oak",
            description="A mighty oak tree",
        )
        item = preset.to_enum_item()

        assert isinstance(item, tuple)
        assert len(item) == 3
        assert item == ("OAK", "Oak", "A mighty oak tree")


class TestTreePresetsRegistry:
    """Tests for TREE_PRESETS registry."""

    def test_expected_presets_exist(self):
        """Registry contains all expected preset types."""
        expected = {"OAK", "PINE", "WILLOW", "RANDOM"}
        assert set(TREE_PRESETS.keys()) == expected

    def test_all_presets_are_tree_preset_instances(self):
        """All registry values are TreePreset instances."""
        for name, preset in TREE_PRESETS.items():
            assert isinstance(preset, TreePreset), f"{name} is not a TreePreset"

    def test_preset_names_match_keys(self):
        """Preset name field matches its registry key."""
        for key, preset in TREE_PRESETS.items():
            assert preset.name == key, f"Preset {key} has mismatched name: {preset.name}"

    def test_oak_preset_has_expected_params(self):
        """OAK preset contains characteristic parameters."""
        oak = TREE_PRESETS["OAK"]
        assert "length" in oak.branches
        assert "gravity_strength" in oak.branches
        assert "start_angle" in oak.branches

    def test_random_preset_has_no_branches(self):
        """RANDOM preset has empty branches (generated at runtime)."""
        random_preset = TREE_PRESETS["RANDOM"]
        assert random_preset.branches == {}


class TestGetPresetItems:
    """Tests for get_preset_items function."""

    def test_returns_list_of_tuples(self):
        """get_preset_items returns a list of 3-tuples."""
        items = get_preset_items()

        assert isinstance(items, list)
        assert len(items) == len(TREE_PRESETS)
        for item in items:
            assert isinstance(item, tuple)
            assert len(item) == 3

    def test_all_tuples_contain_strings(self):
        """Each tuple element is a string (Blender enum requirement)."""
        items = get_preset_items()

        for name, label, description in items:
            assert isinstance(name, str), f"name {name!r} is not a string"
            assert isinstance(label, str), f"label {label!r} is not a string"
            assert isinstance(description, str), f"description {description!r} is not a string"

    def test_names_are_uppercase_identifiers(self):
        """Preset names are uppercase (Blender enum convention)."""
        items = get_preset_items()

        for name, _, _ in items:
            assert name.isupper(), f"Preset name {name!r} should be uppercase"
            assert name.isidentifier(), f"Preset name {name!r} should be a valid identifier"


class TestGenerateRandomParams:
    """Tests for _generate_random_params function."""

    def test_returns_dict(self):
        """Function returns a dictionary."""
        params = _generate_random_params()
        assert isinstance(params, dict)

    def test_contains_expected_keys(self):
        """Random params contain all expected parameter keys."""
        params = _generate_random_params()
        expected_keys = {
            "length",
            "branches_density",
            "start_angle",
            "gravity_strength",
            "up_attraction",
            "flatness",
            "stiffness",
        }
        assert set(params.keys()) == expected_keys

    def test_values_are_numeric(self):
        """All parameter values are numeric."""
        params = _generate_random_params()
        for key, value in params.items():
            assert isinstance(value, (int, float)), f"{key} value {value!r} is not numeric"

    def test_values_within_reasonable_ranges(self):
        """Parameter values fall within expected ranges."""
        # Run multiple times to catch range issues
        # Use slightly wider bounds to account for float precision (e.g., 0.4 + 0.8 = 1.2000000000000002)
        for _ in range(10):
            params = _generate_random_params()

            assert 5 <= params["length"] <= 15
            assert 0.4 - 1e-9 <= params["branches_density"] <= 1.2 + 1e-9
            assert 30 <= params["start_angle"] <= 80
            assert 5 <= params["gravity_strength"] <= 20
            assert 0.1 - 1e-9 <= params["up_attraction"] <= 0.6 + 1e-9
            assert 0.1 - 1e-9 <= params["flatness"] <= 0.5 + 1e-9
            assert 0.05 - 1e-9 <= params["stiffness"] <= 0.35 + 1e-9


class TestPropertyWrapperParams:
    """Tests for PROPERTY_WRAPPER_PARAMS constant."""

    def test_contains_expected_params(self):
        """PROPERTY_WRAPPER_PARAMS has the expected parameter names."""
        expected = {"length", "start_radius", "randomness", "start_angle"}
        assert expected == PROPERTY_WRAPPER_PARAMS

    def test_is_set(self):
        """PROPERTY_WRAPPER_PARAMS is a set for O(1) lookups."""
        assert isinstance(PROPERTY_WRAPPER_PARAMS, set)

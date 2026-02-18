"""Tree generation presets for quick tree creation.

This module defines preset configurations for different tree types.
Each preset specifies branch function parameters that produce a
characteristic tree shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Parameters that require PropertyWrapper (ConstantProperty) instead of raw values
PROPERTY_WRAPPER_PARAMS = {"length", "start_radius", "randomness", "start_angle"}

# Mapping from preset parameter names to nested C++ struct paths on BranchFunction.
# Parameters not in this map are set directly on BranchFunction.
_NESTED_PROPERTY_MAP = {
    "start": ("distribution", "start"),
    "end": ("distribution", "end"),
    "branches_density": ("distribution", "density"),
    "phillotaxis": ("distribution", "phillotaxis"),
    "gravity_strength": ("gravity", "strength"),
    "stiffness": ("gravity", "stiffness"),
    "up_attraction": ("gravity", "up_attraction"),
    "split_proba": ("split", "probability"),
    "split_radius": ("split", "radius"),
    "split_angle": ("split", "angle"),
    "crown_shape": ("crown", "shape"),
    "crown_base_size": ("crown", "base_size"),
    "crown_height": ("crown", "height"),
    "crown_angle_variation": ("crown", "angle_variation"),
}


@dataclass
class TreePreset:
    """Configuration for a tree generation preset."""

    name: str
    label: str
    description: str
    branches: dict[str, Any] = field(default_factory=dict)
    trunk: dict[str, Any] = field(default_factory=dict)
    growth: dict[str, Any] = field(default_factory=dict)
    sub_branches: dict[str, Any] = field(default_factory=dict)
    leaf_params: dict[str, Any] = field(default_factory=dict)

    def to_enum_item(self) -> tuple[str, str, str]:
        """Convert to Blender EnumProperty item tuple."""
        return (self.name, self.label, self.description)


# Default trunk parameters shared across presets
_DEFAULT_TRUNK_PARAMS = {
    "length": 14,
    "start_radius": 0.3,
    "end_radius": 0.05,
    "shape": 0.7,
    "up_attraction": 0.6,
    "resolution": 3,
    "randomness": 1,
}

# Default branch parameters shared across presets
_DEFAULT_BRANCH_PARAMS = {
    "start": 0.1,
    "end": 0.95,
    "resolution": 3,
    "split_proba": 0.5,
    "break_chance": 0.02,
    "start_radius": 0.4,
    "randomness": 0.5,
}


TREE_PRESETS: dict[str, TreePreset] = {
    "RANDOM": TreePreset(
        name="RANDOM",
        label="Random",
        description="Random tree with varied parameters",
    ),
    "OAK": TreePreset(
        name="OAK",
        label="Oak",
        description="Broad spreading tree with thick trunk",
        trunk={
            "length": 7,  # Shorter trunk - oaks branch low
            "start_radius": 0.5,  # Thicker base
            "end_radius": 0.15,  # Less taper - branches into major limbs
            "shape": 0.5,  # More gradual taper
            "up_attraction": 0.5,  # Straighter trunk
        },
        branches={
            "start": 0.15,  # Branches start slightly up the trunk
            "length": 8,  # Shorter branches that split more
            "branches_density": 1.8,  # Many branches to fill crown
            "start_angle": 55,  # Less horizontal, more room to grow up
            "gravity_strength": 6,  # Much less droop - branches hold up
            "up_attraction": 0.45,  # More upward growth for dome shape
            "flatness": 0.35,  # Slightly less flat
            "stiffness": 0.2,  # Stiffer branches resist gravity
            "split_proba": 0.65,  # More splitting for denser crown
        },
    ),
    "PINE": TreePreset(
        name="PINE",
        label="Pine",
        description="Tall conifer with horizontal tiered branches",
        trunk={
            "length": 14,
            "start_radius": 0.3,
            "end_radius": 0.05,
            "shape": 1.0,
            "up_attraction": 0.6,
            "randomness": 0.2,
        },
        branches={
            "start": 0.2,
            "length": 7,
            "branches_density": 2.5,
            "start_angle": 60,
            "randomness": 0.5,
            "flatness": 0.5,
            "up_attraction": 0.0,
            "gravity_strength": 10,
            "stiffness": 0.1,
            "split_proba": 0.5,
            "split_radius": 0.8,
            "split_angle": 35,
            "phillotaxis": 137.5,
            "break_chance": 0.01,
            "start_radius": 0.4,
            "crown_shape": "Conical",
        },
        sub_branches={
            "start": 0.1,
            "end": 0.95,
            "length": 2,
            "branches_density": 4.0,
            "start_angle": 45,
            "randomness": 0.5,
            "flatness": 1.0,
            "up_attraction": 0.0,
            "gravity_strength": 14,
            "stiffness": 0.1,
            "split_proba": 0.5,
            "split_radius": 0.8,
            "split_angle": 35,
            "phillotaxis": 137.5,
            "break_chance": 0.02,
            "resolution": 3,
            "start_radius": 0.4,
        },
        leaf_params={
            "density": 350.0,
            "scale": 1.0,
            "max_radius": 0.03,
        },
    ),
    "WILLOW": TreePreset(
        name="WILLOW",
        label="Willow",
        description="Drooping branches with weeping form",
        trunk={
            "length": 8,
            "start_radius": 0.5,
            "end_radius": 0.15,
            "shape": 0.4,
            "up_attraction": 0.8,
        },
        branches={
            # Structural limbs — spread wide to form umbrella dome
            "start": 0.3,
            "end": 0.9,
            "length": 8,
            "branches_density": 1.2,
            "start_angle": 55,
            "gravity_strength": 5,
            "stiffness": 0.5,
            "up_attraction": 0.6,
            "flatness": 0.15,
            "split_proba": 0.5,
            "break_chance": 0.01,
            "start_radius": 0.7,
            "randomness": 0.3,
        },
        sub_branches={
            # Hanging whips — smooth arc from parent then droop into curtain
            "start": 0.3,
            "end": 0.95,
            "length": 8,
            "branches_density": 1.2,
            "start_angle": 65,
            "gravity_strength": 350,
            "stiffness": 0.1,
            "up_attraction": -0.8,
            "flatness": 0.0,
            "split_proba": 0.02,
            "break_chance": 0.005,
            "start_radius": 0.35,
            "end_radius": 0.02,
            "randomness": 0.2,
            "resolution": 3,
        },
        leaf_params={
            "density": 350.0,
            "scale": 0.18,
            "max_radius": 0.03,
        },
    ),
}


def get_preset_items() -> list[tuple[str, str, str]]:
    """Get preset enum items for Blender EnumProperty."""
    return [preset.to_enum_item() for preset in TREE_PRESETS.values()]


def _generate_random_params() -> dict[str, Any]:
    """Generate randomized branch parameters."""
    return {
        "length": randint(5, 15),
        "branches_density": 0.4 + (randint(0, 8) / 10),  # 0.4 to 1.2
        "start_angle": randint(30, 80),
        "gravity_strength": randint(5, 20),
        "up_attraction": 0.1 + (randint(0, 5) / 10),
        "flatness": randint(1, 5) / 10,
        "stiffness": 0.05 + (randint(0, 3) / 10),
    }


def _wrap_property_value(key: str, value):
    """Wrap value in PropertyWrapper(ConstantProperty) if the parameter requires it."""
    if key == "crown_shape":
        from ..m_tree_wrapper import lazy_m_tree as m_tree

        return getattr(m_tree.CrownShape, value)
    if key in PROPERTY_WRAPPER_PARAMS:
        from ..m_tree_wrapper import lazy_m_tree as m_tree

        constant = m_tree.ConstantProperty(float(value))
        return m_tree.PropertyWrapper(constant)
    return value


def _set_branch_param(branches, key: str, value) -> None:
    """Set a parameter on a BranchFunction, handling nested struct properties."""
    wrapped = _wrap_property_value(key, value)
    if key in _NESTED_PROPERTY_MAP:
        struct_name, field_name = _NESTED_PROPERTY_MAP[key]
        struct = getattr(branches, struct_name)
        setattr(struct, field_name, wrapped)
    else:
        setattr(branches, key, wrapped)


def apply_preset(branches, preset_name: str) -> None:
    """Apply a preset's parameters to a BranchFunction instance.

    Args:
        branches: A BranchFunction instance to configure.
        preset_name: Key from TREE_PRESETS or 'RANDOM' for randomized params.
    """
    # Apply defaults first
    for key, value in _DEFAULT_BRANCH_PARAMS.items():
        _set_branch_param(branches, key, value)

    # Get preset-specific or random parameters
    if preset_name == "RANDOM":
        params = _generate_random_params()
    else:
        preset = TREE_PRESETS.get(preset_name)
        params = preset.branches if preset else {}

    # Apply preset parameters
    for key, value in params.items():
        _set_branch_param(branches, key, value)


def apply_trunk_preset(trunk, preset_name: str) -> None:
    """Apply a preset's trunk parameters to a TrunkFunction instance.

    Args:
        trunk: A TrunkFunction instance to configure.
        preset_name: Key from TREE_PRESETS or 'RANDOM' for default params.
    """
    # Apply defaults first
    for key, value in _DEFAULT_TRUNK_PARAMS.items():
        setattr(trunk, key, value)

    # Apply preset-specific parameters (RANDOM uses defaults)
    if preset_name != "RANDOM":
        preset = TREE_PRESETS.get(preset_name)
        if preset and preset.trunk:
            for key, value in preset.trunk.items():
                setattr(trunk, key, value)


def apply_sub_branch_preset(branches, preset_name: str) -> None:
    """Apply a preset's sub_branches parameters to a BranchFunction instance.

    Args:
        branches: A BranchFunction instance to configure.
        preset_name: Key from TREE_PRESETS.
    """
    # Apply defaults first
    for key, value in _DEFAULT_BRANCH_PARAMS.items():
        _set_branch_param(branches, key, value)

    # Apply preset-specific sub_branches overrides
    preset = TREE_PRESETS.get(preset_name)
    if preset and preset.sub_branches:
        for key, value in preset.sub_branches.items():
            _set_branch_param(branches, key, value)


# Growth function presets
GROWTH_PRESETS: dict[str, dict] = {
    "STRUCTURED": {
        "iterations": 6,
        "apical_dominance": 0.85,
        "split_threshold": 0.8,
        "grow_threshold": 0.4,
        "gravitropism": 0.15,
        "randomness": 0.05,
    },
    "SPREADING": {
        "iterations": 5,
        "apical_dominance": 0.5,
        "split_threshold": 0.6,
        "grow_threshold": 0.3,
        "gravity_strength": 1.5,
    },
    "WEEPING": {
        "iterations": 7,
        "apical_dominance": 0.6,
        "gravitropism": -0.1,
        "gravity_strength": 3.0,
        "branch_length": 1.5,
        "randomness": 0.15,
    },
    "GNARLED": {
        "iterations": 8,
        "apical_dominance": 0.4,
        "split_threshold": 0.5,
        "randomness": 0.3,
        "gravity_strength": 2.0,
    },
}


def get_growth_preset_items() -> list[tuple[str, str, str]]:
    """Get growth preset enum items for Blender EnumProperty."""
    return [
        ("STRUCTURED", "Structured", "Orderly growth with strong apical dominance"),
        ("SPREADING", "Spreading", "Wide, spreading canopy with many branches"),
        ("WEEPING", "Weeping", "Drooping branches like a willow"),
        ("GNARLED", "Gnarled", "Twisted, organic growth pattern"),
    ]


def apply_growth_preset(growth_func, preset_name: str) -> None:
    """Apply a growth preset's parameters to a GrowthFunction instance.

    Args:
        growth_func: A GrowthFunction instance to configure.
        preset_name: Key from GROWTH_PRESETS.
    """
    preset = GROWTH_PRESETS.get(preset_name, {})
    for key, value in preset.items():
        if hasattr(growth_func, key):
            setattr(growth_func, key, value)

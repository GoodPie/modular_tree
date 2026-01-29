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


@dataclass
class TreePreset:
    """Configuration for a tree generation preset."""

    name: str
    label: str
    description: str
    branches: dict[str, Any] = field(default_factory=dict)
    trunk: dict[str, Any] = field(default_factory=dict)

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
            "up_attraction": 0.4,  # Slight lean is natural for oaks
        },
        branches={
            "start": 0.0,  # Branches start at trunk base
            "length": 10,  # Slightly shorter branches
            "branches_density": 0.6,  # Fewer but larger branches
            "start_angle": 70,  # Wider spread
            "gravity_strength": 18,  # More droop
            "up_attraction": 0.2,  # Less upward pull
            "flatness": 0.4,  # More horizontal spread
            "stiffness": 0.12,
        },
    ),
    "PINE": TreePreset(
        name="PINE",
        label="Pine",
        description="Tall conifer with upward branches",
        trunk={
            "length": 18,  # Tall trunk
            "start_radius": 0.25,  # Thinner
            "end_radius": 0.03,  # Sharp taper
            "shape": 0.9,  # Aggressive taper at top
            "up_attraction": 0.8,  # Very straight
        },
        branches={
            "length": 6,
            "branches_density": 1.0,
            "start_angle": 80,
            "gravity_strength": 2,
            "up_attraction": 0.8,
            "flatness": 0.1,
            "stiffness": 0.3,
        },
    ),
    "WILLOW": TreePreset(
        name="WILLOW",
        label="Willow",
        description="Drooping branches with weeping form",
        trunk={
            "length": 10,
            "start_radius": 0.35,
            "end_radius": 0.08,
            "shape": 0.6,
            "up_attraction": 0.5,
        },
        branches={
            "length": 15,
            "branches_density": 0.6,
            "start_angle": 45,
            "gravity_strength": 30,
            "up_attraction": -0.2,
            "flatness": 0.2,
            "stiffness": 0.02,
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


def _wrap_property_value(key: str, value: float):
    """Wrap value in PropertyWrapper(ConstantProperty) if the parameter requires it."""
    if key in PROPERTY_WRAPPER_PARAMS:
        from ..m_tree_wrapper import lazy_m_tree as m_tree

        constant = m_tree.ConstantProperty(float(value))
        return m_tree.PropertyWrapper(constant)
    return value


def apply_preset(branches, preset_name: str) -> None:
    """Apply a preset's parameters to a BranchFunction instance.

    Args:
        branches: A BranchFunction instance to configure.
        preset_name: Key from TREE_PRESETS or 'RANDOM' for randomized params.
    """
    # Apply defaults first
    for key, value in _DEFAULT_BRANCH_PARAMS.items():
        setattr(branches, key, _wrap_property_value(key, value))

    # Get preset-specific or random parameters
    if preset_name == "RANDOM":
        params = _generate_random_params()
    else:
        preset = TREE_PRESETS.get(preset_name)
        params = preset.branches if preset else {}

    # Apply preset parameters
    for key, value in params.items():
        setattr(branches, key, _wrap_property_value(key, value))


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

"""Leaf species preset data for procedural leaf generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Margin type constants matching C++ MarginType enum
MARGIN_ENTIRE = 0
MARGIN_SERRATE = 1
MARGIN_DENTATE = 2
MARGIN_CRENATE = 3
MARGIN_LOBED = 4

# Venation type constants matching C++ VenationType enum
VENATION_OPEN = 0
VENATION_CLOSED = 1


@dataclass
class LeafPreset:
    """Configuration for a leaf species preset."""

    name: str
    label: str
    description: str
    contour: dict[str, Any] = field(default_factory=dict)
    margin: dict[str, Any] = field(default_factory=dict)
    venation: dict[str, Any] = field(default_factory=dict)
    deformation: dict[str, Any] = field(default_factory=dict)

    def to_enum_item(self) -> tuple[str, str, str]:
        return (self.name, self.label, self.description)


# Authoritative preset data for Blender UI (labels, descriptions, nested dict structure).
# The C++ presets in m_tree/source/leaf/LeafPresets.cpp are independent test fixtures
# and do not need to stay in sync with these values.
LEAF_PRESETS: dict[str, LeafPreset] = {
    "OAK": LeafPreset(
        name="OAK",
        label="Oak",
        description="Lobed oak leaf",
        contour={
            "m": 7.0,
            "a": 1.0,
            "b": 1.0,
            "n1": 2.0,
            "n2": 4.0,
            "n3": 4.0,
            "aspect_ratio": 0.7,
        },
        margin={
            "margin_type": MARGIN_LOBED,
            "tooth_count": 7,
            "tooth_depth": 0.3,
            "tooth_sharpness": 0.5,
        },
        venation={
            "enable_venation": True,
            "venation_type": VENATION_OPEN,
            "vein_density": 800.0,
            "kill_distance": 0.03,
            "attraction_distance": 0.08,
            "growth_step_size": 0.01,
        },
        deformation={
            "vein_displacement": 0.3,
            "midrib_curvature": 0.1,
            "cross_curvature": 0.15,
            "edge_curl": 0.05,
        },
    ),
    "MAPLE": LeafPreset(
        name="MAPLE",
        label="Maple",
        description="Deeply lobed maple leaf",
        contour={
            "m": 5.0,
            "a": 1.0,
            "b": 1.0,
            "n1": 1.5,
            "n2": 3.0,
            "n3": 3.0,
            "aspect_ratio": 0.95,
        },
        margin={
            "margin_type": MARGIN_LOBED,
            "tooth_count": 5,
            "tooth_depth": 0.5,
            "tooth_sharpness": 0.5,
        },
        venation={
            "enable_venation": True,
            "venation_type": VENATION_OPEN,
            "vein_density": 1000.0,
            "kill_distance": 0.025,
            "attraction_distance": 0.08,
            "growth_step_size": 0.01,
        },
        deformation={
            "vein_displacement": 0.3,
            "midrib_curvature": 0.05,
            "cross_curvature": 0.1,
            "edge_curl": 0.0,
        },
    ),
    "BIRCH": LeafPreset(
        name="BIRCH",
        label="Birch",
        description="Serrate birch leaf",
        contour={
            "m": 2.0,
            "a": 1.0,
            "b": 0.6,
            "n1": 2.5,
            "n2": 8.0,
            "n3": 8.0,
            "aspect_ratio": 0.6,
        },
        margin={
            "margin_type": MARGIN_SERRATE,
            "tooth_count": 24,
            "tooth_depth": 0.05,
            "tooth_sharpness": 0.5,
        },
        venation={
            "enable_venation": True,
            "venation_type": VENATION_OPEN,
            "vein_density": 600.0,
            "kill_distance": 0.03,
            "attraction_distance": 0.08,
            "growth_step_size": 0.01,
        },
        deformation={
            "vein_displacement": 0.2,
            "midrib_curvature": 0.15,
            "cross_curvature": 0.1,
            "edge_curl": 0.0,
        },
    ),
    "WILLOW": LeafPreset(
        name="WILLOW",
        label="Willow",
        description="Lanceolate willow leaf",
        contour={
            "m": 2.0,
            "a": 1.0,
            "b": 0.3,
            "n1": 3.0,
            "n2": 10.0,
            "n3": 10.0,
            "aspect_ratio": 0.2,
        },
        margin={
            "margin_type": MARGIN_ENTIRE,
            "tooth_count": 0,
            "tooth_depth": 0.0,
            "tooth_sharpness": 0.5,
        },
        venation={
            "enable_venation": True,
            "venation_type": VENATION_OPEN,
            "vein_density": 400.0,
            "kill_distance": 0.04,
            "attraction_distance": 0.08,
            "growth_step_size": 0.01,
        },
        deformation={
            "vein_displacement": 0.0,
            "midrib_curvature": 0.2,
            "cross_curvature": 0.05,
            "edge_curl": 0.0,
        },
    ),
    "PINE": LeafPreset(
        name="PINE",
        label="Pine",
        description="Pine needle",
        contour={
            "m": 2.0,
            "a": 1.0,
            "b": 0.05,
            "n1": 4.0,
            "n2": 20.0,
            "n3": 20.0,
            "aspect_ratio": 0.05,
        },
        margin={
            "margin_type": MARGIN_ENTIRE,
            "tooth_count": 0,
            "tooth_depth": 0.0,
            "tooth_sharpness": 0.5,
        },
        venation={
            "enable_venation": False,
            "venation_type": VENATION_OPEN,
            "vein_density": 0.0,
            "kill_distance": 0.0,
        },
        deformation={
            "midrib_curvature": 0.0,
            "cross_curvature": 0.0,
            "edge_curl": 0.0,
        },
    ),
}


def get_leaf_preset_items() -> list[tuple[str, str, str]]:
    """Return preset items suitable for Blender EnumProperty."""
    return [preset.to_enum_item() for preset in LEAF_PRESETS.values()]

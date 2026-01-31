"""Python port of C++ crown shape math from CrownShape.hpp."""

from __future__ import annotations

import math
from enum import IntEnum

# Shape envelope constants (matching C++ CrownShapeUtils)
MIN_RATIO = 0.2
RATIO_RANGE = 0.8
TAPER_BASE = 0.5
TAPER_RANGE = 0.5
FLAME_PEAK = 0.7
FLAME_FALLOFF = 0.3


class CrownShape(IntEnum):
    """Crown shape enum matching C++ CrownShape."""

    Conical = 0
    Spherical = 1
    Hemispherical = 2
    Cylindrical = 3
    TaperedCylindrical = 4
    Flame = 5
    InverseConical = 6
    TendFlame = 7


# Map Blender enum names to CrownShape values
BLENDER_SHAPE_MAP = {
    "CYLINDRICAL": CrownShape.Cylindrical,
    "CONICAL": CrownShape.Conical,
    "SPHERICAL": CrownShape.Spherical,
    "HEMISPHERICAL": CrownShape.Hemispherical,
    "TAPERED_CYLINDRICAL": CrownShape.TaperedCylindrical,
    "FLAME": CrownShape.Flame,
    "INVERSE_CONICAL": CrownShape.InverseConical,
    "TEND_FLAME": CrownShape.TendFlame,
}


def get_shape_ratio(shape: CrownShape, ratio: float) -> float:
    """Calculate radius multiplier for a given height ratio.

    Args:
        shape: The crown shape type
        ratio: Height ratio from 0 (bottom) to 1 (top)

    Returns:
        Radius multiplier for branch length at this height
    """
    ratio = max(0.0, min(1.0, ratio))

    if shape == CrownShape.Conical:
        return MIN_RATIO + RATIO_RANGE * ratio
    elif shape == CrownShape.Spherical:
        return MIN_RATIO + RATIO_RANGE * math.sin(math.pi * ratio)
    elif shape == CrownShape.Hemispherical:
        return MIN_RATIO + RATIO_RANGE * math.sin(math.pi / 2 * ratio)
    elif shape == CrownShape.Cylindrical:
        return 1.0
    elif shape == CrownShape.TaperedCylindrical:
        return TAPER_BASE + TAPER_RANGE * ratio
    elif shape == CrownShape.Flame:
        if ratio <= FLAME_PEAK:
            return ratio / FLAME_PEAK
        else:
            return (1.0 - ratio) / FLAME_FALLOFF
    elif shape == CrownShape.InverseConical:
        return 1.0 - RATIO_RANGE * ratio
    elif shape == CrownShape.TendFlame:
        if ratio <= FLAME_PEAK:
            return TAPER_BASE + TAPER_RANGE * ratio / FLAME_PEAK
        else:
            return TAPER_BASE + TAPER_RANGE * (1.0 - ratio) / FLAME_FALLOFF
    else:
        return 1.0


def generate_envelope_geometry(
    shape: CrownShape,
    height: float,
    base_radius: float,
    n_rings: int = 24,
    n_profiles: int = 4,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """Generate vertices and line indices for crown envelope wireframe.

    Args:
        shape: The crown shape type
        height: Total height of the envelope
        base_radius: Maximum radius of the envelope
        n_rings: Number of horizontal rings
        n_profiles: Number of vertical profile lines

    Returns:
        Tuple of (vertices, line_indices) where vertices are (x,y,z) tuples
        and line_indices are (start_idx, end_idx) tuples
    """
    vertices = []
    lines = []

    # Generate ring vertices
    for ring_idx in range(n_rings + 1):
        ratio = ring_idx / n_rings
        z = ratio * height
        radius = base_radius * get_shape_ratio(shape, ratio)

        ring_start_idx = len(vertices)
        for profile_idx in range(n_profiles):
            angle = (profile_idx / n_profiles) * 2 * math.pi
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y, z))

        # Connect ring vertices with horizontal lines
        for i in range(n_profiles):
            next_i = (i + 1) % n_profiles
            lines.append((ring_start_idx + i, ring_start_idx + next_i))

    # Connect vertical profile lines
    verts_per_ring = n_profiles
    for profile_idx in range(n_profiles):
        for ring_idx in range(n_rings):
            current_idx = ring_idx * verts_per_ring + profile_idx
            next_idx = (ring_idx + 1) * verts_per_ring + profile_idx
            lines.append((current_idx, next_idx))

    return vertices, lines

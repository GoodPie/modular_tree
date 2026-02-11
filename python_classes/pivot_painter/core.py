"""Pure computational functions for Pivot Painter export.

This module contains functions extracted from the Unity and Unreal exporters
that perform pure mathematical operations without Blender dependencies.
These functions can be tested independently.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Golden ratio conjugate for stem ID hashing
GOLDEN_RATIO_CONJUGATE = 0.61803398875


def compute_stem_id_hash(stem_ids: NDArray[np.floating]) -> NDArray[np.floating]:
    """Compute golden ratio hash for stem IDs to avoid wrap-around patterns.

    Args:
        stem_ids: Array of stem ID values.

    Returns:
        Array of hash values in [0, 1) range.
    """
    return np.mod(stem_ids * GOLDEN_RATIO_CONJUGATE, 1.0)


def normalize_with_minimum(
    values: NDArray[np.floating],
    min_divisor: float = 1.0,
) -> NDArray[np.floating]:
    """Normalize values to [0, 1] range with a minimum divisor.

    Args:
        values: Array of values to normalize.
        min_divisor: Minimum value to use as divisor (prevents division by zero).

    Returns:
        Normalized array with values in [0, 1] range.
    """
    max_val = max(values.max() if len(values) > 0 else 0.0, min_divisor)
    return values / max_val


def pack_unity_vertex_colors(
    hierarchy_depths: NDArray[np.floating],
    branch_extents: NDArray[np.floating],
    stem_id_hashes: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Pack pivot painter data into RGBA vertex color array for Unity.

    Color channels:
        R: Normalized hierarchy depth
        G: Normalized branch extent
        B: Stem ID fraction (for variation)
        A: Always 1.0

    Args:
        hierarchy_depths: Normalized hierarchy depth values.
        branch_extents: Normalized branch extent values.
        stem_id_hashes: Hashed stem ID values.

    Returns:
        Flat array of RGBA values (length = vertex_count * 4).
    """
    vertex_count = len(hierarchy_depths)
    colors = np.zeros(vertex_count * 4)

    for i in range(vertex_count):
        colors[i * 4] = hierarchy_depths[i]  # R
        colors[i * 4 + 1] = branch_extents[i]  # G
        colors[i * 4 + 2] = stem_id_hashes[i]  # B
        colors[i * 4 + 3] = 1.0  # A

    return colors


def stem_id_to_pixel_coords(stem_id: int, texture_size: int) -> tuple[int, int]:
    """Convert stem ID to texture pixel coordinates.

    Maps stem ID to a unique pixel position in a square texture.

    Args:
        stem_id: The stem ID to convert.
        texture_size: Width/height of the square texture.

    Returns:
        Tuple of (px, py) pixel coordinates.
    """
    px = stem_id % texture_size
    py = stem_id // texture_size
    return (px, py)


def stem_id_to_uv_coords(stem_id: int, texture_size: int) -> tuple[float, float]:
    """Convert stem ID to UV coordinates for texture lookup.

    Maps stem ID to the center of its corresponding pixel in UV space.

    Args:
        stem_id: The stem ID to convert.
        texture_size: Width/height of the square texture.

    Returns:
        Tuple of (u, v) coordinates in [0, 1] range.
    """
    px, py = stem_id_to_pixel_coords(stem_id, texture_size)
    # Add 0.5 to center UV in pixel
    u = (px + 0.5) / texture_size
    v = (py + 0.5) / texture_size
    return (u, v)


def normalize_direction_vector(
    direction: NDArray[np.floating],
    epsilon: float = 1e-6,
    fallback: NDArray[np.floating] | None = None,
) -> NDArray[np.floating]:
    """Normalize a direction vector with zero-vector fallback.

    Args:
        direction: 3D direction vector to normalize.
        epsilon: Threshold below which vector is considered zero.
        fallback: Vector to return if input is zero. Defaults to [0, 0, 1].

    Returns:
        Normalized direction vector (unit length) or fallback if input is zero.
    """
    if fallback is None:
        fallback = np.array([0.0, 0.0, 1.0])

    length = np.linalg.norm(direction)
    if length > epsilon:
        normalized = direction / length
        # Clamp to [-1, 1] as safeguard against floating point errors
        return np.clip(normalized, -1.0, 1.0)
    return fallback.copy()


def create_pivot_index_pixels(
    stem_ids: NDArray[np.floating],
    pivot_positions: NDArray[np.floating],
    hierarchy_depths: NDArray[np.floating],
    texture_size: int,
) -> NDArray[np.floating]:
    """Create pixel data for PivotPos_Index texture.

    Epic's format: RGB = pivot world position, A = hierarchy depth.

    Args:
        stem_ids: Per-vertex stem IDs.
        pivot_positions: Per-vertex pivot positions (Nx3 array).
        hierarchy_depths: Per-vertex hierarchy depths.
        texture_size: Width/height of the square texture.

    Returns:
        Flat array of RGBA pixel values (length = size * size * 4).
    """
    size = texture_size
    pixels = np.zeros(size * size * 4)

    # Map each unique stem_id to a pixel
    unique_stems = np.unique(stem_ids.astype(int))
    for stem_id in unique_stems:
        mask = stem_ids == stem_id
        if not np.any(mask):
            continue

        # Get first vertex data for this stem
        idx = np.where(mask)[0][0]
        pos = pivot_positions[idx]
        depth = hierarchy_depths[idx]

        # Map stem_id to pixel coordinates
        px, py = stem_id_to_pixel_coords(int(stem_id), size)

        if py < size:
            pixel_idx = (py * size + px) * 4
            pixels[pixel_idx] = pos[0]  # R = X position
            pixels[pixel_idx + 1] = pos[1]  # G = Y position
            pixels[pixel_idx + 2] = pos[2]  # B = Z position
            pixels[pixel_idx + 3] = depth  # A = hierarchy depth

    return pixels


def create_xvector_extent_pixels(
    stem_ids: NDArray[np.floating],
    directions: NDArray[np.floating],
    branch_extents: NDArray[np.floating],
    texture_size: int,
) -> NDArray[np.floating]:
    """Create pixel data for XVector_Extent texture.

    Epic's format: RGB = normalized branch direction, A = branch length.

    Args:
        stem_ids: Per-vertex stem IDs.
        directions: Per-vertex direction vectors (Nx3 array).
        branch_extents: Per-vertex branch extents.
        texture_size: Width/height of the square texture.

    Returns:
        Flat array of RGBA pixel values (length = size * size * 4).
    """
    size = texture_size
    pixels = np.zeros(size * size * 4)

    unique_stems = np.unique(stem_ids.astype(int))
    for stem_id in unique_stems:
        mask = stem_ids == stem_id
        if not np.any(mask):
            continue

        idx = np.where(mask)[0][0]
        direction = directions[idx].copy()
        extent = branch_extents[idx]

        # Normalize direction vector
        direction = normalize_direction_vector(direction)

        px, py = stem_id_to_pixel_coords(int(stem_id), size)

        if py < size:
            pixel_idx = (py * size + px) * 4
            pixels[pixel_idx] = direction[0]  # R = X direction
            pixels[pixel_idx + 1] = direction[1]  # G = Y direction
            pixels[pixel_idx + 2] = direction[2]  # B = Z direction
            pixels[pixel_idx + 3] = extent  # A = branch extent

    return pixels


def compute_leaf_attachment_points(
    instance_positions: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Extract leaf attachment points from leaf instance positions.

    The attachment point for each leaf is its instance origin position,
    which corresponds to where the leaf petiole meets the branch.

    Args:
        instance_positions: Nx3 array of leaf instance world positions.

    Returns:
        Nx3 array of attachment point positions.
    """
    return np.array(instance_positions, dtype=np.float64).reshape(-1, 3)


def compute_leaf_facing_directions(
    instance_rotations: NDArray[np.floating],
    local_up: NDArray[np.floating] | None = None,
) -> NDArray[np.floating]:
    """Compute leaf facing directions from instance Euler XYZ rotations.

    Each leaf's facing direction is its local up-axis (Z by default)
    rotated by the instance Euler rotation. This represents the leaf
    surface normal after placement.

    Args:
        instance_rotations: Nx3 array of Euler XYZ rotation angles (radians).
        local_up: Local axis to rotate, defaults to [0, 0, 1] (Z-up).

    Returns:
        Nx3 array of normalized facing direction vectors.
    """
    rotations = np.array(instance_rotations, dtype=np.float64).reshape(-1, 3)
    n = len(rotations)

    if n == 0:
        return np.zeros((0, 3), dtype=np.float64)

    cx = np.cos(rotations[:, 0])
    sx = np.sin(rotations[:, 0])
    cy = np.cos(rotations[:, 1])
    sy = np.sin(rotations[:, 1])
    cz = np.cos(rotations[:, 2])
    sz = np.sin(rotations[:, 2])

    if local_up is not None:
        up = np.asarray(local_up, dtype=np.float64).ravel()
    else:
        up = np.array([0.0, 0.0, 1.0])

    # Build per-instance rotation matrices R = Rz * Ry * Rx (Euler XYZ)
    # and apply to the local up vector
    # R00 = cz*cy, R01 = cz*sy*sx - sz*cx, R02 = cz*sy*cx + sz*sx
    # R10 = sz*cy, R11 = sz*sy*sx + cz*cx, R12 = sz*sy*cx - cz*sx
    # R20 = -sy,   R21 = cy*sx,             R22 = cy*cx
    dx = (cz * cy) * up[0] + (cz * sy * sx - sz * cx) * up[1] + (cz * sy * cx + sz * sx) * up[2]
    dy = (sz * cy) * up[0] + (sz * sy * sx + cz * cx) * up[1] + (sz * sy * cx - cz * sx) * up[2]
    dz = (-sy) * up[0] + (cy * sx) * up[1] + (cy * cx) * up[2]

    directions = np.column_stack([dx, dy, dz])

    # Normalize each direction vector
    lengths = np.linalg.norm(directions, axis=1, keepdims=True)
    lengths = np.maximum(lengths, 1e-6)
    directions = directions / lengths

    return directions


def create_leaf_attachment_pixels(
    leaf_ids: NDArray[np.floating],
    attachment_points: NDArray[np.floating],
    texture_size: int,
) -> NDArray[np.floating]:
    """Create pixel data for LeafAttachment texture.

    Format: RGB = attachment world position, A = 1.0.

    Args:
        leaf_ids: Per-vertex leaf instance IDs.
        attachment_points: Per-vertex attachment positions (Nx3 array).
        texture_size: Width/height of the square texture.

    Returns:
        Flat array of RGBA pixel values (length = size * size * 4).
    """
    size = texture_size
    pixels = np.zeros(size * size * 4)

    unique_leaves = np.unique(leaf_ids.astype(int))
    for leaf_id in unique_leaves:
        mask = leaf_ids == leaf_id
        if not np.any(mask):
            continue

        idx = np.where(mask)[0][0]
        pos = attachment_points[idx]

        px, py = stem_id_to_pixel_coords(int(leaf_id), size)

        if py < size:
            pixel_idx = (py * size + px) * 4
            pixels[pixel_idx] = pos[0]  # R = X position
            pixels[pixel_idx + 1] = pos[1]  # G = Y position
            pixels[pixel_idx + 2] = pos[2]  # B = Z position
            pixels[pixel_idx + 3] = 1.0  # A = 1.0

    return pixels


def create_leaf_facing_pixels(
    leaf_ids: NDArray[np.floating],
    facing_directions: NDArray[np.floating],
    texture_size: int,
) -> NDArray[np.floating]:
    """Create pixel data for LeafFacing texture.

    Format: RGB = normalized facing direction, A = 1.0.

    Args:
        leaf_ids: Per-vertex leaf instance IDs.
        facing_directions: Per-vertex facing direction vectors (Nx3 array).
        texture_size: Width/height of the square texture.

    Returns:
        Flat array of RGBA pixel values (length = size * size * 4).
    """
    size = texture_size
    pixels = np.zeros(size * size * 4)

    unique_leaves = np.unique(leaf_ids.astype(int))
    for leaf_id in unique_leaves:
        mask = leaf_ids == leaf_id
        if not np.any(mask):
            continue

        idx = np.where(mask)[0][0]
        direction = normalize_direction_vector(facing_directions[idx].copy())

        px, py = stem_id_to_pixel_coords(int(leaf_id), size)

        if py < size:
            pixel_idx = (py * size + px) * 4
            pixels[pixel_idx] = direction[0]  # R = X direction
            pixels[pixel_idx + 1] = direction[1]  # G = Y direction
            pixels[pixel_idx + 2] = direction[2]  # B = Z direction
            pixels[pixel_idx + 3] = 1.0  # A = 1.0

    return pixels

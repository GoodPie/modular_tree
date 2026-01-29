"""Unity-specific Pivot Painter export."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import bpy

from ..core import compute_stem_id_hash, normalize_with_minimum, pack_unity_vertex_colors
from ..exporter import ExportResult


class UnityExporter:
    """Exports Pivot Painter data as vertex colors for Unity.

    Unity doesn't use textures for Pivot Painter - instead, the data
    is packed into vertex colors that drive the wind shader directly.
    """

    VERTEX_COLOR_NAME = "PivotPainterMask"

    def __init__(self, mesh: bpy.types.Mesh):
        self.mesh = mesh

    def export(self) -> ExportResult:
        """Create vertex color layer with packed pivot painter data.

        Color channels:
            R: Normalized hierarchy depth
            G: Normalized branch extent
            B: Stem ID fraction (for variation)
            A: Always 1.0
        """
        self._ensure_color_attribute()
        self._write_vertex_colors()

        return ExportResult(
            success=True,
            message="Created vertex color layer for Unity",
        )

    def _ensure_color_attribute(self) -> None:
        """Create the vertex color attribute if it doesn't exist."""
        if self.VERTEX_COLOR_NAME not in self.mesh.color_attributes:
            self.mesh.color_attributes.new(
                name=self.VERTEX_COLOR_NAME,
                type="FLOAT_COLOR",
                domain="POINT",
            )

    def _write_vertex_colors(self) -> None:
        """Pack pivot painter data into vertex colors."""
        color_attr = self.mesh.color_attributes[self.VERTEX_COLOR_NAME]
        vertex_count = len(self.mesh.vertices)

        # Extract attribute data
        stem_ids = np.zeros(vertex_count)
        hierarchy_depths = np.zeros(vertex_count)
        branch_extents = np.zeros(vertex_count)

        self.mesh.attributes["stem_id"].data.foreach_get("value", stem_ids)
        self.mesh.attributes["hierarchy_depth"].data.foreach_get("value", hierarchy_depths)
        self.mesh.attributes["branch_extent"].data.foreach_get("value", branch_extents)

        # Normalize values and compute stem ID hashes
        normalized_depths = normalize_with_minimum(hierarchy_depths)
        normalized_extents = normalize_with_minimum(branch_extents)
        stem_id_hashes = compute_stem_id_hash(stem_ids)

        # Pack into RGBA vertex colors
        colors = pack_unity_vertex_colors(normalized_depths, normalized_extents, stem_id_hashes)

        color_attr.data.foreach_set("color", colors)

"""Unity-specific Pivot Painter export."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import bpy

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

        # Normalize values
        max_depth = max(hierarchy_depths.max(), 1.0)
        max_extent = max(branch_extents.max(), 1.0)

        # Pack into RGBA
        # Use golden ratio hash for stem IDs to avoid wrap-around patterns
        stem_id_hashes = np.mod(stem_ids * 0.61803398875, 1.0)

        colors = np.zeros(vertex_count * 4)
        for i in range(vertex_count):
            colors[i * 4] = hierarchy_depths[i] / max_depth  # R
            colors[i * 4 + 1] = branch_extents[i] / max_extent  # G
            colors[i * 4 + 2] = stem_id_hashes[i]  # B
            colors[i * 4 + 3] = 1.0  # A

        color_attr.data.foreach_set("color", colors)

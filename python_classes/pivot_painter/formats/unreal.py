"""Unreal Engine-specific Pivot Painter 2.0 export.

Generates textures compatible with Epic's PivotPainter2FoliageShader material function.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import bpy

from ..core import (
    create_pivot_index_pixels,
    create_xvector_extent_pixels,
    stem_id_to_uv_coords,
)
from ..exporter import ExportResult


class UnrealExporter:
    """Exports Pivot Painter 2.0 data for Unreal Engine 4/5.

    Generates textures in Epic's expected format:
        - Texture 1 (PivotPos_Index): RGB = pivot position, A = hierarchy depth
        - Texture 2 (XVector_Extent): RGB = branch direction (X-Vector), A = branch extent
        - UV2 layer: Encodes stem ID as texture lookup coordinates

    These textures work directly with UE's PivotPainter2FoliageShader material function.
    """

    def __init__(
        self,
        mesh: bpy.types.Mesh,
        object_name: str,
        texture_size: int,
        export_path: str,
        is_ue5: bool = True,
    ):
        self.mesh = mesh
        self.object_name = object_name
        self.texture_size = texture_size
        self.export_path = export_path
        self.is_ue5 = is_ue5

    def export(self) -> ExportResult:
        """Export textures and UV2 for Unreal Engine."""
        import bpy

        export_dir = bpy.path.abspath(self.export_path)
        os.makedirs(export_dir, exist_ok=True)

        # Extract vertex data
        vertex_data = self._extract_vertex_data()

        # Generate textures in Epic's Pivot Painter 2.0 format
        files_created = []

        # Texture 1: RGB = Pivot Position, A = Hierarchy Depth (parent index proxy)
        pivot_path = os.path.join(export_dir, f"{self.object_name}_PivotPos_Index.exr")
        self._create_pivot_index_texture(vertex_data, pivot_path)
        files_created.append(pivot_path)

        # Texture 2: RGB = X-Vector (direction), A = X-Extent (branch length)
        xvector_path = os.path.join(export_dir, f"{self.object_name}_XVector_Extent.exr")
        self._create_xvector_extent_texture(vertex_data, xvector_path)
        files_created.append(xvector_path)

        # Add UV2 layer for texture lookup
        self._add_pivot_painter_uv(vertex_data["stem_ids"])

        engine = "UE5" if self.is_ue5 else "UE4"
        return ExportResult(
            success=True,
            message=f"Exported Pivot Painter 2.0 textures for {engine}. "
            f"Use with PivotPainter2FoliageShader material function.",
            files_created=files_created,
        )

    def _extract_vertex_data(self) -> dict:
        """Extract all pivot painter attributes from mesh.

        Handles both POINT and CORNER domain attributes correctly.
        """
        num_verts = len(self.mesh.vertices)

        # Initialize arrays for per-vertex data
        stem_ids = np.zeros(num_verts)
        hierarchy_depths = np.zeros(num_verts)
        pivot_positions = np.zeros((num_verts, 3))
        branch_extents = np.zeros(num_verts)
        directions = np.zeros((num_verts, 3))

        # Read each attribute based on its domain
        for attr_name, target, is_vector in [
            ("stem_id", stem_ids, False),
            ("hierarchy_depth", hierarchy_depths, False),
            ("pivot_position", pivot_positions, True),
            ("branch_extent", branch_extents, False),
            ("direction", directions, True),
        ]:
            attr = self.mesh.attributes[attr_name]
            domain = attr.domain

            if domain == "POINT":
                # Per-vertex attribute - direct read
                if is_vector:
                    flat = np.zeros(num_verts * 3)
                    attr.data.foreach_get("vector", flat)
                    target[:] = flat.reshape(-1, 3)
                else:
                    attr.data.foreach_get("value", target)

            elif domain == "CORNER":
                # Per-loop attribute - need to map back to vertices
                num_loops = len(self.mesh.loops)
                if is_vector:
                    flat = np.zeros(num_loops * 3)
                    attr.data.foreach_get("vector", flat)
                    loop_data = flat.reshape(-1, 3)
                else:
                    loop_data = np.zeros(num_loops)
                    attr.data.foreach_get("value", loop_data)

                # Map loop data to vertex data (take first loop's value per vertex)
                loop_to_vert = np.zeros(num_loops, dtype=int)
                self.mesh.loops.foreach_get("vertex_index", loop_to_vert)

                # Track which vertices have been assigned (first occurrence wins)
                has_value = np.zeros(num_verts, dtype=bool)

                for loop_idx, vert_idx in enumerate(loop_to_vert):
                    if not has_value[vert_idx]:
                        target[vert_idx] = loop_data[loop_idx]
                        has_value[vert_idx] = True

        return {
            "stem_ids": stem_ids,
            "hierarchy_depths": hierarchy_depths,
            "pivot_positions": pivot_positions,
            "branch_extents": branch_extents,
            "directions": directions,
        }

    def _create_pivot_index_texture(self, vertex_data: dict, filepath: str) -> None:
        """Create texture with pivot position (RGB) and hierarchy depth (A).

        Epic's format: RGB = pivot world position, A = parent index.
        We use hierarchy_depth as a proxy for parent index since it indicates
        how many steps from the root this branch is.
        """
        pixels = create_pivot_index_pixels(
            stem_ids=vertex_data["stem_ids"],
            pivot_positions=vertex_data["pivot_positions"],
            hierarchy_depths=vertex_data["hierarchy_depths"],
            texture_size=self.texture_size,
        )
        self._save_exr_texture("PivotPos_Index", pixels, filepath)

    def _create_xvector_extent_texture(self, vertex_data: dict, filepath: str) -> None:
        """Create texture with X-Vector (RGB) and branch extent (A).

        Epic's format: RGB = normalized branch direction, A = branch length.
        The X-Vector is used to calculate rotation axis: cross(XVector, WindDir).
        """
        pixels = create_xvector_extent_pixels(
            stem_ids=vertex_data["stem_ids"],
            directions=vertex_data["directions"],
            branch_extents=vertex_data["branch_extents"],
            texture_size=self.texture_size,
        )
        self._save_exr_texture("XVector_Extent", pixels, filepath)

    def _save_exr_texture(self, name: str, pixels: np.ndarray, filepath: str) -> None:
        """Save pixel data as EXR texture.

        EXR format preserves full float precision needed for world-space positions
        and normalized vectors.
        """
        import bpy

        size = self.texture_size

        image = bpy.data.images.new(name, width=size, height=size, alpha=True, float_buffer=True)
        image.pixels = pixels.tolist()
        image.filepath_raw = filepath
        image.file_format = "OPEN_EXR"
        image.save()
        bpy.data.images.remove(image)

    def _add_pivot_painter_uv(self, stem_ids: np.ndarray) -> None:
        """Add UV2 layer with stem_id encoded as UV coordinates.

        Each vertex's UV points to the pixel containing its stem's data.
        This allows the shader to look up pivot position and direction per-vertex.
        """
        if len(self.mesh.uv_layers) < 2:
            self.mesh.uv_layers.new(name="PivotPainterUV")

        uv_layer = (
            self.mesh.uv_layers[1] if len(self.mesh.uv_layers) > 1 else self.mesh.uv_layers[0]
        )

        # Set UV coordinates based on stem_id
        for poly in self.mesh.polygons:
            for loop_idx in poly.loop_indices:
                vert_idx = self.mesh.loops[loop_idx].vertex_index
                stem_id = int(stem_ids[vert_idx])
                uv = stem_id_to_uv_coords(stem_id, self.texture_size)
                uv_layer.data[loop_idx].uv = uv

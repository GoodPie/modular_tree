"""Pivot Painter 2.0 export module for game engine integration.

This module provides export functionality for Pivot Painter 2.0 data,
supporting Unreal Engine 4/5 and Unity.

For UE5, the exporter generates textures compatible with Epic's built-in
PivotPainter2FoliageShader material function. See UE5_MATERIAL_SETUP.md
for detailed setup instructions.

Texture format (Epic's Pivot Painter 2.0 standard):
    - PivotPos_Index.exr: RGB = pivot position, A = hierarchy depth
    - XVector_Extent.exr: RGB = branch direction, A = branch length
"""

from .exporter import PivotPainterExporter, ExportFormat, ExportResult

__all__ = ["PivotPainterExporter", "ExportFormat", "ExportResult"]

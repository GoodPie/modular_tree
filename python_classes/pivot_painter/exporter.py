"""Main Pivot Painter exporter class."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


class ExportFormat(Enum):
    """Supported export formats for Pivot Painter data."""

    UE5 = "UE5"
    UE4 = "UE4"
    UNITY = "UNITY"


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    message: str
    files_created: list[str] | None = None


class PivotPainterExporter:
    """Exports Pivot Painter 2.0 data for game engines.

    This class handles the extraction of pivot painter attributes from
    Blender meshes and exports them in engine-specific formats.
    """

    REQUIRED_ATTRIBUTES = [
        "stem_id",
        "hierarchy_depth",
        "pivot_position",
        "branch_extent",
        "direction",  # X-Vector for Pivot Painter 2.0
    ]

    def __init__(
        self,
        mesh: "bpy.types.Mesh",
        export_format: ExportFormat,
        texture_size: int = 1024,
        export_path: str = "",
    ):
        self.mesh = mesh
        self.export_format = export_format
        self.texture_size = texture_size
        self.export_path = export_path

    def validate(self) -> ExportResult | None:
        """Validate that the mesh has required attributes.

        Returns:
            ExportResult with error if validation fails, None if valid.
        """
        for attr in self.REQUIRED_ATTRIBUTES:
            if attr not in self.mesh.attributes:
                return ExportResult(
                    success=False,
                    message=f"Missing attribute '{attr}'. Generate tree with mesher first.",
                )
        return None

    def export(self, object_name: str) -> ExportResult:
        """Export pivot painter data in the specified format.

        Args:
            object_name: Name of the object (used for file naming).

        Returns:
            ExportResult indicating success or failure.
        """
        validation_error = self.validate()
        if validation_error:
            return validation_error

        if self.export_format == ExportFormat.UNITY:
            return self._export_unity()
        else:
            return self._export_unreal(object_name)

    def _export_unity(self) -> ExportResult:
        """Export vertex colors for Unity wind shader."""
        from .formats.unity import UnityExporter

        exporter = UnityExporter(self.mesh)
        return exporter.export()

    def _export_unreal(self, object_name: str) -> ExportResult:
        """Export textures and UV2 for Unreal Engine."""
        from .formats.unreal import UnrealExporter

        exporter = UnrealExporter(
            mesh=self.mesh,
            object_name=object_name,
            texture_size=self.texture_size,
            export_path=self.export_path,
            is_ue5=(self.export_format == ExportFormat.UE5),
        )
        return exporter.export()

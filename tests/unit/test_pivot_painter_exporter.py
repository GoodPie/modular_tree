"""Tests for pivot painter exporter classes."""

from dataclasses import fields
from unittest.mock import MagicMock, patch

from exporter import ExportFormat, ExportResult, PivotPainterExporter


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_ue5_value(self):
        """UE5 format has correct value."""
        assert ExportFormat.UE5.value == "UE5"

    def test_ue4_value(self):
        """UE4 format has correct value."""
        assert ExportFormat.UE4.value == "UE4"

    def test_unity_value(self):
        """Unity format has correct value."""
        assert ExportFormat.UNITY.value == "UNITY"

    def test_all_formats_exist(self):
        """All expected formats are defined."""
        expected = {"UE5", "UE4", "UNITY"}
        actual = {f.value for f in ExportFormat}
        assert expected == actual


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_create_success_result(self):
        """Can create successful result."""
        result = ExportResult(success=True, message="Export completed")
        assert result.success is True
        assert result.message == "Export completed"
        assert result.files_created is None

    def test_create_failure_result(self):
        """Can create failure result."""
        result = ExportResult(success=False, message="Missing attribute")
        assert result.success is False
        assert result.message == "Missing attribute"

    def test_create_with_files(self):
        """Can create result with files list."""
        files = ["/path/to/texture1.exr", "/path/to/texture2.exr"]
        result = ExportResult(success=True, message="Done", files_created=files)
        assert result.files_created == files

    def test_dataclass_fields(self):
        """ExportResult has expected fields."""
        field_names = {f.name for f in fields(ExportResult)}
        assert field_names == {"success", "message", "files_created"}


class TestPivotPainterExporterValidation:
    """Tests for PivotPainterExporter.validate method."""

    def test_validate_missing_stem_id(self):
        """Validation fails when stem_id is missing."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {}

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is not None
        assert result.success is False
        assert "stem_id" in result.message

    def test_validate_missing_hierarchy_depth(self):
        """Validation fails when hierarchy_depth is missing."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {"stem_id": MagicMock()}

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is not None
        assert result.success is False
        assert "hierarchy_depth" in result.message

    def test_validate_missing_pivot_position(self):
        """Validation fails when pivot_position is missing."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {"stem_id": MagicMock(), "hierarchy_depth": MagicMock()}

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is not None
        assert result.success is False
        assert "pivot_position" in result.message

    def test_validate_missing_branch_extent(self):
        """Validation fails when branch_extent is missing."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {
            "stem_id": MagicMock(),
            "hierarchy_depth": MagicMock(),
            "pivot_position": MagicMock(),
        }

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is not None
        assert result.success is False
        assert "branch_extent" in result.message

    def test_validate_missing_direction(self):
        """Validation fails when direction is missing."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {
            "stem_id": MagicMock(),
            "hierarchy_depth": MagicMock(),
            "pivot_position": MagicMock(),
            "branch_extent": MagicMock(),
        }

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is not None
        assert result.success is False
        assert "direction" in result.message

    def test_validate_all_attributes_present(self):
        """Validation passes when all attributes present."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {
            "stem_id": MagicMock(),
            "hierarchy_depth": MagicMock(),
            "pivot_position": MagicMock(),
            "branch_extent": MagicMock(),
            "direction": MagicMock(),
        }

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.validate()

        assert result is None


class TestPivotPainterExporterExport:
    """Tests for PivotPainterExporter.export method."""

    def _create_valid_mock_mesh(self):
        """Create a mock mesh with all required attributes."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {
            "stem_id": MagicMock(),
            "hierarchy_depth": MagicMock(),
            "pivot_position": MagicMock(),
            "branch_extent": MagicMock(),
            "direction": MagicMock(),
        }
        return mock_mesh

    def test_export_returns_validation_error_if_invalid(self):
        """Export returns error if validation fails."""
        mock_mesh = MagicMock()
        mock_mesh.attributes = {}

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.export("TestObject")

        assert result.success is False
        assert "Missing attribute" in result.message

    @patch("exporter.PivotPainterExporter._export_unity")
    def test_export_routes_to_unity(self, mock_export_unity):
        """Unity format routes to _export_unity."""
        mock_mesh = self._create_valid_mock_mesh()
        mock_export_unity.return_value = ExportResult(success=True, message="Unity OK")

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UNITY)
        result = exporter.export("TestObject")

        mock_export_unity.assert_called_once()
        assert result.message == "Unity OK"

    @patch("exporter.PivotPainterExporter._export_unreal")
    def test_export_routes_to_unreal_for_ue5(self, mock_export_unreal):
        """UE5 format routes to _export_unreal."""
        mock_mesh = self._create_valid_mock_mesh()
        mock_export_unreal.return_value = ExportResult(success=True, message="UE5 OK")

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        result = exporter.export("TestObject")

        mock_export_unreal.assert_called_once_with("TestObject")
        assert result.message == "UE5 OK"

    @patch("exporter.PivotPainterExporter._export_unreal")
    def test_export_routes_to_unreal_for_ue4(self, mock_export_unreal):
        """UE4 format routes to _export_unreal."""
        mock_mesh = self._create_valid_mock_mesh()
        mock_export_unreal.return_value = ExportResult(success=True, message="UE4 OK")

        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE4)
        result = exporter.export("TestObject")

        mock_export_unreal.assert_called_once_with("TestObject")
        assert result.message == "UE4 OK"


class TestPivotPainterExporterInit:
    """Tests for PivotPainterExporter initialization."""

    def test_default_texture_size(self):
        """Default texture size is 1024."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        assert exporter.texture_size == 1024

    def test_custom_texture_size(self):
        """Custom texture size is stored."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5, texture_size=512)
        assert exporter.texture_size == 512

    def test_default_export_path(self):
        """Default export path is empty string."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        assert exporter.export_path == ""

    def test_custom_export_path(self):
        """Custom export path is stored."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5, export_path="/tmp/export")
        assert exporter.export_path == "/tmp/export"

    def test_stores_mesh_reference(self):
        """Mesh reference is stored."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UE5)
        assert exporter.mesh is mock_mesh

    def test_stores_format(self):
        """Export format is stored."""
        mock_mesh = MagicMock()
        exporter = PivotPainterExporter(mock_mesh, ExportFormat.UNITY)
        assert exporter.export_format == ExportFormat.UNITY


class TestRequiredAttributes:
    """Tests for REQUIRED_ATTRIBUTES constant."""

    def test_all_required_attributes_defined(self):
        """All required attributes are in the list."""
        expected = {
            "stem_id",
            "hierarchy_depth",
            "pivot_position",
            "branch_extent",
            "direction",
        }
        assert set(PivotPainterExporter.REQUIRED_ATTRIBUTES) == expected

    def test_required_attributes_is_list(self):
        """REQUIRED_ATTRIBUTES is a list (ordered)."""
        assert isinstance(PivotPainterExporter.REQUIRED_ATTRIBUTES, list)

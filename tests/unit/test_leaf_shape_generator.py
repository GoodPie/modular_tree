"""Integration tests for LeafShapeGenerator via pybind11 bindings.

Tests the C++ LeafShapeGenerator through Python, verifying mesh data,
preset application, parameter edge cases, and LOD generation.
"""

import numpy as np
import pytest

# Import directly from module (path setup in conftest.py)
from m_tree_wrapper import get_m_tree

# Check if m_tree native module is available
try:
    from m_tree import m_tree  # noqa: F401

    HAS_NATIVE_MODULE = True
except ImportError:
    HAS_NATIVE_MODULE = False

requires_native = pytest.mark.skipif(
    not HAS_NATIVE_MODULE,
    reason="m_tree native module not installed (build with ./build_mtree.osx)",
)


@requires_native
class TestLeafShapeGeneratorBasic:
    """Basic generation tests."""

    def test_default_generate_returns_mesh(self):
        """Default parameters produce a valid mesh."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        polys = np.array(mesh.get_polygons())

        assert len(verts) > 3 * 3, "Mesh should have more than 3 vertices"
        assert len(polys) > 0, "Mesh should have polygons"

    def test_vertices_are_finite(self):
        """All vertex coordinates must be finite (no NaN or inf)."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        assert np.all(np.isfinite(verts)), "All vertex coordinates must be finite"

    def test_uvs_in_zero_one_range(self):
        """UV coordinates must be in [0, 1] range."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        mesh = gen.generate()

        uvs = np.array(mesh.get_uvs())
        assert len(uvs) > 0, "Mesh should have UV coordinates"
        assert np.all(uvs >= 0.0), "UVs must be >= 0"
        assert np.all(uvs <= 1.0), "UVs must be <= 1"

    def test_polygons_reference_valid_vertices(self):
        """All polygon vertex indices must reference valid vertices."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        polys = np.array(mesh.get_polygons())
        num_verts = len(verts) // 3

        assert np.all(polys >= 0), "Polygon indices must be non-negative"
        assert np.all(polys < num_verts), "Polygon indices must reference valid vertices"

    def test_deterministic_generation(self):
        """Same seed produces identical meshes."""
        mt = get_m_tree()
        gen1 = mt.LeafShapeGenerator()
        gen1.seed = 42
        mesh1 = gen1.generate()

        gen2 = mt.LeafShapeGenerator()
        gen2.seed = 42
        mesh2 = gen2.generate()

        verts1 = np.array(mesh1.get_vertices())
        verts2 = np.array(mesh2.get_vertices())

        np.testing.assert_array_equal(verts1, verts2)


@requires_native
class TestLeafShapeGeneratorParameters:
    """Test parameter modification effects."""

    def test_aspect_ratio_affects_shape(self):
        """Changing aspect ratio produces different mesh dimensions."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()

        gen.aspect_ratio = 0.2
        mesh_narrow = gen.generate()
        verts_narrow = np.array(mesh_narrow.get_vertices()).reshape(-1, 3)

        gen.aspect_ratio = 1.0
        mesh_wide = gen.generate()
        verts_wide = np.array(mesh_wide.get_vertices()).reshape(-1, 3)

        # Narrow leaf should have smaller X extent relative to Y
        narrow_x_range = verts_narrow[:, 0].max() - verts_narrow[:, 0].min()
        wide_x_range = verts_wide[:, 0].max() - verts_wide[:, 0].min()

        assert narrow_x_range < wide_x_range, "Narrow aspect should produce smaller X range"

    def test_margin_type_modifies_contour(self):
        """Non-ENTIRE margin types produce different vertex counts/positions."""
        mt = get_m_tree()

        gen_entire = mt.LeafShapeGenerator()
        gen_entire.margin_type = mt.MarginType.Entire
        mesh_entire = gen_entire.generate()

        gen_serrate = mt.LeafShapeGenerator()
        gen_serrate.margin_type = mt.MarginType.Serrate
        gen_serrate.tooth_count = 12
        gen_serrate.tooth_depth = 0.2
        mesh_serrate = gen_serrate.generate()

        verts_entire = np.array(mesh_entire.get_vertices())
        verts_serrate = np.array(mesh_serrate.get_vertices())

        # Serrate margin should produce different geometry
        assert not np.array_equal(
            verts_entire, verts_serrate
        ), "Serrate margin should differ from Entire"

    def test_all_margin_types_generate(self):
        """All margin types produce valid meshes."""
        mt = get_m_tree()
        margin_types = [
            mt.MarginType.Entire,
            mt.MarginType.Serrate,
            mt.MarginType.Dentate,
            mt.MarginType.Crenate,
            mt.MarginType.Lobed,
        ]

        for margin in margin_types:
            gen = mt.LeafShapeGenerator()
            gen.margin_type = margin
            gen.tooth_count = 8
            gen.tooth_depth = 0.15
            mesh = gen.generate()

            verts = np.array(mesh.get_vertices())
            assert len(verts) > 3 * 3, f"MarginType {margin} should produce valid mesh"

    def test_superformula_m_affects_symmetry(self):
        """Changing m parameter changes the number of lobes."""
        mt = get_m_tree()

        gen_m2 = mt.LeafShapeGenerator()
        gen_m2.m = 2.0
        mesh_m2 = gen_m2.generate()

        gen_m7 = mt.LeafShapeGenerator()
        gen_m7.m = 7.0
        mesh_m7 = gen_m7.generate()

        verts_m2 = np.array(mesh_m2.get_vertices())
        verts_m7 = np.array(mesh_m7.get_vertices())

        # Different m values should produce different geometry
        # m=7 typically produces more complex shapes that need more vertices
        assert not np.array_equal(verts_m2, verts_m7)

    def test_contour_resolution_minimum(self):
        """Contour resolution is clamped to minimum of 8."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.contour_resolution = 2  # Below minimum
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        # Should still produce a valid mesh (clamped to 8)
        assert len(verts) >= 8 * 3, "Should have at least 8 vertices after clamping"


@requires_native
class TestLeafShapeGeneratorEdgeCases:
    """Test parameter edge cases and clamping."""

    def test_n1_zero_clamped(self):
        """n1=0 should be clamped and not crash."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.n1 = 0.0
        # Should not raise an exception - clamping prevents division by zero.
        # Note: n1=0 clamps to 0.001 which produces pow(x, -1000), so extreme
        # values are expected. The important thing is no crash/segfault.
        mesh = gen.generate()
        verts = np.array(mesh.get_vertices())
        assert len(verts) > 0, "n1=0 should still produce vertices after clamping"

    def test_negative_n1_clamped(self):
        """Negative n1 near zero should be clamped safely."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.n1 = -0.0001
        mesh = gen.generate()
        verts = np.array(mesh.get_vertices())
        assert np.all(np.isfinite(verts)), "Small negative n1 should be clamped"

    def test_extreme_parameters(self):
        """Extreme parameter values produce valid (finite) meshes."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.m = 20.0
        gen.n1 = 50.0
        gen.n2 = 50.0
        gen.n3 = 50.0
        gen.aspect_ratio = 0.01
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        assert np.all(np.isfinite(verts)), "Extreme parameters should still produce finite vertices"

    def test_very_high_tooth_count(self):
        """High tooth count produces valid mesh without crash."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.margin_type = mt.MarginType.Serrate
        gen.tooth_count = 50
        gen.tooth_depth = 0.1
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices())
        assert len(verts) > 0, "High tooth count should still produce valid mesh"


@requires_native
class TestLeafShapeGeneratorVenation:
    """Test venation integration via pybind11."""

    def test_venation_disabled_no_attribute(self):
        """With venation disabled, vein_distance attribute should not exist."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.enable_venation = False
        mesh = gen.generate()

        assert not mesh.has_float_attribute(
            "vein_distance"
        ), "vein_distance should not exist when venation is disabled"

    def test_venation_enabled_has_attribute(self):
        """With venation enabled, vein_distance attribute should exist."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.enable_venation = True
        gen.venation_type = mt.VenationType.Open
        gen.vein_density = 500.0
        mesh = gen.generate()

        assert mesh.has_float_attribute(
            "vein_distance"
        ), "vein_distance should exist when venation is enabled"

    def test_venation_distances_non_negative(self):
        """Vein distance values should be non-negative."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.enable_venation = True
        gen.venation_type = mt.VenationType.Open
        gen.vein_density = 500.0
        mesh = gen.generate()

        distances = np.array(mesh.get_float_attribute("vein_distance"))
        assert np.all(distances >= 0.0), "Vein distances must be non-negative"

    def test_venation_closed_type(self):
        """CLOSED venation type produces valid mesh with vein_distance."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.enable_venation = True
        gen.venation_type = mt.VenationType.Closed
        gen.vein_density = 500.0
        mesh = gen.generate()

        assert mesh.has_float_attribute("vein_distance")
        distances = np.array(mesh.get_float_attribute("vein_distance"))
        assert np.all(np.isfinite(distances))

    def test_vein_displacement_produces_visible_offset(self):
        """Vein displacement with correct params produces visible Z offset (>0.05 units)."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.enable_venation = True
        gen.venation_type = mt.VenationType.Open
        gen.vein_density = 800.0
        gen.kill_distance = 0.03
        gen.attraction_distance = 0.08
        gen.growth_step_size = 0.01
        gen.vein_displacement = 0.3
        # Zero out other deformations to isolate vein effect
        gen.midrib_curvature = 0.0
        gen.cross_curvature = 0.0
        gen.edge_curl = 0.0
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices()).reshape(-1, 3)
        z_range = verts[:, 2].max() - verts[:, 2].min()
        assert (
            z_range > 0.05
        ), f"Vein displacement should produce visible Z offset (>0.05), got {z_range}"


@requires_native
class TestLeafShapeGeneratorSurfaceDeformation:
    """Test surface deformation parameters."""

    def test_midrib_curvature_modifies_z(self):
        """Non-zero midrib curvature should produce non-zero Z coordinates."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.midrib_curvature = 0.5
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices()).reshape(-1, 3)
        z_range = verts[:, 2].max() - verts[:, 2].min()
        assert z_range > 0.0, "Midrib curvature should produce Z displacement"

    def test_cross_curvature_modifies_z(self):
        """Non-zero cross curvature should produce non-zero Z coordinates."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.cross_curvature = 0.5
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices()).reshape(-1, 3)
        z_range = verts[:, 2].max() - verts[:, 2].min()
        assert z_range > 0.0, "Cross curvature should produce Z displacement"

    def test_flat_leaf_with_zero_deformation(self):
        """Zero deformation parameters should produce a flat leaf (Z ≈ 0)."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        gen.midrib_curvature = 0.0
        gen.cross_curvature = 0.0
        gen.edge_curl = 0.0
        gen.vein_displacement = 0.0
        mesh = gen.generate()

        verts = np.array(mesh.get_vertices()).reshape(-1, 3)
        assert np.allclose(verts[:, 2], 0.0, atol=1e-6), "Zero deformation should produce flat leaf"


@requires_native
class TestLeafPresetApplication:
    """Test applying C++ presets to the generator."""

    def test_all_preset_names_exist(self):
        """All 5 species presets are accessible."""
        mt = get_m_tree()
        names = mt.get_leaf_preset_names()
        assert len(names) == 5
        expected = {"Oak", "Maple", "Birch", "Willow", "Pine"}
        assert set(names) == expected

    def test_get_preset_returns_valid_data(self):
        """Each preset returns a LeafPreset with valid parameters."""
        mt = get_m_tree()
        for name in mt.get_leaf_preset_names():
            preset = mt.get_leaf_preset(name)
            assert preset is not None, f"Preset '{name}' should exist"
            assert preset.name == name
            assert preset.m > 0
            assert preset.n1 != 0

    def test_apply_preset_to_generator(self):
        """Preset values can be applied to a LeafShapeGenerator."""
        mt = get_m_tree()
        preset = mt.get_leaf_preset("Oak")
        gen = mt.LeafShapeGenerator()

        gen.m = preset.m
        gen.a = preset.a
        gen.b = preset.b
        gen.n1 = preset.n1
        gen.n2 = preset.n2
        gen.n3 = preset.n3
        gen.aspect_ratio = preset.aspect_ratio
        gen.margin_type = preset.margin_type
        gen.tooth_count = preset.tooth_count
        gen.tooth_depth = preset.tooth_depth

        mesh = gen.generate()
        verts = np.array(mesh.get_vertices())
        assert len(verts) > 0, "Oak preset should generate valid mesh"

    def test_presets_produce_distinct_meshes(self):
        """Different presets produce measurably different meshes."""
        mt = get_m_tree()
        meshes = {}

        for name in mt.get_leaf_preset_names():
            preset = mt.get_leaf_preset(name)
            gen = mt.LeafShapeGenerator()
            gen.m = preset.m
            gen.a = preset.a
            gen.b = preset.b
            gen.n1 = preset.n1
            gen.n2 = preset.n2
            gen.n3 = preset.n3
            gen.aspect_ratio = preset.aspect_ratio
            gen.margin_type = preset.margin_type
            gen.tooth_count = preset.tooth_count
            gen.tooth_depth = preset.tooth_depth
            gen.tooth_sharpness = preset.tooth_sharpness

            mesh = gen.generate()
            verts = np.array(mesh.get_vertices()).reshape(-1, 3)
            # Use bounding box dimensions as a distinguishing metric
            x_range = verts[:, 0].max() - verts[:, 0].min()
            y_range = verts[:, 1].max() - verts[:, 1].min()
            meshes[name] = (x_range, y_range, len(verts))

        # At least Oak and Pine should be very different
        oak_x, oak_y, _ = meshes["Oak"]
        pine_x, pine_y, _ = meshes["Pine"]
        assert (
            abs(oak_x - pine_x) > 0.01 or abs(oak_y - pine_y) > 0.01
        ), "Oak and Pine should produce visually distinct shapes"

    def test_invalid_preset_name_returns_none(self):
        """get_leaf_preset with invalid name returns None."""
        mt = get_m_tree()
        preset = mt.get_leaf_preset("NonExistent")
        assert preset is None


@requires_native
class TestLeafLODGenerator:
    """Test LeafLODGenerator through pybind11."""

    def test_generate_card_from_leaf(self):
        """generate_card produces a 4-vertex quad from a leaf mesh."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        leaf_mesh = gen.generate()

        lod = mt.LeafLODGenerator()
        card = lod.generate_card(leaf_mesh)

        verts = np.array(card.get_vertices())
        polys = np.array(card.get_polygons())
        assert len(verts) == 4 * 3, "Card should have exactly 4 vertices"
        assert len(polys) == 2 * 4, "Card should have 2 triangles (as degenerate quads)"

    def test_card_uvs_cover_full_range(self):
        """Card mesh UVs should span 0-1 in both U and V."""
        mt = get_m_tree()
        gen = mt.LeafShapeGenerator()
        leaf_mesh = gen.generate()

        lod = mt.LeafLODGenerator()
        card = lod.generate_card(leaf_mesh)

        uvs = np.array(card.get_uvs()).reshape(-1, 2)
        assert uvs[:, 0].min() == pytest.approx(0.0)
        assert uvs[:, 0].max() == pytest.approx(1.0)
        assert uvs[:, 1].min() == pytest.approx(0.0)
        assert uvs[:, 1].max() == pytest.approx(1.0)

    def test_billboard_cloud_binding_exists(self):
        """generate_billboard_cloud method exists on LeafLODGenerator."""
        mt = get_m_tree()
        lod = mt.LeafLODGenerator()
        # Verify the method is accessible (Eigen::Vector3f arguments require
        # registered type conversion which is not exposed; test method existence)
        assert hasattr(lod, "generate_billboard_cloud")

    def test_impostor_view_directions_binding_exists(self):
        """get_impostor_view_directions method exists on LeafLODGenerator."""
        mt = get_m_tree()
        lod = mt.LeafLODGenerator()
        # Eigen::Vector3f return type requires opaque type registration;
        # these methods are verified via C++ unit tests instead
        assert hasattr(lod, "get_impostor_view_directions")

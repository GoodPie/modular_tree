"""Unit tests for crown shape formulas (shape_formulas.py)."""

import math

import pytest
from shape_formulas import (
    BLENDER_SHAPE_MAP,
    FLAME_FALLOFF,
    FLAME_PEAK,
    MIN_RATIO,
    RATIO_RANGE,
    TAPER_BASE,
    TAPER_RANGE,
    CrownShape,
    generate_envelope_geometry,
    get_shape_ratio,
)


class TestGetShapeRatioConical:
    """Tests for Conical shape (0.2 + 0.8 * ratio)."""

    def test_at_zero(self):
        """Conical at ratio=0 should return MIN_RATIO (0.2)."""
        result = get_shape_ratio(CrownShape.Conical, 0.0)
        assert result == pytest.approx(MIN_RATIO)

    def test_at_half(self):
        """Conical at ratio=0.5 should return 0.6."""
        result = get_shape_ratio(CrownShape.Conical, 0.5)
        assert result == pytest.approx(0.6)

    def test_at_one(self):
        """Conical at ratio=1 should return 1.0."""
        result = get_shape_ratio(CrownShape.Conical, 1.0)
        assert result == pytest.approx(1.0)


class TestGetShapeRatioSpherical:
    """Tests for Spherical shape (0.2 + 0.8 * sin(π * ratio))."""

    def test_at_zero(self):
        """Spherical at ratio=0 should return MIN_RATIO (0.2)."""
        result = get_shape_ratio(CrownShape.Spherical, 0.0)
        assert result == pytest.approx(MIN_RATIO)

    def test_at_half(self):
        """Spherical at ratio=0.5 should return 1.0 (peak of sine)."""
        result = get_shape_ratio(CrownShape.Spherical, 0.5)
        assert result == pytest.approx(1.0)

    def test_at_one(self):
        """Spherical at ratio=1 should return MIN_RATIO (0.2)."""
        result = get_shape_ratio(CrownShape.Spherical, 1.0)
        assert result == pytest.approx(MIN_RATIO)


class TestGetShapeRatioHemispherical:
    """Tests for Hemispherical shape (0.2 + 0.8 * sin(π/2 * ratio))."""

    def test_at_zero(self):
        """Hemispherical at ratio=0 should return MIN_RATIO (0.2)."""
        result = get_shape_ratio(CrownShape.Hemispherical, 0.0)
        assert result == pytest.approx(MIN_RATIO)

    def test_at_half(self):
        """Hemispherical at ratio=0.5 should return ~0.766."""
        expected = MIN_RATIO + RATIO_RANGE * math.sin(math.pi / 2 * 0.5)
        result = get_shape_ratio(CrownShape.Hemispherical, 0.5)
        assert result == pytest.approx(expected)

    def test_at_one(self):
        """Hemispherical at ratio=1 should return 1.0."""
        result = get_shape_ratio(CrownShape.Hemispherical, 1.0)
        assert result == pytest.approx(1.0)


class TestGetShapeRatioCylindrical:
    """Tests for Cylindrical shape (constant 1.0)."""

    def test_at_zero(self):
        """Cylindrical at ratio=0 should return 1.0."""
        result = get_shape_ratio(CrownShape.Cylindrical, 0.0)
        assert result == pytest.approx(1.0)

    def test_at_half(self):
        """Cylindrical at ratio=0.5 should return 1.0."""
        result = get_shape_ratio(CrownShape.Cylindrical, 0.5)
        assert result == pytest.approx(1.0)

    def test_at_one(self):
        """Cylindrical at ratio=1 should return 1.0."""
        result = get_shape_ratio(CrownShape.Cylindrical, 1.0)
        assert result == pytest.approx(1.0)


class TestGetShapeRatioTaperedCylindrical:
    """Tests for TaperedCylindrical shape (0.5 + 0.5 * ratio)."""

    def test_at_zero(self):
        """TaperedCylindrical at ratio=0 should return TAPER_BASE (0.5)."""
        result = get_shape_ratio(CrownShape.TaperedCylindrical, 0.0)
        assert result == pytest.approx(TAPER_BASE)

    def test_at_half(self):
        """TaperedCylindrical at ratio=0.5 should return 0.75."""
        result = get_shape_ratio(CrownShape.TaperedCylindrical, 0.5)
        assert result == pytest.approx(0.75)

    def test_at_one(self):
        """TaperedCylindrical at ratio=1 should return 1.0."""
        result = get_shape_ratio(CrownShape.TaperedCylindrical, 1.0)
        assert result == pytest.approx(1.0)


class TestGetShapeRatioFlame:
    """Tests for Flame shape (piecewise at FLAME_PEAK=0.7)."""

    def test_at_zero(self):
        """Flame at ratio=0 should return 0.0."""
        result = get_shape_ratio(CrownShape.Flame, 0.0)
        assert result == pytest.approx(0.0)

    def test_at_half(self):
        """Flame at ratio=0.5 should return 0.5/0.7 ≈ 0.714."""
        expected = 0.5 / FLAME_PEAK
        result = get_shape_ratio(CrownShape.Flame, 0.5)
        assert result == pytest.approx(expected)

    def test_at_peak(self):
        """Flame at ratio=0.7 (peak) should return 1.0."""
        result = get_shape_ratio(CrownShape.Flame, FLAME_PEAK)
        assert result == pytest.approx(1.0)

    def test_at_one(self):
        """Flame at ratio=1 should return 0.0."""
        result = get_shape_ratio(CrownShape.Flame, 1.0)
        assert result == pytest.approx(0.0)

    def test_after_peak(self):
        """Flame at ratio=0.85 should be in falloff region."""
        expected = (1.0 - 0.85) / FLAME_FALLOFF
        result = get_shape_ratio(CrownShape.Flame, 0.85)
        assert result == pytest.approx(expected)


class TestGetShapeRatioInverseConical:
    """Tests for InverseConical shape (1.0 - 0.8 * ratio)."""

    def test_at_zero(self):
        """InverseConical at ratio=0 should return 1.0."""
        result = get_shape_ratio(CrownShape.InverseConical, 0.0)
        assert result == pytest.approx(1.0)

    def test_at_half(self):
        """InverseConical at ratio=0.5 should return 0.6."""
        result = get_shape_ratio(CrownShape.InverseConical, 0.5)
        assert result == pytest.approx(0.6)

    def test_at_one(self):
        """InverseConical at ratio=1 should return MIN_RATIO (0.2)."""
        result = get_shape_ratio(CrownShape.InverseConical, 1.0)
        assert result == pytest.approx(MIN_RATIO)


class TestGetShapeRatioTendFlame:
    """Tests for TendFlame shape (piecewise at FLAME_PEAK=0.7, with TAPER_BASE offset)."""

    def test_at_zero(self):
        """TendFlame at ratio=0 should return TAPER_BASE (0.5)."""
        result = get_shape_ratio(CrownShape.TendFlame, 0.0)
        assert result == pytest.approx(TAPER_BASE)

    def test_at_half(self):
        """TendFlame at ratio=0.5 should return ~0.857."""
        expected = TAPER_BASE + TAPER_RANGE * 0.5 / FLAME_PEAK
        result = get_shape_ratio(CrownShape.TendFlame, 0.5)
        assert result == pytest.approx(expected)

    def test_at_peak(self):
        """TendFlame at ratio=0.7 (peak) should return 1.0."""
        result = get_shape_ratio(CrownShape.TendFlame, FLAME_PEAK)
        assert result == pytest.approx(1.0)

    def test_at_one(self):
        """TendFlame at ratio=1 should return TAPER_BASE (0.5)."""
        result = get_shape_ratio(CrownShape.TendFlame, 1.0)
        assert result == pytest.approx(TAPER_BASE)

    def test_after_peak(self):
        """TendFlame at ratio=0.85 should be in falloff region."""
        expected = TAPER_BASE + TAPER_RANGE * (1.0 - 0.85) / FLAME_FALLOFF
        result = get_shape_ratio(CrownShape.TendFlame, 0.85)
        assert result == pytest.approx(expected)


class TestShapeRatioEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_ratio_below_zero_clamps(self):
        """Ratio < 0 should be clamped to 0."""
        result = get_shape_ratio(CrownShape.Conical, -0.5)
        expected = get_shape_ratio(CrownShape.Conical, 0.0)
        assert result == pytest.approx(expected)

    def test_ratio_above_one_clamps(self):
        """Ratio > 1 should be clamped to 1."""
        result = get_shape_ratio(CrownShape.Conical, 1.5)
        expected = get_shape_ratio(CrownShape.Conical, 1.0)
        assert result == pytest.approx(expected)

    def test_flame_exactly_at_boundary(self):
        """Flame at exactly FLAME_PEAK (0.7) uses the <= branch."""
        result = get_shape_ratio(CrownShape.Flame, FLAME_PEAK)
        # ratio / FLAME_PEAK = 0.7 / 0.7 = 1.0
        assert result == pytest.approx(1.0)

    def test_tendflame_exactly_at_boundary(self):
        """TendFlame at exactly FLAME_PEAK (0.7) uses the <= branch."""
        result = get_shape_ratio(CrownShape.TendFlame, FLAME_PEAK)
        # TAPER_BASE + TAPER_RANGE * ratio / FLAME_PEAK = 0.5 + 0.5 * 1.0 = 1.0
        assert result == pytest.approx(1.0)

    def test_flame_just_after_boundary(self):
        """Flame just after FLAME_PEAK uses the falloff formula."""
        ratio = FLAME_PEAK + 0.001
        result = get_shape_ratio(CrownShape.Flame, ratio)
        expected = (1.0 - ratio) / FLAME_FALLOFF
        assert result == pytest.approx(expected)

    def test_tendflame_just_after_boundary(self):
        """TendFlame just after FLAME_PEAK uses the falloff formula."""
        ratio = FLAME_PEAK + 0.001
        result = get_shape_ratio(CrownShape.TendFlame, ratio)
        expected = TAPER_BASE + TAPER_RANGE * (1.0 - ratio) / FLAME_FALLOFF
        assert result == pytest.approx(expected)


class TestGenerateEnvelopeGeometry:
    """Test envelope geometry generation."""

    def test_returns_tuple_of_lists(self):
        """Should return tuple of (vertices, lines)."""
        result = generate_envelope_geometry(CrownShape.Cylindrical, 10.0, 5.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        vertices, lines = result
        assert isinstance(vertices, list)
        assert isinstance(lines, list)

    def test_vertices_are_3_tuples(self):
        """Each vertex should be a 3-tuple (x, y, z)."""
        vertices, _ = generate_envelope_geometry(CrownShape.Cylindrical, 10.0, 5.0)
        for v in vertices:
            assert isinstance(v, tuple)
            assert len(v) == 3
            assert all(isinstance(coord, float) for coord in v)

    def test_lines_are_2_tuples(self):
        """Each line should be a 2-tuple of indices."""
        _, lines = generate_envelope_geometry(CrownShape.Cylindrical, 10.0, 5.0)
        for line in lines:
            assert isinstance(line, tuple)
            assert len(line) == 2

    def test_line_indices_in_bounds(self):
        """Line indices should be within bounds of vertices list."""
        vertices, lines = generate_envelope_geometry(CrownShape.Cylindrical, 10.0, 5.0)
        num_verts = len(vertices)
        for start_idx, end_idx in lines:
            assert 0 <= start_idx < num_verts
            assert 0 <= end_idx < num_verts

    def test_vertex_count(self):
        """Should have (n_rings + 1) * n_profiles vertices."""
        n_rings = 12
        n_profiles = 6
        vertices, _ = generate_envelope_geometry(
            CrownShape.Cylindrical, 10.0, 5.0, n_rings=n_rings, n_profiles=n_profiles
        )
        expected_count = (n_rings + 1) * n_profiles
        assert len(vertices) == expected_count

    def test_cylindrical_constant_radius(self):
        """Cylindrical shape should have constant radius at all heights."""
        base_radius = 5.0
        n_rings = 10
        n_profiles = 4
        vertices, _ = generate_envelope_geometry(
            CrownShape.Cylindrical,
            height=10.0,
            base_radius=base_radius,
            n_rings=n_rings,
            n_profiles=n_profiles,
        )
        # Check radius of first vertex in each ring
        for ring_idx in range(n_rings + 1):
            v_idx = ring_idx * n_profiles
            x, y, _ = vertices[v_idx]
            radius = math.sqrt(x * x + y * y)
            assert radius == pytest.approx(base_radius)

    def test_conical_increasing_radius(self):
        """Conical shape should have increasing radius with height."""
        base_radius = 5.0
        n_rings = 10
        n_profiles = 4
        vertices, _ = generate_envelope_geometry(
            CrownShape.Conical,
            height=10.0,
            base_radius=base_radius,
            n_rings=n_rings,
            n_profiles=n_profiles,
        )
        # Get radii at first and last ring
        first_ring_v = vertices[0]
        last_ring_v = vertices[(n_rings) * n_profiles]
        first_radius = math.sqrt(first_ring_v[0] ** 2 + first_ring_v[1] ** 2)
        last_radius = math.sqrt(last_ring_v[0] ** 2 + last_ring_v[1] ** 2)
        # Conical: radius at bottom (ratio=0) is MIN_RATIO * base_radius
        # Conical: radius at top (ratio=1) is 1.0 * base_radius
        assert first_radius < last_radius
        assert first_radius == pytest.approx(MIN_RATIO * base_radius)
        assert last_radius == pytest.approx(base_radius)

    def test_height_z_values(self):
        """Vertices should span from z=0 to z=height."""
        height = 15.0
        n_rings = 10
        n_profiles = 4
        vertices, _ = generate_envelope_geometry(
            CrownShape.Cylindrical,
            height=height,
            base_radius=5.0,
            n_rings=n_rings,
            n_profiles=n_profiles,
        )
        # First ring at z=0
        assert vertices[0][2] == pytest.approx(0.0)
        # Last ring at z=height
        last_ring_start = n_rings * n_profiles
        assert vertices[last_ring_start][2] == pytest.approx(height)


class TestBlenderShapeMap:
    """Test Blender enum mapping."""

    def test_all_shapes_mapped(self):
        """All CrownShape enum values should be in the map."""
        mapped_shapes = set(BLENDER_SHAPE_MAP.values())
        all_shapes = set(CrownShape)
        assert mapped_shapes == all_shapes

    def test_map_has_eight_entries(self):
        """Should have exactly 8 entries (one per shape)."""
        assert len(BLENDER_SHAPE_MAP) == 8

    def test_cylindrical_mapping(self):
        """CYLINDRICAL should map to CrownShape.Cylindrical."""
        assert BLENDER_SHAPE_MAP["CYLINDRICAL"] == CrownShape.Cylindrical

    def test_conical_mapping(self):
        """CONICAL should map to CrownShape.Conical."""
        assert BLENDER_SHAPE_MAP["CONICAL"] == CrownShape.Conical

    def test_spherical_mapping(self):
        """SPHERICAL should map to CrownShape.Spherical."""
        assert BLENDER_SHAPE_MAP["SPHERICAL"] == CrownShape.Spherical

    def test_hemispherical_mapping(self):
        """HEMISPHERICAL should map to CrownShape.Hemispherical."""
        assert BLENDER_SHAPE_MAP["HEMISPHERICAL"] == CrownShape.Hemispherical

    def test_tapered_cylindrical_mapping(self):
        """TAPERED_CYLINDRICAL should map to CrownShape.TaperedCylindrical."""
        assert BLENDER_SHAPE_MAP["TAPERED_CYLINDRICAL"] == CrownShape.TaperedCylindrical

    def test_flame_mapping(self):
        """FLAME should map to CrownShape.Flame."""
        assert BLENDER_SHAPE_MAP["FLAME"] == CrownShape.Flame

    def test_inverse_conical_mapping(self):
        """INVERSE_CONICAL should map to CrownShape.InverseConical."""
        assert BLENDER_SHAPE_MAP["INVERSE_CONICAL"] == CrownShape.InverseConical

    def test_tend_flame_mapping(self):
        """TEND_FLAME should map to CrownShape.TendFlame."""
        assert BLENDER_SHAPE_MAP["TEND_FLAME"] == CrownShape.TendFlame

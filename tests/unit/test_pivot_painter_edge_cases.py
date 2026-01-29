"""Edge case tests for pivot painter core functions."""

import numpy as np
import pytest
from core import (
    compute_stem_id_hash,
    create_pivot_index_pixels,
    create_xvector_extent_pixels,
    normalize_direction_vector,
    normalize_with_minimum,
    pack_unity_vertex_colors,
    stem_id_to_pixel_coords,
    stem_id_to_uv_coords,
)


class TestEmptyDataArrays:
    """Tests for handling empty input arrays."""

    def test_compute_stem_id_hash_empty(self):
        """Empty array returns empty array."""
        result = compute_stem_id_hash(np.array([]))
        assert len(result) == 0
        assert isinstance(result, np.ndarray)

    def test_normalize_with_minimum_empty(self):
        """Empty array returns empty array."""
        result = normalize_with_minimum(np.array([]))
        assert len(result) == 0
        assert isinstance(result, np.ndarray)

    def test_pack_unity_vertex_colors_empty(self):
        """Empty arrays return empty color array."""
        result = pack_unity_vertex_colors(np.array([]), np.array([]), np.array([]))
        assert len(result) == 0
        assert isinstance(result, np.ndarray)

    def test_create_pivot_index_pixels_empty(self):
        """Empty data produces zeroed texture."""
        result = create_pivot_index_pixels(
            stem_ids=np.array([]),
            pivot_positions=np.zeros((0, 3)),
            hierarchy_depths=np.array([]),
            texture_size=4,
        )
        assert len(result) == 4 * 4 * 4
        assert np.all(result == 0.0)

    def test_create_xvector_extent_pixels_empty(self):
        """Empty data produces zeroed texture."""
        result = create_xvector_extent_pixels(
            stem_ids=np.array([]),
            directions=np.zeros((0, 3)),
            branch_extents=np.array([]),
            texture_size=4,
        )
        assert len(result) == 4 * 4 * 4
        assert np.all(result == 0.0)


class TestSingleVertexCases:
    """Tests for single vertex input."""

    def test_compute_stem_id_hash_single(self):
        """Single value returns single hash."""
        result = compute_stem_id_hash(np.array([42.0]))
        assert len(result) == 1
        assert 0.0 <= result[0] < 1.0

    def test_normalize_with_minimum_single(self):
        """Single value normalizes correctly."""
        result = normalize_with_minimum(np.array([5.0]), min_divisor=1.0)
        assert len(result) == 1
        assert result[0] == pytest.approx(1.0)  # 5/5 = 1

    def test_pack_unity_vertex_colors_single(self):
        """Single vertex produces 4 color values."""
        result = pack_unity_vertex_colors(np.array([0.5]), np.array([0.3]), np.array([0.7]))
        assert len(result) == 4
        assert result[3] == pytest.approx(1.0)  # Alpha

    def test_create_pivot_index_pixels_single(self):
        """Single vertex creates one pixel."""
        result = create_pivot_index_pixels(
            stem_ids=np.array([0.0]),
            pivot_positions=np.array([[1.0, 2.0, 3.0]]),
            hierarchy_depths=np.array([0.5]),
            texture_size=4,
        )
        # Only pixel 0 should be set
        assert result[0] == pytest.approx(1.0)  # X
        assert result[1] == pytest.approx(2.0)  # Y
        assert result[2] == pytest.approx(3.0)  # Z
        assert result[3] == pytest.approx(0.5)  # depth
        # Other pixels should be zero
        assert result[4] == 0.0


class TestNumericLimits:
    """Tests for numeric edge cases and limits."""

    def test_compute_stem_id_hash_very_large(self):
        """Very large stem IDs still produce valid hashes."""
        large_ids = np.array([1e15, 1e18, np.finfo(np.float64).max / 2])
        result = compute_stem_id_hash(large_ids)
        assert np.all(np.isfinite(result))
        assert np.all(result >= 0.0)
        assert np.all(result < 1.0)

    def test_normalize_with_minimum_very_small_values(self):
        """Very small values normalize without overflow."""
        tiny = np.array([1e-100, 1e-200, 1e-300])
        result = normalize_with_minimum(tiny, min_divisor=1.0)
        assert np.all(np.isfinite(result))

    def test_normalize_with_minimum_very_large_values(self):
        """Very large values normalize without overflow."""
        huge = np.array([1e100, 1e200, 1e300])
        result = normalize_with_minimum(huge, min_divisor=1.0)
        assert np.all(np.isfinite(result))
        assert result[-1] == pytest.approx(1.0)

    def test_stem_id_to_pixel_coords_large_stem_id(self):
        """Large stem ID beyond texture bounds still computes."""
        px, py = stem_id_to_pixel_coords(1000000, 1024)
        assert px == 1000000 % 1024
        assert py == 1000000 // 1024

    def test_stem_id_to_uv_coords_large_stem_id(self):
        """Large stem ID produces valid UV (even if > 1)."""
        u, v = stem_id_to_uv_coords(1000000, 1024)
        assert np.isfinite(u)
        assert np.isfinite(v)


class TestTextureBoundaryConditions:
    """Tests for texture edge cases."""

    def test_stem_id_at_texture_max(self):
        """Stem ID at max texture capacity."""
        size = 4
        max_stem_id = size * size - 1  # 15 for 4x4
        px, py = stem_id_to_pixel_coords(max_stem_id, size)
        assert px == 3
        assert py == 3

    def test_stem_id_exceeds_texture(self):
        """Stem ID beyond texture capacity wraps correctly."""
        size = 4
        stem_id = size * size  # 16, first pixel of "next" texture
        px, py = stem_id_to_pixel_coords(stem_id, size)
        assert px == 0
        assert py == 4  # Beyond texture bounds

    def test_create_pivot_index_pixels_ignores_overflow(self):
        """Stems beyond texture bounds are ignored."""
        size = 4
        stem_ids = np.array([0.0, 16.0])  # Second one overflows
        positions = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        depths = np.array([1.0, 1.0])

        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=size)

        # Stem 0 should be written
        assert result[0] == pytest.approx(1.0)
        # Stem 16 overflows (py=4 >= size), shouldn't crash

    def test_texture_size_one(self):
        """Minimal 1x1 texture works."""
        result = create_pivot_index_pixels(
            stem_ids=np.array([0.0]),
            pivot_positions=np.array([[1.0, 2.0, 3.0]]),
            hierarchy_depths=np.array([0.5]),
            texture_size=1,
        )
        assert len(result) == 4
        assert result[0] == pytest.approx(1.0)

    def test_uv_coords_for_single_pixel_texture(self):
        """UV for 1x1 texture centers correctly."""
        u, v = stem_id_to_uv_coords(0, 1)
        assert u == pytest.approx(0.5)
        assert v == pytest.approx(0.5)


class TestZeroVectorHandling:
    """Tests for zero and near-zero vector handling."""

    def test_normalize_exact_zero_vector(self):
        """Exact zero vector returns fallback."""
        direction = np.array([0.0, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        np.testing.assert_array_almost_equal(result, [0.0, 0.0, 1.0])

    def test_normalize_near_zero_vector(self):
        """Near-zero vector uses fallback."""
        direction = np.array([1e-10, 1e-10, 1e-10])
        result = normalize_direction_vector(direction, epsilon=1e-6)
        np.testing.assert_array_almost_equal(result, [0.0, 0.0, 1.0])

    def test_normalize_just_above_epsilon(self):
        """Vector just above epsilon normalizes normally."""
        # Length = sqrt(3) * 1e-5 ≈ 1.73e-5 > 1e-6
        direction = np.array([1e-5, 1e-5, 1e-5])
        result = normalize_direction_vector(direction, epsilon=1e-6)
        # Should be normalized, not fallback
        length = np.linalg.norm(result)
        assert length == pytest.approx(1.0, rel=1e-5)

    def test_create_xvector_extent_handles_zero_direction(self):
        """XVector texture uses fallback for zero directions."""
        result = create_xvector_extent_pixels(
            stem_ids=np.array([0.0]),
            directions=np.array([[0.0, 0.0, 0.0]]),
            branch_extents=np.array([1.0]),
            texture_size=4,
        )
        # Should use fallback [0, 0, 1]
        assert result[0] == pytest.approx(0.0)  # X
        assert result[1] == pytest.approx(0.0)  # Y
        assert result[2] == pytest.approx(1.0)  # Z


class TestNaNHandling:
    """Tests for NaN value handling."""

    def test_compute_stem_id_hash_nan_propagates(self):
        """NaN in input produces NaN in output (expected behavior)."""
        result = compute_stem_id_hash(np.array([np.nan]))
        assert np.isnan(result[0])

    def test_normalize_direction_nan_vector(self):
        """NaN direction vector is handled."""
        direction = np.array([np.nan, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        # linalg.norm of NaN is NaN, which is not > epsilon
        # So fallback should be used
        np.testing.assert_array_almost_equal(result, [0.0, 0.0, 1.0])


class TestNegativeValues:
    """Tests for negative value handling."""

    def test_compute_stem_id_hash_negative(self):
        """Negative stem IDs produce valid hashes (mod wraps)."""
        result = compute_stem_id_hash(np.array([-1.0, -100.0, -1000.0]))
        # mod with negative produces positive result in numpy
        assert np.all(result >= 0.0)
        assert np.all(result < 1.0)

    def test_normalize_with_minimum_all_negative(self):
        """All negative values normalize correctly."""
        values = np.array([-10.0, -5.0, -1.0])
        result = normalize_with_minimum(values, min_divisor=1.0)
        # Max of negatives is -1, but min_divisor=1 is used
        # So result = values / 1.0 = values
        np.testing.assert_array_almost_equal(result, values)

    def test_normalize_direction_all_negative(self):
        """All-negative direction normalizes correctly."""
        direction = np.array([-1.0, -1.0, -1.0])
        result = normalize_direction_vector(direction)
        length = np.linalg.norm(result)
        assert length == pytest.approx(1.0, rel=1e-5)
        assert np.all(result < 0)

    def test_pivot_positions_can_be_negative(self):
        """Negative world positions are stored correctly."""
        result = create_pivot_index_pixels(
            stem_ids=np.array([0.0]),
            pivot_positions=np.array([[-10.0, -20.0, -30.0]]),
            hierarchy_depths=np.array([1.0]),
            texture_size=4,
        )
        assert result[0] == pytest.approx(-10.0)
        assert result[1] == pytest.approx(-20.0)
        assert result[2] == pytest.approx(-30.0)


class TestDuplicateStemIds:
    """Tests for handling duplicate stem IDs."""

    def test_create_pivot_index_uses_first_vertex(self):
        """When stem ID appears multiple times, first vertex is used."""
        stem_ids = np.array([0.0, 0.0, 0.0])
        positions = np.array(
            [
                [1.0, 0.0, 0.0],  # First
                [2.0, 0.0, 0.0],  # Duplicate
                [3.0, 0.0, 0.0],  # Duplicate
            ]
        )
        depths = np.array([0.1, 0.2, 0.3])

        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Should use first vertex's data
        assert result[0] == pytest.approx(1.0)  # First position
        assert result[3] == pytest.approx(0.1)  # First depth

    def test_create_xvector_uses_first_vertex(self):
        """XVector texture uses first vertex for duplicate stems."""
        stem_ids = np.array([0.0, 0.0])
        directions = np.array(
            [
                [1.0, 0.0, 0.0],  # First
                [0.0, 1.0, 0.0],  # Duplicate
            ]
        )
        extents = np.array([1.0, 2.0])

        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        # Should use first vertex's direction
        assert result[0] == pytest.approx(1.0)  # X = 1
        assert result[1] == pytest.approx(0.0)  # Y = 0


class TestFloatPrecision:
    """Tests for floating point precision issues."""

    def test_normalize_direction_near_unit_length(self):
        """Direction vectors near unit length don't cause issues."""
        # Vector slightly longer than 1
        direction = np.array([1.0 + 1e-10, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        length = np.linalg.norm(result)
        assert length == pytest.approx(1.0, rel=1e-9)

    def test_normalize_direction_clamps_result(self):
        """Result components are clamped to [-1, 1]."""
        # Even with potential floating point errors, result should be clamped
        direction = np.array([1.0, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)

    def test_uv_coords_precision(self):
        """UV coordinates have reasonable precision."""
        # Test that centering calculation doesn't accumulate error
        u, v = stem_id_to_uv_coords(0, 1024)
        expected_u = 0.5 / 1024
        assert abs(u - expected_u) < 1e-15


class TestMixedStemIds:
    """Tests for non-sequential and mixed stem IDs."""

    def test_non_sequential_stem_ids(self):
        """Non-sequential stem IDs map correctly."""
        stem_ids = np.array([0.0, 5.0, 10.0])
        positions = np.array(
            [
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [3.0, 0.0, 0.0],
            ]
        )
        depths = np.array([1.0, 2.0, 3.0])

        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=16)

        # Check each stem's pixel
        assert result[0] == pytest.approx(1.0)  # Stem 0, pixel 0
        assert result[5 * 4] == pytest.approx(2.0)  # Stem 5, pixel 5
        assert result[10 * 4] == pytest.approx(3.0)  # Stem 10, pixel 10

    def test_integer_stem_ids_map_correctly(self):
        """Integer stem IDs map to correct pixels."""
        stem_ids = np.array([0.0, 1.0, 2.0])
        positions = np.array(
            [
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [3.0, 0.0, 0.0],
            ]
        )
        depths = np.array([1.0, 1.0, 1.0])

        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Stem 0 -> pixel 0, Stem 1 -> pixel 1, Stem 2 -> pixel 2
        assert result[0] == pytest.approx(1.0)  # Pixel 0
        assert result[4] == pytest.approx(2.0)  # Pixel 1
        assert result[8] == pytest.approx(3.0)  # Pixel 2

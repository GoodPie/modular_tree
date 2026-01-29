"""Tests for pivot painter core pure functions."""

import numpy as np
import pytest
from core import (
    GOLDEN_RATIO_CONJUGATE,
    compute_stem_id_hash,
    create_pivot_index_pixels,
    create_xvector_extent_pixels,
    normalize_direction_vector,
    normalize_with_minimum,
    pack_unity_vertex_colors,
    stem_id_to_pixel_coords,
    stem_id_to_uv_coords,
)


class TestComputeStemIdHash:
    """Tests for compute_stem_id_hash function."""

    def test_stem_id_zero_returns_zero(self):
        """Stem ID 0 should hash to 0."""
        result = compute_stem_id_hash(np.array([0.0]))
        assert result[0] == pytest.approx(0.0)

    def test_stem_id_one_returns_golden_ratio(self):
        """Stem ID 1 should hash to approximately 0.618."""
        result = compute_stem_id_hash(np.array([1.0]))
        assert result[0] == pytest.approx(GOLDEN_RATIO_CONJUGATE, rel=1e-6)

    def test_result_in_zero_one_range(self):
        """All hash values should be in [0, 1) range."""
        stem_ids = np.array([0.0, 1.0, 10.0, 100.0, 1000.0, 999999.0])
        result = compute_stem_id_hash(stem_ids)
        assert np.all(result >= 0.0)
        assert np.all(result < 1.0)

    def test_empty_array(self):
        """Empty input should return empty output."""
        result = compute_stem_id_hash(np.array([]))
        assert len(result) == 0

    def test_large_stem_ids(self):
        """Large stem IDs should still produce valid hashes."""
        stem_ids = np.array([1e9, 1e12])
        result = compute_stem_id_hash(stem_ids)
        assert np.all(result >= 0.0)
        assert np.all(result < 1.0)

    def test_sequential_ids_spread_evenly(self):
        """Sequential stem IDs should spread across range (golden ratio property)."""
        stem_ids = np.arange(10, dtype=float)
        result = compute_stem_id_hash(stem_ids)
        # Check that values are reasonably distributed (not all clustered)
        assert result.max() - result.min() > 0.5

    def test_preserves_array_shape(self):
        """Output array should have same shape as input."""
        stem_ids = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = compute_stem_id_hash(stem_ids)
        assert result.shape == stem_ids.shape


class TestNormalizeWithMinimum:
    """Tests for normalize_with_minimum function."""

    def test_normalize_simple_values(self):
        """Simple values should normalize correctly."""
        values = np.array([0.0, 5.0, 10.0])
        result = normalize_with_minimum(values)
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(1.0)

    def test_min_divisor_prevents_division_by_zero(self):
        """Min divisor should prevent division by zero."""
        values = np.array([0.0, 0.0, 0.0])
        result = normalize_with_minimum(values, min_divisor=1.0)
        assert np.all(result == 0.0)

    def test_custom_min_divisor(self):
        """Custom min divisor should be used when max is below it."""
        values = np.array([0.5])
        result = normalize_with_minimum(values, min_divisor=2.0)
        assert result[0] == pytest.approx(0.25)

    def test_max_exceeds_min_divisor(self):
        """When max exceeds min divisor, max is used."""
        values = np.array([0.0, 10.0])
        result = normalize_with_minimum(values, min_divisor=1.0)
        assert result[1] == pytest.approx(1.0)

    def test_empty_array(self):
        """Empty array should return empty array."""
        values = np.array([])
        result = normalize_with_minimum(values)
        assert len(result) == 0

    def test_negative_values(self):
        """Negative values should work correctly."""
        values = np.array([-5.0, 0.0, 5.0])
        result = normalize_with_minimum(values, min_divisor=1.0)
        assert result[2] == pytest.approx(1.0)
        # Negative stays negative
        assert result[0] == pytest.approx(-1.0)


class TestPackUnityVertexColors:
    """Tests for pack_unity_vertex_colors function."""

    def test_basic_packing(self):
        """Colors should be packed in RGBARGBA... format."""
        depths = np.array([0.5])
        extents = np.array([0.3])
        hashes = np.array([0.7])
        result = pack_unity_vertex_colors(depths, extents, hashes)
        assert result[0] == pytest.approx(0.5)  # R
        assert result[1] == pytest.approx(0.3)  # G
        assert result[2] == pytest.approx(0.7)  # B
        assert result[3] == pytest.approx(1.0)  # A

    def test_alpha_always_one(self):
        """Alpha channel should always be 1.0."""
        depths = np.array([0.0, 0.5, 1.0])
        extents = np.array([0.0, 0.5, 1.0])
        hashes = np.array([0.0, 0.5, 1.0])
        result = pack_unity_vertex_colors(depths, extents, hashes)
        for i in range(3):
            assert result[i * 4 + 3] == pytest.approx(1.0)

    def test_output_length(self):
        """Output should be 4x vertex count."""
        count = 10
        depths = np.zeros(count)
        extents = np.zeros(count)
        hashes = np.zeros(count)
        result = pack_unity_vertex_colors(depths, extents, hashes)
        assert len(result) == count * 4

    def test_channel_correctness(self):
        """Each channel should contain correct data."""
        depths = np.array([0.1, 0.2, 0.3])
        extents = np.array([0.4, 0.5, 0.6])
        hashes = np.array([0.7, 0.8, 0.9])
        result = pack_unity_vertex_colors(depths, extents, hashes)

        for i in range(3):
            assert result[i * 4] == pytest.approx(depths[i])  # R
            assert result[i * 4 + 1] == pytest.approx(extents[i])  # G
            assert result[i * 4 + 2] == pytest.approx(hashes[i])  # B
            assert result[i * 4 + 3] == pytest.approx(1.0)  # A

    def test_empty_arrays(self):
        """Empty input should return empty output."""
        result = pack_unity_vertex_colors(np.array([]), np.array([]), np.array([]))
        assert len(result) == 0


class TestStemIdToPixelCoords:
    """Tests for stem_id_to_pixel_coords function."""

    def test_stem_id_zero(self):
        """Stem ID 0 should map to (0, 0)."""
        px, py = stem_id_to_pixel_coords(0, 1024)
        assert px == 0
        assert py == 0

    def test_stem_id_one(self):
        """Stem ID 1 should map to (1, 0)."""
        px, py = stem_id_to_pixel_coords(1, 1024)
        assert px == 1
        assert py == 0

    def test_stem_id_at_row_boundary(self):
        """Stem ID at row boundary should wrap to next row."""
        px, py = stem_id_to_pixel_coords(1024, 1024)
        assert px == 0
        assert py == 1

    def test_stem_id_mid_row(self):
        """Stem ID in middle of second row."""
        px, py = stem_id_to_pixel_coords(1030, 1024)
        assert px == 6  # 1030 % 1024 = 6
        assert py == 1  # 1030 // 1024 = 1

    def test_small_texture_size(self):
        """Works with small texture sizes."""
        px, py = stem_id_to_pixel_coords(5, 4)
        assert px == 1  # 5 % 4 = 1
        assert py == 1  # 5 // 4 = 1

    def test_large_stem_id(self):
        """Large stem IDs map correctly."""
        size = 256
        stem_id = 65536  # 256 * 256
        px, py = stem_id_to_pixel_coords(stem_id, size)
        assert px == 0
        assert py == 256  # Off texture but calculation is correct


class TestStemIdToUvCoords:
    """Tests for stem_id_to_uv_coords function."""

    def test_stem_id_zero_centers_in_first_pixel(self):
        """Stem ID 0 should map to center of first pixel."""
        u, v = stem_id_to_uv_coords(0, 1024)
        assert u == pytest.approx(0.5 / 1024)
        assert v == pytest.approx(0.5 / 1024)

    def test_uv_coords_centered(self):
        """UV coordinates should be centered in pixels."""
        u, v = stem_id_to_uv_coords(1, 4)
        # Pixel (1, 0) -> UV center is (1.5/4, 0.5/4)
        assert u == pytest.approx(1.5 / 4)
        assert v == pytest.approx(0.5 / 4)

    def test_second_row_uv(self):
        """Second row UV coordinates."""
        u, v = stem_id_to_uv_coords(4, 4)
        # Pixel (0, 1) -> UV center is (0.5/4, 1.5/4)
        assert u == pytest.approx(0.5 / 4)
        assert v == pytest.approx(1.5 / 4)

    def test_uv_range_within_zero_one(self):
        """UVs for valid pixels should be in (0, 1) range."""
        size = 128
        for stem_id in [0, 1, 127, 128, 1000, size * size - 1]:
            u, v = stem_id_to_uv_coords(stem_id, size)
            if stem_id < size * size:
                assert 0 < u < 1
                assert 0 < v < 1


class TestNormalizeDirectionVector:
    """Tests for normalize_direction_vector function."""

    def test_unit_vector_unchanged(self):
        """Unit vectors should remain unchanged."""
        direction = np.array([1.0, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        np.testing.assert_array_almost_equal(result, [1.0, 0.0, 0.0])

    def test_scales_to_unit_length(self):
        """Non-unit vectors should be scaled to unit length."""
        direction = np.array([3.0, 0.0, 4.0])  # length = 5
        result = normalize_direction_vector(direction)
        np.testing.assert_array_almost_equal(result, [0.6, 0.0, 0.8])

    def test_zero_vector_returns_fallback(self):
        """Zero vector should return fallback (default [0,0,1])."""
        direction = np.array([0.0, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        np.testing.assert_array_almost_equal(result, [0.0, 0.0, 1.0])

    def test_custom_fallback(self):
        """Custom fallback should be used for zero vectors."""
        direction = np.array([0.0, 0.0, 0.0])
        fallback = np.array([0.0, 1.0, 0.0])
        result = normalize_direction_vector(direction, fallback=fallback)
        np.testing.assert_array_almost_equal(result, [0.0, 1.0, 0.0])

    def test_very_small_vector_uses_fallback(self):
        """Very small vectors should use fallback."""
        direction = np.array([1e-8, 0.0, 0.0])
        result = normalize_direction_vector(direction, epsilon=1e-6)
        np.testing.assert_array_almost_equal(result, [0.0, 0.0, 1.0])

    def test_negative_components(self):
        """Negative components should be handled correctly."""
        direction = np.array([-1.0, -1.0, -1.0])
        result = normalize_direction_vector(direction)
        length = np.linalg.norm(result)
        assert length == pytest.approx(1.0)
        assert np.all(result < 0)

    def test_result_clamped_to_valid_range(self):
        """Result should be clamped to [-1, 1] range."""
        direction = np.array([1.0, 0.0, 0.0])
        result = normalize_direction_vector(direction)
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)

    def test_does_not_modify_original(self):
        """Original array should not be modified."""
        direction = np.array([3.0, 0.0, 4.0])
        original = direction.copy()
        normalize_direction_vector(direction)
        np.testing.assert_array_equal(direction, original)

    def test_fallback_is_copied(self):
        """Returned fallback should be a copy, not the original."""
        direction = np.array([0.0, 0.0, 0.0])
        fallback = np.array([0.0, 1.0, 0.0])
        result = normalize_direction_vector(direction, fallback=fallback)
        result[1] = 999.0
        assert fallback[1] == pytest.approx(1.0)


class TestCreatePivotIndexPixels:
    """Tests for create_pivot_index_pixels function."""

    def test_basic_pixel_generation(self):
        """Basic pixel generation for single stem."""
        stem_ids = np.array([0.0, 0.0, 0.0])
        positions = np.array([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
        depths = np.array([0.5, 0.5, 0.5])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Pixel 0 should contain position and depth
        assert result[0] == pytest.approx(1.0)  # R = X
        assert result[1] == pytest.approx(2.0)  # G = Y
        assert result[2] == pytest.approx(3.0)  # B = Z
        assert result[3] == pytest.approx(0.5)  # A = depth

    def test_multiple_stems(self):
        """Multiple stems write to different pixels."""
        stem_ids = np.array([0.0, 1.0])
        positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        depths = np.array([1.0, 2.0])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Pixel 0 (stem 0)
        assert result[0] == pytest.approx(1.0)  # R
        # Pixel 1 (stem 1)
        assert result[4] == pytest.approx(0.0)  # R
        assert result[5] == pytest.approx(1.0)  # G

    def test_stem_in_second_row(self):
        """Stem ID that wraps to second row."""
        stem_ids = np.array([4.0])  # In 4x4 texture, this is row 1, col 0
        positions = np.array([[5.0, 6.0, 7.0]])
        depths = np.array([1.0])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Pixel at row 1, col 0 -> index = (1 * 4 + 0) * 4 = 16
        assert result[16] == pytest.approx(5.0)
        assert result[17] == pytest.approx(6.0)
        assert result[18] == pytest.approx(7.0)
        assert result[19] == pytest.approx(1.0)

    def test_output_size(self):
        """Output array has correct size."""
        stem_ids = np.array([0.0])
        positions = np.array([[0.0, 0.0, 0.0]])
        depths = np.array([0.0])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=8)
        assert len(result) == 8 * 8 * 4

    def test_empty_input(self):
        """Empty input produces zeroed texture."""
        stem_ids = np.array([])
        positions = np.zeros((0, 3))
        depths = np.array([])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)
        assert np.all(result == 0.0)

    def test_takes_first_vertex_for_stem(self):
        """Uses first vertex's data for each stem."""
        stem_ids = np.array([0.0, 0.0, 0.0])
        positions = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
        depths = np.array([0.1, 0.2, 0.3])
        result = create_pivot_index_pixels(stem_ids, positions, depths, texture_size=4)

        # Should use first vertex's position (1.0) not others
        assert result[0] == pytest.approx(1.0)
        assert result[3] == pytest.approx(0.1)


class TestCreateXvectorExtentPixels:
    """Tests for create_xvector_extent_pixels function."""

    def test_basic_pixel_generation(self):
        """Basic pixel generation with direction and extent."""
        stem_ids = np.array([0.0])
        directions = np.array([[1.0, 0.0, 0.0]])
        extents = np.array([5.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        # Pixel 0 should contain normalized direction and extent
        assert result[0] == pytest.approx(1.0)  # R = X
        assert result[1] == pytest.approx(0.0)  # G = Y
        assert result[2] == pytest.approx(0.0)  # B = Z
        assert result[3] == pytest.approx(5.0)  # A = extent

    def test_normalizes_direction(self):
        """Direction should be normalized to unit length."""
        stem_ids = np.array([0.0])
        directions = np.array([[3.0, 0.0, 4.0]])  # length = 5
        extents = np.array([1.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        assert result[0] == pytest.approx(0.6)  # 3/5
        assert result[1] == pytest.approx(0.0)
        assert result[2] == pytest.approx(0.8)  # 4/5

    def test_zero_direction_uses_fallback(self):
        """Zero direction should use fallback [0, 0, 1]."""
        stem_ids = np.array([0.0])
        directions = np.array([[0.0, 0.0, 0.0]])
        extents = np.array([1.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.0)
        assert result[2] == pytest.approx(1.0)  # Z = 1 (fallback)

    def test_multiple_stems(self):
        """Multiple stems write to different pixels."""
        stem_ids = np.array([0.0, 1.0])
        directions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        extents = np.array([1.0, 2.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        # Pixel 0 (stem 0)
        assert result[0] == pytest.approx(1.0)  # X direction
        assert result[3] == pytest.approx(1.0)  # extent
        # Pixel 1 (stem 1)
        assert result[5] == pytest.approx(1.0)  # Y direction
        assert result[7] == pytest.approx(2.0)  # extent

    def test_output_size(self):
        """Output array has correct size."""
        stem_ids = np.array([0.0])
        directions = np.array([[1.0, 0.0, 0.0]])
        extents = np.array([1.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=16)
        assert len(result) == 16 * 16 * 4

    def test_empty_input(self):
        """Empty input produces zeroed texture."""
        stem_ids = np.array([])
        directions = np.zeros((0, 3))
        extents = np.array([])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)
        assert np.all(result == 0.0)

    def test_negative_direction_components(self):
        """Negative direction components are preserved after normalization."""
        stem_ids = np.array([0.0])
        directions = np.array([[-1.0, -1.0, -1.0]])
        extents = np.array([1.0])
        result = create_xvector_extent_pixels(stem_ids, directions, extents, texture_size=4)

        # All components should be negative and equal
        expected = -1.0 / np.sqrt(3)
        assert result[0] == pytest.approx(expected, rel=1e-5)
        assert result[1] == pytest.approx(expected, rel=1e-5)
        assert result[2] == pytest.approx(expected, rel=1e-5)

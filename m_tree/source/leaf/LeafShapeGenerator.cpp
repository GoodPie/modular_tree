#include "LeafShapeGenerator.hpp"
#include <algorithm>
#include <cmath>
#include <numeric>

namespace Mtree
{

static constexpr float PI = 3.14159265358979323846f;
static constexpr float TWO_PI = 2.0f * PI;

float LeafShapeGenerator::superformula_radius(float theta, float effective_n1) const
{
	float ct = std::cos(m * theta / 4.0f);
	float st = std::sin(m * theta / 4.0f);

	float term1 = std::pow(std::abs(ct / a), n2);
	float term2 = std::pow(std::abs(st / b), n3);

	float sum = term1 + term2;
	if (sum < 1e-10f)
		return 1.0f;

	return std::pow(sum, -1.0f / effective_n1);
}

std::vector<Vector2> LeafShapeGenerator::sample_contour()
{
	int res = std::max(contour_resolution, 8);

	// Sample base contour points
	std::vector<Vector2> points;
	points.reserve(res * 2);

	float clamped_n1 = (std::abs(n1) < 0.001f) ? 0.001f : n1;

	for (int i = 0; i < res; ++i)
	{
		float theta = TWO_PI * static_cast<float>(i) / static_cast<float>(res);
		float r = superformula_radius(theta, clamped_n1);
		float x = r * std::cos(theta) * aspect_ratio;
		float y = r * std::sin(theta);
		points.push_back(Vector2(x, y));
	}

	// Adaptive refinement: subdivide segments with high curvature
	std::vector<Vector2> refined;
	refined.reserve(points.size() * 2);

	for (size_t i = 0; i < points.size(); ++i)
	{
		size_t prev = (i == 0) ? points.size() - 1 : i - 1;
		size_t next = (i + 1) % points.size();

		refined.push_back(points[i]);

		// Check curvature deviation between this segment and the next
		Vector2 d1 = points[i] - points[prev];
		Vector2 d2 = points[next] - points[i];
		d1.normalize();
		d2.normalize();
		float dot = d1.dot(d2);

		// If angle deviation is significant, add midpoint
		if (dot < 0.95f)
		{
			float theta_mid = TWO_PI * (static_cast<float>(i) + 0.5f) / static_cast<float>(res);
			float r_mid = superformula_radius(theta_mid, clamped_n1);
			float x_mid = r_mid * std::cos(theta_mid) * aspect_ratio;
			float y_mid = r_mid * std::sin(theta_mid);
			refined.push_back(Vector2(x_mid, y_mid));
		}
	}

	return refined;
}

std::vector<Vector2> LeafShapeGenerator::apply_margin(const std::vector<Vector2>& contour)
{
	if (margin_type == MarginType::Entire || tooth_count <= 0)
	{
		return contour;
	}

	std::mt19937 rng(asymmetry_seed);
	std::uniform_real_distribution<float> asym_dist(-0.3f, 0.3f);

	std::vector<Vector2> result;
	result.reserve(contour.size());

	for (size_t i = 0; i < contour.size(); ++i)
	{
		const Vector2& pt = contour[i];
		float r = pt.norm();
		if (r < 1e-10f)
		{
			result.push_back(pt);
			continue;
		}

		float theta = std::atan2(pt.y(), pt.x());
		if (theta < 0.0f)
			theta += TWO_PI;

		float t = theta * static_cast<float>(tooth_count) / TWO_PI;
		float frac = t - std::floor(t);
		float asym_offset = (asymmetry_seed != 0) ? asym_dist(rng) : 0.0f;
		float depth = tooth_depth * (1.0f + asym_offset);
		float mod = 0.0f;

		switch (margin_type)
		{
		case MarginType::Serrate:
		{
			// Asymmetric sawtooth wave (teeth point toward tip)
			float saw = frac < tooth_sharpness ? frac / tooth_sharpness
			                                   : (1.0f - frac) / (1.0f - tooth_sharpness);
			mod = depth * saw;
			break;
		}
		case MarginType::Dentate:
		{
			// Symmetric triangular wave (teeth point outward)
			mod = depth * (1.0f - 2.0f * std::abs(frac - 0.5f));
			break;
		}
		case MarginType::Crenate:
		{
			// Sine wave (rounded scallops)
			mod = depth * 0.5f * (1.0f + std::sin(TWO_PI * frac));
			break;
		}
		case MarginType::Lobed:
		{
			// Low-frequency cosine with high amplitude
			mod = depth * 0.5f * (1.0f + std::cos(TWO_PI * frac));
			break;
		}
		default:
			break;
		}

		float new_r = r * (1.0f + mod);
		result.push_back(Vector2(new_r * std::cos(theta), new_r * std::sin(theta)));
	}

	return result;
}

float LeafShapeGenerator::cross2d(const Vector2& o, const Vector2& a, const Vector2& b) const
{
	return (a.x() - o.x()) * (b.y() - o.y()) - (a.y() - o.y()) * (b.x() - o.x());
}

bool LeafShapeGenerator::point_in_triangle(const Vector2& p, const Vector2& a, const Vector2& b,
                                           const Vector2& c) const
{
	float d1 = cross2d(p, a, b);
	float d2 = cross2d(p, b, c);
	float d3 = cross2d(p, c, a);

	bool has_neg = (d1 < 0) || (d2 < 0) || (d3 < 0);
	bool has_pos = (d1 > 0) || (d2 > 0) || (d3 > 0);

	return !(has_neg && has_pos);
}

bool LeafShapeGenerator::is_ear(const std::vector<Vector2>& polygon, int prev, int curr,
                                int next) const
{
	const Vector2& a = polygon[prev];
	const Vector2& b = polygon[curr];
	const Vector2& c = polygon[next];

	// Must be convex (counter-clockwise)
	if (cross2d(a, b, c) <= 0.0f)
		return false;

	// No other vertices inside this triangle
	for (size_t i = 0; i < polygon.size(); ++i)
	{
		int ii = static_cast<int>(i);
		if (ii == prev || ii == curr || ii == next)
			continue;
		if (point_in_triangle(polygon[i], a, b, c))
			return false;
	}

	return true;
}

Mesh LeafShapeGenerator::triangulate(const std::vector<Vector2>& contour)
{
	Mesh mesh;

	// Add vertices to mesh (Z = 0 for flat leaf)
	for (const auto& pt : contour)
	{
		mesh.vertices.push_back(Vector3(pt.x(), pt.y(), 0.0f));
	}

	// Ear clipping triangulation
	std::vector<int> indices(contour.size());
	std::iota(indices.begin(), indices.end(), 0);

	// Ensure counter-clockwise winding
	float signed_area = 0.0f;
	for (size_t i = 0; i < contour.size(); ++i)
	{
		size_t next = (i + 1) % contour.size();
		signed_area += contour[i].x() * contour[next].y();
		signed_area -= contour[next].x() * contour[i].y();
	}
	if (signed_area < 0.0f)
	{
		std::reverse(indices.begin(), indices.end());
	}

	// Build polygon list for ear clipping
	std::vector<Vector2> poly;
	poly.reserve(indices.size());
	for (int idx : indices)
	{
		poly.push_back(contour[idx]);
	}

	while (poly.size() > 2)
	{
		bool ear_found = false;
		for (size_t i = 0; i < poly.size(); ++i)
		{
			int prev_idx = static_cast<int>((i == 0) ? poly.size() - 1 : i - 1);
			int curr_idx = static_cast<int>(i);
			int next_idx = static_cast<int>((i + 1) % poly.size());

			if (is_ear(poly, prev_idx, curr_idx, next_idx))
			{
				// Add triangle as degenerate quad (for compatibility with Mesh format)
				int pi = mesh.polygons.size();
				mesh.polygons.push_back(
				    {indices[prev_idx], indices[curr_idx], indices[next_idx], indices[next_idx]});
				mesh.uv_loops.push_back({0, 0, 0, 0}); // UVs computed later

				// Remove ear vertex
				poly.erase(poly.begin() + i);
				indices.erase(indices.begin() + i);
				ear_found = true;
				break;
			}
		}
		if (!ear_found)
		{
			// Fallback: centroid fan triangulation for remaining polygon
			if (poly.size() > 2)
			{
				// Compute centroid of remaining polygon
				Vector2 centroid(0.0f, 0.0f);
				for (const auto& pt : poly)
				{
					centroid += pt;
				}
				centroid /= static_cast<float>(poly.size());

				// Add centroid as a new mesh vertex
				int centroid_idx = static_cast<int>(mesh.vertices.size());
				mesh.vertices.push_back(Vector3(centroid.x(), centroid.y(), 0.0f));

				// Fan-triangulate from centroid to each edge
				for (size_t i = 0; i < poly.size(); ++i)
				{
					size_t next = (i + 1) % poly.size();
					mesh.polygons.push_back(
					    {indices[i], indices[next], centroid_idx, centroid_idx});
					mesh.uv_loops.push_back({0, 0, 0, 0}); // UVs computed later
				}
			}
			break; // Polygon fully consumed
		}
	}

	return mesh;
}

void LeafShapeGenerator::apply_deformation(Mesh& mesh, const std::vector<Vector2>& contour)
{
	if (mesh.vertices.empty())
		return;

	// Compute bounding box for normalization
	float min_x = contour[0].x(), max_x = contour[0].x();
	float min_y = contour[0].y(), max_y = contour[0].y();
	for (const auto& pt : contour)
	{
		min_x = std::min(min_x, pt.x());
		max_x = std::max(max_x, pt.x());
		min_y = std::min(min_y, pt.y());
		max_y = std::max(max_y, pt.y());
	}
	float width = max_x - min_x;
	float height = max_y - min_y;
	if (width < 1e-10f || height < 1e-10f)
		return;

	float center_x = (min_x + max_x) * 0.5f;

	// Compute min distance to contour edge for each vertex (for edge curl)
	std::vector<float> edge_distances(mesh.vertices.size(), 1e10f);
	for (size_t vi = 0; vi < mesh.vertices.size(); ++vi)
	{
		Vector2 pt(mesh.vertices[vi].x(), mesh.vertices[vi].y());
		for (size_t ci = 0; ci < contour.size(); ++ci)
		{
			size_t next = (ci + 1) % contour.size();
			Vector2 seg = contour[next] - contour[ci];
			float seg_len = seg.norm();
			if (seg_len < 1e-10f)
				continue;
			float t = std::clamp((pt - contour[ci]).dot(seg) / (seg_len * seg_len), 0.0f, 1.0f);
			Vector2 closest = contour[ci] + t * seg;
			float dist = (pt - closest).norm();
			edge_distances[vi] = std::min(edge_distances[vi], dist);
		}
	}

	// Apply deformations to Z coordinates
	for (size_t i = 0; i < mesh.vertices.size(); ++i)
	{
		auto& v = mesh.vertices[i];
		float nx = (v.x() - center_x) / (width * 0.5f); // -1 to 1 across width
		float ny = (v.y() - min_y) / height;            // 0 to 1 along length

		float z = 0.0f;

		// 1. Midrib curvature: circular arc bend along Y axis
		z += midrib_curvature * ny * ny * 0.5f;

		// 2. Cross curvature: parabolic cupping perpendicular to midrib
		z += cross_curvature * nx * nx * 0.3f;

		// 3. Edge curl: inward curl based on distance from edge
		float max_edge_dist = width * 0.5f;
		float edge_factor =
		    1.0f - std::clamp(edge_distances[i] / (max_edge_dist * 0.3f), 0.0f, 1.0f);
		z += edge_curl * edge_factor * edge_factor * 0.2f;

		v.z() = z;
	}
}

void LeafShapeGenerator::compute_uvs(Mesh& mesh, const std::vector<Vector2>& contour)
{
	if (contour.empty() || mesh.vertices.empty())
		return;

	// Compute bounding box of contour
	float min_x = contour[0].x(), max_x = contour[0].x();
	float min_y = contour[0].y(), max_y = contour[0].y();
	for (const auto& pt : contour)
	{
		min_x = std::min(min_x, pt.x());
		max_x = std::max(max_x, pt.x());
		min_y = std::min(min_y, pt.y());
		max_y = std::max(max_y, pt.y());
	}
	float width = max_x - min_x;
	float height = max_y - min_y;

	// Planar UV projection: map vertex XY to 0-1 range
	mesh.uvs.resize(mesh.vertices.size());
	for (size_t i = 0; i < mesh.vertices.size(); ++i)
	{
		float u = (width > 1e-10f) ? (mesh.vertices[i].x() - min_x) / width : 0.5f;
		float v = (height > 1e-10f) ? (mesh.vertices[i].y() - min_y) / height : 0.5f;
		mesh.uvs[i] = Vector2(std::clamp(u, 0.0f, 1.0f), std::clamp(v, 0.0f, 1.0f));
	}

	// Set UV loops to reference the vertex UVs directly
	for (size_t i = 0; i < mesh.polygons.size(); ++i)
	{
		mesh.uv_loops[i] = mesh.polygons[i]; // UV indices = vertex indices for planar projection
	}
}

Mesh LeafShapeGenerator::generate()
{
	// Parameter validation
	if (std::abs(n1) < 0.001f)
	{
		n1 = (n1 >= 0.0f) ? 0.001f : -0.001f;
	}
	contour_resolution = std::max(contour_resolution, 8);

	// Pipeline
	std::vector<Vector2> contour = sample_contour();
	contour = apply_margin(contour);
	Mesh mesh = triangulate(contour);
	compute_uvs(mesh, contour);
	apply_deformation(mesh, contour);

	return mesh;
}

} // namespace Mtree

#include "LeafLODGenerator.hpp"
#include <Eigen/Geometry>
#include <algorithm>
#include <cmath>

namespace Mtree
{

Mesh LeafLODGenerator::generate_card(const Mesh& source)
{
	Mesh card;

	if (source.vertices.size() < 3)
	{
		return card;
	}

	// Compute axis-aligned bounding box of source mesh
	float min_x = source.vertices[0].x();
	float max_x = source.vertices[0].x();
	float min_y = source.vertices[0].y();
	float max_y = source.vertices[0].y();
	float min_z = source.vertices[0].z();
	float max_z = source.vertices[0].z();

	for (const auto& v : source.vertices)
	{
		min_x = std::min(min_x, v.x());
		max_x = std::max(max_x, v.x());
		min_y = std::min(min_y, v.y());
		max_y = std::max(max_y, v.y());
		min_z = std::min(min_z, v.z());
		max_z = std::max(max_z, v.z());
	}

	// Average Z for the card plane
	float avg_z = (min_z + max_z) * 0.5f;

	// Create 4 vertices for the bounding quad
	// Ordered: bottom-left, bottom-right, top-right, top-left
	card.vertices.push_back(Vector3(min_x, min_y, avg_z));
	card.vertices.push_back(Vector3(max_x, min_y, avg_z));
	card.vertices.push_back(Vector3(max_x, max_y, avg_z));
	card.vertices.push_back(Vector3(min_x, max_y, avg_z));

	// UVs mapping to 0-1 range
	card.uvs.push_back(Vector2(0.0f, 0.0f));
	card.uvs.push_back(Vector2(1.0f, 0.0f));
	card.uvs.push_back(Vector2(1.0f, 1.0f));
	card.uvs.push_back(Vector2(0.0f, 1.0f));

	// Two triangles stored as degenerate quads (matching project convention)
	// Triangle 1: 0, 1, 2, 2
	card.polygons.push_back({0, 1, 2, 2});
	// Triangle 2: 0, 2, 3, 3
	card.polygons.push_back({0, 2, 3, 3});

	// UV loops matching polygons
	card.uv_loops.push_back({0, 1, 2, 2});
	card.uv_loops.push_back({0, 2, 3, 3});

	return card;
}

Mesh LeafLODGenerator::generate_billboard_cloud(const std::vector<Vector3>& positions,
                                                int num_planes)
{
	Mesh cloud;

	if (positions.empty() || num_planes < 1)
	{
		return cloud;
	}

	// Compute center of all positions
	Vector3 center = Vector3::Zero();
	for (const auto& p : positions)
	{
		center += p;
	}
	center /= static_cast<float>(positions.size());

	// Compute bounding radius
	float max_dist = 0.0f;
	for (const auto& p : positions)
	{
		float d = (p - center).norm();
		max_dist = std::max(max_dist, d);
	}

	// Default half-size for each billboard quad
	float half_size = std::max(max_dist, 0.5f);

	// Generate num_planes intersecting quads with evenly distributed normals
	for (int i = 0; i < num_planes; ++i)
	{
		// Distribute plane normals evenly around the Y axis
		float angle =
		    static_cast<float>(M_PI) * static_cast<float>(i) / static_cast<float>(num_planes);

		// Plane normal in the XZ plane
		Vector3 normal(std::cos(angle), 0.0f, std::sin(angle));

		// Build tangent and bitangent for the plane
		Vector3 up(0.0f, 1.0f, 0.0f);
		Vector3 tangent = up.cross(normal).normalized();
		// If normal is parallel to up, use a fallback
		if (tangent.norm() < 0.001f)
		{
			tangent = Vector3(1.0f, 0.0f, 0.0f);
		}
		Vector3 bitangent = normal.cross(tangent).normalized();

		int base_idx = static_cast<int>(cloud.vertices.size());

		// 4 corners of the quad
		cloud.vertices.push_back(center - tangent * half_size - bitangent * half_size);
		cloud.vertices.push_back(center + tangent * half_size - bitangent * half_size);
		cloud.vertices.push_back(center + tangent * half_size + bitangent * half_size);
		cloud.vertices.push_back(center - tangent * half_size + bitangent * half_size);

		// UVs
		cloud.uvs.push_back(Vector2(0.0f, 0.0f));
		cloud.uvs.push_back(Vector2(1.0f, 0.0f));
		cloud.uvs.push_back(Vector2(1.0f, 1.0f));
		cloud.uvs.push_back(Vector2(0.0f, 1.0f));

		// Two triangles per quad (degenerate quad format)
		cloud.polygons.push_back({base_idx, base_idx + 1, base_idx + 2, base_idx + 2});
		cloud.polygons.push_back({base_idx, base_idx + 2, base_idx + 3, base_idx + 3});

		cloud.uv_loops.push_back({base_idx, base_idx + 1, base_idx + 2, base_idx + 2});
		cloud.uv_loops.push_back({base_idx, base_idx + 2, base_idx + 3, base_idx + 3});
	}

	return cloud;
}

std::vector<Vector3> LeafLODGenerator::get_impostor_view_directions(int resolution)
{
	std::vector<Vector3> directions;
	directions.reserve(resolution * resolution);

	// Generate evenly distributed directions on the upper hemisphere
	// using spherical coordinates: theta (azimuth) and phi (elevation)
	for (int j = 0; j < resolution; ++j)
	{
		// Phi: elevation from the pole (0 = straight up, PI/2 = horizon)
		// Distribute from nearly straight up to nearly horizontal
		float phi = static_cast<float>(M_PI) * 0.5f * static_cast<float>(j + 1) /
		            static_cast<float>(resolution + 1);

		for (int i = 0; i < resolution; ++i)
		{
			// Theta: azimuth angle around Y axis
			float theta = 2.0f * static_cast<float>(M_PI) * static_cast<float>(i) /
			              static_cast<float>(resolution);

			float x = std::sin(phi) * std::cos(theta);
			float y = std::sin(phi) * std::sin(theta);
			float z = std::cos(phi); // Always >= 0 for upper hemisphere

			directions.push_back(Vector3(x, y, z).normalized());
		}
	}

	return directions;
}

} // namespace Mtree

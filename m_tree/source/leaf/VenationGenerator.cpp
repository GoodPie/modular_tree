#include "VenationGenerator.hpp"
#include <algorithm>
#include <cmath>
#include <limits>

namespace Mtree
{

// =========================================================================
// SpatialHash2D
// =========================================================================

SpatialHash2D::SpatialHash2D(float cell_size, const Vector2& min_bound, const Vector2& max_bound)
    : cell_size_(cell_size), min_bound_(min_bound)
{
	Vector2 range = max_bound - min_bound;
	grid_width_ = std::max(1, static_cast<int>(std::ceil(range.x() / cell_size_)) + 1);
	grid_height_ = std::max(1, static_cast<int>(std::ceil(range.y() / cell_size_)) + 1);
	cells_.resize(grid_width_ * grid_height_);
}

std::pair<int, int> SpatialHash2D::to_cell(const Vector2& pos) const
{
	int cx = static_cast<int>((pos.x() - min_bound_.x()) / cell_size_);
	int cy = static_cast<int>((pos.y() - min_bound_.y()) / cell_size_);
	cx = std::clamp(cx, 0, grid_width_ - 1);
	cy = std::clamp(cy, 0, grid_height_ - 1);
	return {cx, cy};
}

int SpatialHash2D::cell_index(int cx, int cy) const { return cy * grid_width_ + cx; }

void SpatialHash2D::insert(int id, const Vector2& pos)
{
	auto [cx, cy] = to_cell(pos);
	cells_[cell_index(cx, cy)].push_back({id, pos});
}

std::vector<int> SpatialHash2D::query_radius(const Vector2& center, float radius) const
{
	std::vector<int> result;
	float radius_sq = radius * radius;

	auto [cx_min, cy_min] = to_cell(center - Vector2(radius, radius));
	auto [cx_max, cy_max] = to_cell(center + Vector2(radius, radius));

	for (int cy = cy_min; cy <= cy_max; ++cy)
	{
		for (int cx = cx_min; cx <= cx_max; ++cx)
		{
			const auto& cell = cells_[cell_index(cx, cy)];
			for (const auto& entry : cell)
			{
				float dist_sq = (entry.position - center).squaredNorm();
				if (dist_sq <= radius_sq)
				{
					result.push_back(entry.id);
				}
			}
		}
	}

	return result;
}

void SpatialHash2D::clear()
{
	for (auto& cell : cells_)
	{
		cell.clear();
	}
}

// =========================================================================
// VenationGenerator helpers
// =========================================================================

bool VenationGenerator::point_in_contour(const Vector2& point,
                                         const std::vector<Vector2>& contour) const
{
	int crossings = 0;
	for (size_t i = 0, j = contour.size() - 1; i < contour.size(); j = i++)
	{
		if (((contour[i].y() > point.y()) != (contour[j].y() > point.y())) &&
		    (point.x() < (contour[j].x() - contour[i].x()) * (point.y() - contour[i].y()) /
		                         (contour[j].y() - contour[i].y()) +
		                     contour[i].x()))
		{
			crossings++;
		}
	}
	return (crossings % 2) != 0;
}

float VenationGenerator::compute_contour_area(const std::vector<Vector2>& contour) const
{
	float area = 0.0f;
	for (size_t i = 0, j = contour.size() - 1; i < contour.size(); j = i++)
	{
		area += contour[j].x() * contour[i].y();
		area -= contour[i].x() * contour[j].y();
	}
	return std::abs(area) * 0.5f;
}

float VenationGenerator::distance_to_segment(const Vector2& p, const Vector2& a,
                                             const Vector2& b) const
{
	Vector2 ab = b - a;
	float len_sq = ab.squaredNorm();
	if (len_sq < 1e-10f)
		return (p - a).norm();
	float t = std::clamp((p - a).dot(ab) / len_sq, 0.0f, 1.0f);
	Vector2 closest = a + t * ab;
	return (p - closest).norm();
}

bool VenationGenerator::is_ancestor(const std::vector<VeinNode>& nodes, int node_idx,
                                    int potential_ancestor) const
{
	int current = node_idx;
	int steps = 0;
	while (current >= 0 && steps < static_cast<int>(nodes.size()))
	{
		if (current == potential_ancestor)
			return true;
		current = nodes[current].parent;
		steps++;
	}
	return false;
}

void VenationGenerator::compute_pipe_widths(std::vector<VeinNode>& nodes)
{
	if (nodes.empty())
		return;

	// Count children for each node
	std::vector<int> child_count(nodes.size(), 0);
	for (size_t i = 1; i < nodes.size(); ++i)
	{
		if (nodes[i].parent >= 0)
			child_count[nodes[i].parent]++;
	}

	// Initialize: tips get width 1.0, internal nodes start at 0
	for (size_t i = 0; i < nodes.size(); ++i)
	{
		nodes[i].width = (child_count[i] == 0) ? 1.0f : 0.0f;
	}

	// Propagate from tips to root (nodes are ordered parent-before-child)
	for (int i = static_cast<int>(nodes.size()) - 1; i >= 0; --i)
	{
		if (nodes[i].parent >= 0)
		{
			nodes[nodes[i].parent].width += nodes[i].width;
		}
	}

	// Apply sqrt for pipe model
	for (auto& node : nodes)
	{
		node.width = std::sqrt(std::max(node.width, 1.0f));
	}
}

// =========================================================================
// VenationGenerator core algorithm
// =========================================================================

std::vector<VenationGenerator::AuxinSource>
VenationGenerator::generate_auxin_sources(const std::vector<Vector2>& contour,
                                          std::mt19937& rng) const
{
	// Compute contour bounding box
	Vector2 min_b = contour[0], max_b = contour[0];
	for (const auto& pt : contour)
	{
		min_b.x() = std::min(min_b.x(), pt.x());
		min_b.y() = std::min(min_b.y(), pt.y());
		max_b.x() = std::max(max_b.x(), pt.x());
		max_b.y() = std::max(max_b.y(), pt.y());
	}

	// Determine number of auxin sources from density and area
	float area = compute_contour_area(contour);
	int num_auxins = static_cast<int>(vein_density * area);
	num_auxins = std::max(0, std::min(num_auxins, 5000));

	std::vector<AuxinSource> auxins;
	if (num_auxins == 0)
		return auxins;

	auxins.reserve(num_auxins);

	std::uniform_real_distribution<float> dist_x(min_b.x(), max_b.x());
	std::uniform_real_distribution<float> dist_y(min_b.y(), max_b.y());

	int attempts = 0;
	while (static_cast<int>(auxins.size()) < num_auxins && attempts < num_auxins * 10)
	{
		Vector2 pos(dist_x(rng), dist_y(rng));
		if (point_in_contour(pos, contour))
		{
			auxins.push_back({pos, true});
		}
		attempts++;
	}

	return auxins;
}

std::vector<VeinNode> VenationGenerator::generate_veins(const std::vector<Vector2>& contour)
{
	if (contour.size() < 3 || vein_density <= 0.0f)
		return {};

	std::mt19937 rng(seed);
	auto auxins = generate_auxin_sources(contour, rng);
	if (auxins.empty())
		return {};

	// Compute contour bounding box for root placement and spatial hash
	Vector2 min_b = contour[0], max_b = contour[0];
	for (const auto& pt : contour)
	{
		min_b.x() = std::min(min_b.x(), pt.x());
		min_b.y() = std::min(min_b.y(), pt.y());
		max_b.x() = std::max(max_b.x(), pt.x());
		max_b.y() = std::max(max_b.y(), pt.y());
	}

	// Initialize vein network with root at leaf base (bottom center)
	std::vector<VeinNode> veins;
	Vector2 root_pos(0.0f, min_b.y() + (max_b.y() - min_b.y()) * 0.02f);

	// Ensure root is inside contour
	if (!point_in_contour(root_pos, contour))
	{
		// Find contour point closest to bottom center
		float best_dist = std::numeric_limits<float>::max();
		Vector2 target(0.0f, min_b.y());
		for (const auto& pt : contour)
		{
			float d = (pt - target).squaredNorm();
			if (d < best_dist)
			{
				best_dist = d;
				root_pos = pt;
			}
		}
		// Move slightly inside toward centroid
		Vector2 centroid(0.0f, 0.0f);
		for (const auto& pt : contour)
			centroid += pt;
		centroid /= static_cast<float>(contour.size());
		root_pos = root_pos + (centroid - root_pos).normalized() * growth_step_size;
	}

	VeinNode root;
	root.position = root_pos;
	root.parent = -1;
	veins.push_back(root);

	// Build vein spatial hash
	Vector2 pad(attraction_distance, attraction_distance);
	SpatialHash2D vein_hash(attraction_distance, min_b - pad, max_b + pad);
	vein_hash.insert(0, root_pos);

	// Effective kill distance: reduced for CLOSED type to allow denser growth
	float effective_kill = (type == VenationType::Closed) ? kill_distance * 0.5f : kill_distance;

	// Runions iterations
	for (int iter = 0; iter < max_iterations; ++iter)
	{
		// For each vein node with attracted auxins, compute growth direction
		std::vector<Vector2> growth_dirs(veins.size(), Vector2(0.0f, 0.0f));
		std::vector<int> growth_counts(veins.size(), 0);

		int active_auxins = 0;

		for (const auto& auxin : auxins)
		{
			if (!auxin.active)
				continue;
			active_auxins++;

			auto candidates = vein_hash.query_radius(auxin.position, attraction_distance);
			if (candidates.empty())
				continue;

			// Find nearest vein node
			int nearest = -1;
			float nearest_dist_sq = std::numeric_limits<float>::max();
			for (int vid : candidates)
			{
				float d = (veins[vid].position - auxin.position).squaredNorm();
				if (d < nearest_dist_sq)
				{
					nearest_dist_sq = d;
					nearest = vid;
				}
			}

			if (nearest >= 0)
			{
				Vector2 dir = auxin.position - veins[nearest].position;
				float len = dir.norm();
				if (len > 1e-10f)
				{
					growth_dirs[nearest] += dir / len;
					growth_counts[nearest]++;
				}
			}
		}

		if (active_auxins == 0)
			break;

		// Grow new vein nodes
		bool any_grew = false;
		int old_size = static_cast<int>(veins.size());

		for (int vi = 0; vi < old_size; ++vi)
		{
			if (growth_counts[vi] == 0)
				continue;

			Vector2 avg_dir = growth_dirs[vi] / static_cast<float>(growth_counts[vi]);
			float len = avg_dir.norm();
			if (len < 1e-10f)
				continue;
			avg_dir /= len;

			Vector2 new_pos = veins[vi].position + avg_dir * growth_step_size;

			// Check new position is inside contour
			if (!point_in_contour(new_pos, contour))
				continue;

			// For CLOSED type: check if close to existing non-ancestor vein (form loops)
			if (type == VenationType::Closed)
			{
				auto nearby = vein_hash.query_radius(new_pos, growth_step_size * 3.0f);
				bool merged = false;
				for (int nid : nearby)
				{
					if (nid == vi)
						continue;
					if (is_ancestor(veins, vi, nid))
						continue;
					if (is_ancestor(veins, nid, vi))
						continue;
					// Close to existing non-ancestor vein - create loop connection
					VeinNode loop_node;
					loop_node.position = new_pos;
					loop_node.parent = nid;
					int new_idx = static_cast<int>(veins.size());
					veins.push_back(loop_node);
					vein_hash.insert(new_idx, new_pos);
					merged = true;
					any_grew = true;
					break;
				}
				if (merged)
					continue;
			}

			VeinNode new_node;
			new_node.position = new_pos;
			new_node.parent = vi;
			int new_idx = static_cast<int>(veins.size());
			veins.push_back(new_node);
			vein_hash.insert(new_idx, new_pos);
			any_grew = true;
		}

		if (!any_grew)
			break;

		// Kill auxin sources within kill_distance of any new vein node
		float kill_sq = effective_kill * effective_kill;
		for (int vi = old_size; vi < static_cast<int>(veins.size()); ++vi)
		{
			for (auto& auxin : auxins)
			{
				if (!auxin.active)
					continue;
				float d = (auxin.position - veins[vi].position).squaredNorm();
				if (d <= kill_sq)
				{
					auxin.active = false;
				}
			}
		}
	}

	// Compute pipe model widths
	compute_pipe_widths(veins);

	return veins;
}

void VenationGenerator::compute_vein_distances(Mesh& mesh, const std::vector<VeinNode>& veins)
{
	if (veins.empty() || mesh.vertices.empty())
		return;

	auto& attr = mesh.add_attribute<float>("vein_distance");
	attr.data.resize(mesh.vertices.size());

	for (size_t vi = 0; vi < mesh.vertices.size(); ++vi)
	{
		Vector2 vpos(mesh.vertices[vi].x(), mesh.vertices[vi].y());
		float min_dist = std::numeric_limits<float>::max();

		// Check distance to each vein segment
		for (size_t ni = 0; ni < veins.size(); ++ni)
		{
			if (veins[ni].parent < 0)
			{
				// Root node: check point distance
				float d = (vpos - veins[ni].position).norm();
				min_dist = std::min(min_dist, d);
				continue;
			}
			float d =
			    distance_to_segment(vpos, veins[veins[ni].parent].position, veins[ni].position);
			min_dist = std::min(min_dist, d);
		}

		attr.data[vi] = min_dist;
	}
}

} // namespace Mtree

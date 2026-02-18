#pragma once
#include "../mesh/Mesh.hpp"
#include "LeafPresets.hpp"
#include <random>
#include <vector>

namespace Mtree
{

// 2D grid spatial hash for O(1) neighbor lookups in bounded domain
class SpatialHash2D
{
  public:
	struct Entry
	{
		int id;
		Vector2 position;
	};

	SpatialHash2D(float cell_size, const Vector2& min_bound, const Vector2& max_bound);

	void insert(int id, const Vector2& pos);
	std::vector<int> query_radius(const Vector2& center, float radius) const;
	void clear();

  private:
	float cell_size_;
	Vector2 min_bound_;
	int grid_width_ = 0;
	int grid_height_ = 0;
	std::vector<std::vector<Entry>> cells_;

	std::pair<int, int> to_cell(const Vector2& pos) const;
	int cell_index(int cx, int cy) const;
};

struct VeinNode
{
	Vector2 position;
	int parent = -1; // -1 = root node
	float width = 1.0f;
};

class VenationGenerator
{
  public:
	VenationType type = VenationType::Open;
	float vein_density = 800.0f;
	float kill_distance = 0.03f;
	float growth_step_size = 0.01f;
	float attraction_distance = 0.08f;
	int max_iterations = 300;
	int seed = 42;

	// Generate vein network within the contour boundary
	// Returns empty vector if contour has < 3 points or density is 0
	std::vector<VeinNode> generate_veins(const std::vector<Vector2>& contour);

	// Compute vein_distance float attribute on mesh
	// Each vertex gets distance to nearest vein segment
	void compute_vein_distances(Mesh& mesh, const std::vector<VeinNode>& veins);

  private:
	struct AuxinSource
	{
		Vector2 position;
		bool active = true;
	};

	std::vector<AuxinSource> generate_auxin_sources(const std::vector<Vector2>& contour,
	                                                std::mt19937& rng) const;
	bool point_in_contour(const Vector2& point, const std::vector<Vector2>& contour) const;
	float compute_contour_area(const std::vector<Vector2>& contour) const;
	void compute_pipe_widths(std::vector<VeinNode>& nodes);
	float distance_to_segment(const Vector2& p, const Vector2& a, const Vector2& b) const;
	bool is_ancestor(const std::vector<VeinNode>& nodes, int node_idx,
	                 int potential_ancestor) const;
};

} // namespace Mtree

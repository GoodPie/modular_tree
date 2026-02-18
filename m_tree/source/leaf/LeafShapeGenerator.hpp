#pragma once
#include "../mesh/Mesh.hpp"
#include "LeafPresets.hpp"
#include <random>
#include <vector>

namespace Mtree
{

class LeafShapeGenerator
{
  public:
	// Superformula parameters
	float m = 2.0f;
	float a = 1.0f;
	float b = 1.0f;
	float n1 = 3.0f;
	float n2 = 3.0f;
	float n3 = 3.0f;
	float aspect_ratio = 0.5f;

	// Margin parameters
	MarginType margin_type = MarginType::Entire;
	int tooth_count = 0;
	float tooth_depth = 0.1f;
	float tooth_sharpness = 0.5f;
	int asymmetry_seed = 0;

	// Venation parameters
	bool enable_venation = false;
	VenationType venation_type = VenationType::Open;
	float vein_density = 800.0f;
	float kill_distance = 0.03f;
	float attraction_distance = 0.08f;
	float growth_step_size = 0.01f;

	// Surface deformation
	float midrib_curvature = 0.0f;
	float cross_curvature = 0.0f;
	float vein_displacement = 0.0f;
	float edge_curl = 0.0f;

	// Resolution
	int contour_resolution = 64;
	int seed = 42;

	Mesh generate();

  private:
	std::vector<Vector2> sample_contour();
	std::vector<Vector2> apply_margin(const std::vector<Vector2>& contour);
	Mesh triangulate(const std::vector<Vector2>& contour);
	void apply_venation(Mesh& mesh, const std::vector<Vector2>& contour);
	void apply_deformation(Mesh& mesh, const std::vector<Vector2>& contour);
	void compute_uvs(Mesh& mesh, const std::vector<Vector2>& contour);

	struct BBox2D
	{
		float min_x, max_x, min_y, max_y, width, height, center_x;
	};
	BBox2D compute_contour_bbox(const std::vector<Vector2>& contour) const;

	float superformula_radius(float theta, float effective_n1) const;
};

} // namespace Mtree

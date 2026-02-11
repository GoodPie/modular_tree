#pragma once
#include <string>

namespace Mtree
{

enum class MarginType
{
	Entire = 0,
	Serrate = 1,
	Dentate = 2,
	Crenate = 3,
	Lobed = 4
};

enum class VenationType
{
	Open = 0,
	Closed = 1
};

struct LeafPreset
{
	std::string name;
	// Superformula
	float m, a, b, n1, n2, n3, aspect_ratio;
	// Margin
	MarginType margin_type;
	int tooth_count;
	float tooth_depth, tooth_sharpness;
	// Venation
	bool enable_venation;
	VenationType venation_type;
	float vein_density, kill_distance;
	// Deformation
	float midrib_curvature, cross_curvature, edge_curl;
};

} // namespace Mtree

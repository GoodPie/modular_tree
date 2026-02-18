#pragma once
#include <string>
#include <vector>

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
	float m = 2.0f;
	float a = 1.0f;
	float b = 1.0f;
	float n1 = 3.0f;
	float n2 = 3.0f;
	float n3 = 3.0f;
	float aspect_ratio = 0.5f;
	// Margin
	MarginType margin_type = MarginType::Entire;
	int tooth_count = 0;
	float tooth_depth = 0.1f;
	float tooth_sharpness = 0.5f;
	// Venation
	bool enable_venation = false;
	VenationType venation_type = VenationType::Open;
	float vein_density = 800.0f;
	float kill_distance = 0.03f;
	float attraction_distance = 0.08f;
	// Deformation
	float midrib_curvature = 0.0f;
	float cross_curvature = 0.0f;
	float vein_displacement = 0.0f;
	float edge_curl = 0.0f;
};

const LeafPreset* get_leaf_preset(const std::string& name);
std::vector<std::string> get_leaf_preset_names();

} // namespace Mtree

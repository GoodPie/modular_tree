#pragma once
#include <Eigen/Core>
#include <variant>

namespace Mtree
{
using Vector3 = Eigen::Vector3f;

struct BranchGrowthInfo
{
	float desired_length;
	float origin_radius;
	Vector3 position;
	float current_length = 0;
	float deviation_from_rest_pose = 0;
	float cumulated_weight = 0;
	float age = 0;
	bool inactive = false;
};

struct BioNodeInfo
{
	enum class NodeType
	{
		Meristem,
		Branch,
		Cut,
		Ignored,
		Dormant,
		Flower
	} type;
	float branch_weight = 0;
	Vector3 center_of_mass;
	Vector3 absolute_position;
	float vigor_ratio = 1;
	float vigor = 0;
	int age = 0;
	float philotaxis_angle = 0;
	bool is_lateral = false;

	BioNodeInfo(NodeType type = NodeType::Ignored, int age = 0, float philotaxis_angle = 0,
	            bool is_lateral = false)
	    : type(type), age(age), philotaxis_angle(philotaxis_angle), is_lateral(is_lateral)
	{
	}
};

using GrowthInfo = std::variant<std::monostate, BranchGrowthInfo, BioNodeInfo>;

} // namespace Mtree

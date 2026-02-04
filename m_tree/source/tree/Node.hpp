#pragma once
#include "GrowthInfo.hpp"
#include <Eigen/Core>
#include <memory>
#include <vector>

namespace Mtree
{
using Vector3 = Eigen::Vector3f;

struct NodeChild;

class Node
{
  public:
	std::vector<std::shared_ptr<NodeChild>> children;
	Vector3 direction;
	Vector3 tangent;
	float length;
	float radius;
	int creator_id = 0;
	GrowthInfo growthInfo;

	bool is_leaf() const;

	Node(Vector3 direction, Vector3 parent_tangent, float length, float radius, int creator_id);
};

struct NodeChild
{
	Node node;
	float position_in_parent;
};

struct Stem
{
	Node node;
	Vector3 position;
};
} // namespace Mtree

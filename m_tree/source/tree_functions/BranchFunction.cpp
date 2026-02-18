#include <iostream>
#include <numbers>
#include <queue>
#include <ranges>

#include "BranchFunction.hpp"
#include "source/utilities/GeometryUtilities.hpp"
#include "source/utilities/NodeUtilities.hpp"

using namespace Mtree;

namespace
{
constexpr float EPSILON = 0.001f;

void update_positions_rec(Node& node, const Vector3& position)
{
	auto& info = std::get<BranchGrowthInfo>(node.growthInfo);
	info.position = position;

	for (auto& child : node.children)
	{
		Vector3 child_position =
		    position + node.direction * node.length * child->position_in_parent;
		update_positions_rec(child->node, child_position);
	}
}

bool avoid_floor(const Vector3& node_position, Vector3& node_direction,
                 float parent_length) // return true if branch should be terminated
{
	if (node_direction.z() < 0)
	{
		node_direction[2] -= node_direction[2] * 2 / (2 + node_position.z());
	}
	return (node_position + node_direction).z() * parent_length * 4 <
	       0; // is node heading to floor too fast
}

Vector3 get_main_child_direction(Node& parent, const Vector3& parent_position,
                                 const float up_attraction, const float flatness,
                                 const float randomness, const float resolution,
                                 bool& should_terminate)
{
	Vector3 random_dir =
	    Geometry::random_vec(flatness).normalized() + Vector3{0, 0, 1} * up_attraction;
	Vector3 child_direction = parent.direction + random_dir * randomness / resolution;
	should_terminate = avoid_floor(parent_position, child_direction, parent.length);
	child_direction.normalize();
	return child_direction;
}

Vector3 get_split_direction(const Node& parent, const Vector3& parent_position,
                            const float up_attraction, const float flatness, const float resolution,
                            const float angle)
{
	Vector3 child_direction = Geometry::random_vec();
	child_direction =
	    child_direction.cross(parent.direction) + Vector3{0, 0, 1} * up_attraction * flatness;
	Vector3 flat_normal =
	    Vector3{0, 0, 1}.cross(parent.direction).cross(parent.direction).normalized();
	child_direction -= child_direction.dot(flat_normal) * flatness * flat_normal;
	avoid_floor(parent_position, child_direction, parent.length);
	child_direction = Geometry::lerp(parent.direction, child_direction,
	                                 angle / 90); // TODO use slerp for correct angle
	child_direction.normalize();
	return child_direction;
}

void mark_inactive(Node& node)
{
	auto& info = std::get<BranchGrowthInfo>(node.growthInfo);
	info.inactive = true;
}

bool propagate_inactive_rec(Node& node)
{
	auto* info = std::get_if<BranchGrowthInfo>(&node.growthInfo);

	if (node.children.size() == 0 || info->inactive)
		return info->inactive;

	bool inactive = std::ranges::any_of(node.children, [](const auto& child)
	                                    { return propagate_inactive_rec(child->node); });
	info->inactive = inactive;
	return inactive;
}
} // namespace

namespace Mtree
{
void BranchFunction::apply_gravity_to_branch(Node& branch_origin)
{
	propagate_inactive_rec(branch_origin);
	update_weight_rec(branch_origin);
	apply_gravity_rec(branch_origin, Eigen::AngleAxisf::Identity());
	auto& info = std::get<BranchGrowthInfo>(branch_origin.growthInfo);
	update_positions_rec(branch_origin, info.position);
}

void BranchFunction::apply_gravity_rec(Node& node, Eigen::AngleAxisf curent_rotation)
{
	auto& info = std::get<BranchGrowthInfo>(node.growthInfo);
	if (!info.inactive || true)
	{
		float horizontality = 1 - std::abs(node.direction.z());
		info.age += 1 / resolution;
		float displacement = horizontality * std::pow(info.cumulated_weight, .5f) *
		                     gravity->strength / resolution / resolution / 1000 / (1 + info.age);
		displacement *=
		    std::exp(-std::abs(info.deviation_from_rest_pose / resolution * gravity->stiffness));
		info.deviation_from_rest_pose += displacement;

		Vector3 tangent = node.direction.cross(Vector3{0, 0, -1}).normalized();
		Eigen::AngleAxisf rot{displacement, tangent};
		curent_rotation = rot * curent_rotation;

		node.direction = curent_rotation * node.direction;
	}

	for (auto& child : node.children)
	{
		apply_gravity_rec(child->node, curent_rotation);
	}
}

void BranchFunction::update_weight_rec(Node& node)
{
	float node_weight = node.length;
	for (auto& child : node.children)
	{
		update_weight_rec(child->node);
		auto& child_info = std::get<BranchGrowthInfo>(child->node.growthInfo);
		node_weight += child_info.cumulated_weight;
	}

	auto* info = std::get_if<BranchGrowthInfo>(&node.growthInfo);
	info->cumulated_weight = node_weight;
}

// grow extremity by one level (add one or more children)
void BranchFunction::grow_node_once(Node& node, const int id,
                                    std::queue<std::reference_wrapper<Node>>& results)
{
	bool break_branch = rand_gen.get_0_1() * resolution < break_chance;
	if (break_branch)
	{
		mark_inactive(node);
		return;
	}

	auto& info = std::get<BranchGrowthInfo>(node.growthInfo);
	float factor_in_branch = info.current_length / info.desired_length;

	float child_radius =
	    Geometry::lerp(info.origin_radius, info.origin_radius * end_radius, factor_in_branch);
	float child_length = std::min(1 / resolution, info.desired_length - info.current_length);
	bool should_terminate;
	Vector3 child_direction = get_main_child_direction(
	    node, info.position, gravity->up_attraction, flatness, randomness.execute(factor_in_branch),
	    resolution, should_terminate);

	if (should_terminate)
	{
		mark_inactive(node);
		return;
	}

	NodeChild child{.node = Node{child_direction, node.tangent, child_length, child_radius, id},
	                .position_in_parent = 1};
	node.children.push_back(std::make_shared<NodeChild>(std::move(child)));
	auto& child_node = node.children.back()->node;

	float current_length = info.current_length + child_length;
	Vector3 child_position = info.position + child_direction * child_length;
	child_node.growthInfo = BranchGrowthInfo{.desired_length = info.desired_length,
	                                         .origin_radius = info.origin_radius,
	                                         .position = child_position,
	                                         .current_length = current_length};
	if (current_length < info.desired_length)
	{
		results.push(std::ref<Node>(child_node));
	}

	bool do_split = rand_gen.get_0_1() * resolution <
	                split->probability; // should the node split into two children
	if (do_split)
	{
		Vector3 split_child_direction = get_split_direction(
		    node, info.position, gravity->up_attraction, flatness, resolution, split->angle);
		float split_child_radius = node.radius * split->radius;

		NodeChild child{
		    .node = Node{split_child_direction, node.tangent, child_length, split_child_radius, id},
		    .position_in_parent = rand_gen.get_0_1()};
		node.children.push_back(std::make_shared<NodeChild>(std::move(child)));
		auto& child_node = node.children.back()->node;

		Vector3 split_child_position = info.position + split_child_direction * child_length;
		child_node.growthInfo =
		    BranchGrowthInfo{.desired_length = info.desired_length,
		                     .origin_radius = info.origin_radius * split->radius,
		                     .position = split_child_position,
		                     .current_length = current_length};
		if (current_length < info.desired_length)
		{
			results.push(std::ref<Node>(child_node));
		}
	}
}

void BranchFunction::grow_origins(std::vector<std::reference_wrapper<Node>>& origins, const int id)
{
	std::queue<std::reference_wrapper<Node>> extremities;
	for (auto& node_ref : origins)
	{
		extremities.push(node_ref);
	}
	int batch_size = extremities.size();
	while (!extremities.empty())
	{
		if (batch_size == 0)
		{
			batch_size = extremities.size();
			for (auto& node_ref : origins)
			{
				apply_gravity_to_branch(node_ref.get());
			}
		}
		auto& node = extremities.front().get();
		extremities.pop();
		grow_node_once(node, id, extremities);
		batch_size--;
	}
}

// get the origins of the branches that will be created.
// origins are created from the nodes made by the parent TreeFunction
std::vector<std::reference_wrapper<Node>>
BranchFunction::get_origins(std::vector<Stem>& stems, const int id, const int parent_id)
{
	// get all nodes created by the parent TreeFunction, organised by branch
	NodeUtilities::BranchSelection selection = NodeUtilities::select_from_tree(stems, parent_id);
	std::vector<std::reference_wrapper<Node>> origins;

	// Calculate effective crown height for shape envelope
	float effective_crown_height = crown->height;
	if (effective_crown_height < 0 && parent_id == 0 && stems.size() > 0)
	{
		effective_crown_height = NodeUtilities::get_branch_length(stems[0].node);
	}
	float crown_start_z = effective_crown_height * crown->base_size;
	float crown_zone_height = effective_crown_height * (1.0f - crown->base_size);

	float origins_dist =
	    1 / (distribution->density + .001); // distance between two consecutive origins

	for (auto& branch : selection) // parent branches
	{
		if (branch.size() == 0)
		{
			continue;
		}

		float branch_length = NodeUtilities::get_branch_length(*branch[0].node);
		float absolute_start =
		    distribution->start *
		    branch_length; // the length at which we can start adding new branch origins
		float absolute_end = distribution->end *
		                     branch_length; // the length at which we stop adding new branch origins
		float current_length = 0;
		float dist_to_next_origin = absolute_start;
		Vector3 tangent = Geometry::get_orthogonal_vector(branch[0].node->direction);

		for (size_t node_index = 0; node_index < branch.size(); node_index++)
		{
			auto& node = *branch[node_index].node;
			Vector3 node_position = branch[node_index].node_position;
			if (node.children.size() ==
			    0) // cant add children since it would "continue" the branch and not ad a split
			{
				continue;
			}
			auto rot =
			    Eigen::AngleAxisf((distribution->phillotaxis + (rand_gen.get_0_1() - .5) * 2) /
			                          180 * std::numbers::pi_v<float>,
			                      node.direction);
			if (dist_to_next_origin > node.length)
			{
				dist_to_next_origin -= node.length;
				current_length += node.length;
			}
			else
			{
				float remaining_node_length = node.length - dist_to_next_origin;
				current_length += dist_to_next_origin;
				int origins_to_create = remaining_node_length / origins_dist +
				                        1; // number of origins to create on the node
				float position_in_parent =
				    dist_to_next_origin /
				    node.length; // position of the first origin within the node
				float position_in_parent_step =
				    origins_dist / node.length; // relative distance between origins within the node

				for (int i = 0; i < origins_to_create; i++)
				{
					if (current_length > absolute_end)
					{
						break;
					}
					float factor = (current_length - absolute_start) /
					               std::max(0.001f, absolute_end - absolute_start);
					tangent = rot * tangent;
					Geometry::project_on_plane(tangent, node.direction);
					tangent.normalize();
					float child_radius = node.radius * start_radius.execute(factor);
					float branch_length = length.execute(factor);
					float effective_start_angle = start_angle.execute(factor);

					// Calculate height-based modifications for crown shape and angle
					bool needs_height_calc =
					    crown_zone_height > EPSILON && (crown->shape != CrownShape::Cylindrical ||
					                                    std::abs(crown->angle_variation) > EPSILON);

					if (needs_height_calc)
					{
						float branch_z =
						    (node_position + node.direction * node.length * position_in_parent).z();

						if (branch_z >= crown_start_z)
						{
							// Ratio goes from 1.0 at crown base to 0.0 at top, matching Weber &
							// Penn paper convention where ratio represents "distance from top"
							float height_ratio = 1.0f - std::min(1.0f, (branch_z - crown_start_z) /
							                                               crown_zone_height);

							// Crown shape length multiplier
							if (crown->shape != CrownShape::Cylindrical)
							{
								branch_length *=
								    CrownShapeUtils::get_shape_ratio(crown->shape, height_ratio);
							}

							// Height-based angle variation (always uses Conical per W&P paper)
							if (std::abs(crown->angle_variation) > EPSILON)
							{
								float shape_ratio = CrownShapeUtils::get_shape_ratio(
								    CrownShape::Conical, height_ratio);
								float angle_offset =
								    crown->angle_variation * (1.0f - 2.0f * shape_ratio);
								effective_start_angle =
								    std::clamp(effective_start_angle + angle_offset, 0.0f, 180.0f);
							}
						}
					}

					Vector3 child_direction =
					    Geometry::lerp(node.direction, tangent, effective_start_angle / 90);
					child_direction.normalize();

					float node_length = std::min(branch_length, 1 / (resolution + 0.001f));
					NodeChild child{
					    Node{child_direction, node.tangent, node_length, child_radius, id},
					    position_in_parent};
					node.children.push_back(std::make_shared<NodeChild>(std::move(child)));
					auto& child_node = node.children.back()->node;
					Vector3 child_position =
					    node_position + node.direction * node.length * position_in_parent;
					child_node.growthInfo =
					    BranchGrowthInfo{.desired_length = branch_length - node_length,
					                     .origin_radius = child_radius,
					                     .position = child_position,
					                     .current_length = child_node.length};

					if (branch_length - node_length > 1e-3)
						origins.push_back(std::ref(child_node));
					position_in_parent += position_in_parent_step;
					if (i > 0)
					{
						current_length += origins_dist;
					}
				}
				remaining_node_length =
				    (remaining_node_length - (origins_to_create - 1) * origins_dist);
				dist_to_next_origin = origins_dist - remaining_node_length;
			}
		}
	}
	return origins;
}

void BranchFunction::execute(std::vector<Stem>& stems, int id, int parent_id)
{
	rand_gen.set_seed(seed);
	auto origins = get_origins(stems, id, parent_id);
	grow_origins(origins, id);
	execute_children(stems, id);
}
} // namespace Mtree

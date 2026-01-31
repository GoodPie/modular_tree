#pragma once
#include "GrowthFunction.hpp"
#include "./base_types/TreeFunction.hpp"
#include "source/utilities/GeometryUtilities.hpp"
#include "source/utilities/NodeUtilities.hpp"
#include <Eigen/Geometry>
#include <iostream>
#include <math.h>
#include <vector>

namespace Mtree
{
void setup_growth_information_rec(Node& node)
{
	node.growthInfo =
	    std::make_unique<BioNodeInfo>(node.children.size() == 0 ? BioNodeInfo::NodeType::Meristem
	                                                            : BioNodeInfo::NodeType::Ignored);
	for (auto& child : node.children)
		setup_growth_information_rec(child->node);
}

// get total amount of energy from the node and its descendance, and assign for each node the
// realtive amount of energy it receive
float GrowthFunction::update_vigor_ratio_rec(Node& node)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);
	if (info.type == BioNodeInfo::NodeType::Meristem)
	{
		return 1;
	}
	else if (info.type == BioNodeInfo::NodeType::Dormant)
	{
		// Dormant buds request less energy (suppressed by apical dominance)
		info.vigor_ratio = 0.3f;
		return 0.3f;
	}
	else if (info.type == BioNodeInfo::NodeType::Branch ||
	         info.type == BioNodeInfo::NodeType::Ignored)
	{
		float light_flux = update_vigor_ratio_rec(node.children[0]->node);
		float vigor_ratio = 1;
		for (size_t i = 1; i < node.children.size(); i++)
		{
			float child_flux = update_vigor_ratio_rec(node.children[i]->node);
			float t = apical_dominance;
			vigor_ratio = (t * light_flux) / (t * light_flux + (1 - t) * child_flux + .001f);
			static_cast<BioNodeInfo*>(node.children[i]->node.growthInfo.get())->vigor_ratio =
			    1 - vigor_ratio;
			light_flux += child_flux;
		}
		static_cast<BioNodeInfo*>(node.children[0]->node.growthInfo.get())->vigor_ratio =
		    vigor_ratio;
		return light_flux;
	}
	else
	{
		info.vigor_ratio = 0;
		return 0;
	}
}

// update the amount of energy available to a node
void GrowthFunction::update_vigor_rec(Node& node, float vigor)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);
	info.vigor = vigor;
	for (auto& child : node.children)
	{
		float child_vigor =
		    static_cast<BioNodeInfo*>(child->node.growthInfo.get())->vigor_ratio * vigor;
		update_vigor_rec(child->node, child_vigor);
	}
}

// apply rules on the node based on the energy available to it
void GrowthFunction::simulate_growth_rec(Node& node, int id)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);
	bool primary_growth =
	    info.type == BioNodeInfo::NodeType::Meristem && info.vigor > grow_threshold;
	bool secondary_growth =
	    info.vigor > grow_threshold &&
	    info.type != BioNodeInfo::NodeType::Ignored; // Todo : should be another parameter
	bool split = info.type == BioNodeInfo::NodeType::Meristem && info.vigor > split_threshold;
	bool cut = info.type == BioNodeInfo::NodeType::Meristem && info.vigor < cut_threshold;
	int child_count = node.children.size();
	if (cut)
	{
		info.type = BioNodeInfo::NodeType::Cut;
		return;
	}
	info.age++;
	if (secondary_growth)
	{
		node.radius = (1 - std::exp(-info.age * .01f) + .01f) * .5;
	}
	if (primary_growth)
	{
		Vector3 child_direction =
		    node.direction + Vector3{0, 0, 1} * gravitropism + Geometry::random_vec() * randomness;
		child_direction.normalize();
		float child_radius = node.radius;
		float child_length = branch_length * (info.vigor + .1f);
		NodeChild child =
		    NodeChild{Node{child_direction, node.tangent, branch_length, child_radius, id}, 1};
		float child_angle =
		    split ? info.philotaxis_angle + philotaxis_angle : info.philotaxis_angle;
		child.node.growthInfo =
		    std::make_unique<BioNodeInfo>(BioNodeInfo::NodeType::Meristem, 0, child_angle);
		node.children.push_back(std::make_shared<NodeChild>(std::move(child)));
		info.type = BioNodeInfo::NodeType::Branch;
	}
	if (split)
	{
		info.philotaxis_angle += philotaxis_angle;
		Vector3 tangent{std::cos(info.philotaxis_angle), std::sin(info.philotaxis_angle), 0};
		tangent = Geometry::get_look_at_rot(node.direction) * tangent;
		Vector3 child_direction = Geometry::lerp(node.direction, tangent, split_angle / 90);
		child_direction.normalize();
		float child_radius = node.radius;
		float child_length = branch_length * (info.vigor + .1f);
		NodeChild child =
		    NodeChild{Node{child_direction, node.tangent, branch_length, child_radius, id}, 1};
		child.node.growthInfo = std::make_unique<BioNodeInfo>(BioNodeInfo::NodeType::Meristem);
		node.children.push_back(std::make_shared<NodeChild>(std::move(child)));
		info.type = BioNodeInfo::NodeType::Branch;
	}
	for (size_t i = 0; i < child_count; i++)
	{
		simulate_growth_rec(node.children[i]->node, id);
	}
}

void GrowthFunction::get_weight_rec(Node& node)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);
	for (auto& child : node.children)
	{
		get_weight_rec(child->node);
	}
	float segment_weight = node.length * node.radius * node.radius;
	Vector3 center_of_mass =
	    (info.absolute_position + node.direction * node.length / 2) * segment_weight;
	float total_weight = segment_weight;
	for (auto& child : node.children)
	{
		BioNodeInfo& child_info = static_cast<BioNodeInfo&>(*child->node.growthInfo);
		center_of_mass += child_info.center_of_mass * child_info.branch_weight;
		total_weight += child_info.branch_weight;
	}
	center_of_mass /= total_weight;
	info.center_of_mass = center_of_mass;
	info.branch_weight = total_weight;
}

void GrowthFunction::apply_gravity_rec(Node& node, Eigen::Matrix3f curent_rotation)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);

	// Only apply gravity bending to growth nodes, not the original trunk
	if (info.type != BioNodeInfo::NodeType::Ignored)
	{
		Vector3 offset = (info.center_of_mass - info.absolute_position);
		offset[2] = 0;
		float lever_arm = offset.norm();
		float torque = info.branch_weight * lever_arm;
		float bendiness = std::exp(-(info.age / 2 + info.vigor));
		float angle = torque * bendiness * gravity_strength * 50;
		Vector3 tangent = node.direction.cross(Vector3{0, 0, -1});
		Eigen::Matrix3f rot;
		rot = Eigen::AngleAxis<float>(angle, tangent);
		curent_rotation = curent_rotation * rot;
		node.direction = curent_rotation * node.direction;
	}

	for (auto& child : node.children)
	{
		apply_gravity_rec(child->node, curent_rotation);
	}
}

void GrowthFunction::update_absolute_position_rec(Node& node, const Vector3& node_position)
{
	static_cast<BioNodeInfo*>(node.growthInfo.get())->absolute_position = node_position;
	for (auto& child : node.children)
	{
		Vector3 child_position =
		    node_position + node.direction * child->position_in_parent * node.length;
		update_absolute_position_rec(child->node, child_position);
	}
}

// Create dormant lateral buds along Ignored nodes
void GrowthFunction::create_lateral_buds_rec(Node& node, int id, Vector3 pos, float& dist_to_next,
                                             float& current_length, float total_length, float& philo)
{
	BioNodeInfo& info = static_cast<BioNodeInfo&>(*node.growthInfo);

	// Only create buds on Ignored nodes (part of the original trunk structure)
	if (info.type == BioNodeInfo::NodeType::Ignored && node.children.size() > 0)
	{
		float absolute_start = lateral_start * total_length;
		float absolute_end = lateral_end * total_length;
		float bud_spacing = 1.0f / (lateral_density + 0.001f);

		// Process this node segment
		if (current_length + node.length >= absolute_start && current_length < absolute_end)
		{
			float remaining = node.length;
			float pos_in_node = 0;

			// Skip to start zone if needed
			if (current_length < absolute_start)
			{
				float skip = absolute_start - current_length;
				remaining -= skip;
				pos_in_node = skip;
				dist_to_next = 0;
			}

			// Create buds along this node
			while (remaining > dist_to_next && current_length + pos_in_node < absolute_end)
			{
				pos_in_node += dist_to_next;
				remaining -= dist_to_next;

				// Create dormant bud
				philo += philotaxis_angle;
				Vector3 tangent{std::cos(philo), std::sin(philo), 0};
				tangent = Geometry::get_look_at_rot(node.direction) * tangent;
				Vector3 bud_direction = Geometry::lerp(node.direction, tangent, lateral_angle / 90.0f);
				bud_direction.normalize();

				float position_in_parent = pos_in_node / node.length;
				float child_radius = node.radius * 0.5f;
				float child_length = branch_length * 0.5f;

				NodeChild child{Node{bud_direction, node.tangent, child_length, child_radius, id},
				                position_in_parent};
				child.node.growthInfo =
				    std::make_unique<BioNodeInfo>(BioNodeInfo::NodeType::Dormant, 0, philo);
				node.children.push_back(std::make_shared<NodeChild>(std::move(child)));

				dist_to_next = bud_spacing;
			}

			dist_to_next -= remaining;
		}
		else if (current_length + node.length < absolute_start)
		{
			// Before start zone, just track distance
			dist_to_next = std::max(0.0f, absolute_start - (current_length + node.length));
		}
	}

	current_length += node.length;
	Vector3 child_pos = pos + node.direction * node.length;

	// Recurse into the main continuation (first child only for trunk)
	if (node.children.size() > 0)
	{
		create_lateral_buds_rec(node.children[0]->node, id, child_pos, dist_to_next, current_length,
		                        total_length, philo);
	}
}

void GrowthFunction::execute(std::vector<Stem>& stems, int id, int parent_id)
{
	rand_gen.set_seed(seed);

	for (Stem& stem : stems)
	{
		setup_growth_information_rec(stem.node);
	}

	// Create dormant lateral buds before growth iterations
	if (enable_lateral_branching)
	{
		for (Stem& stem : stems)
		{
			float total_length = NodeUtilities::get_branch_length(stem.node);
			float dist_to_next = lateral_start * total_length;
			float current_length = 0;
			float philo = 0;
			create_lateral_buds_rec(stem.node, id, stem.position, dist_to_next, current_length,
			                        total_length, philo);
		}
	}

	for (size_t i = 0; i < iterations; i++) // an iteration can be seen as a year of growth
	{
		for (Stem& stem : stems) // the energy is not shared between stems
		{
			float target_light_flux = 1 + std::pow((float)i, 1.5);
			float light_flux = update_vigor_ratio_rec(stem.node); // get total available energy

			if (target_light_flux > light_flux)
			{
				cut_threshold -= .1f;
				// grow_threshold -= .1f
			}
			else if (target_light_flux < light_flux)
			{
				cut_threshold += .1f;
			}
			// cut_threshold = (light_flux / target_light_flux) / 2;

			update_vigor_rec(stem.node, target_light_flux); // distribute the energy in each node
			simulate_growth_rec(stem.node, id);             // apply rules to the tree
			update_absolute_position_rec(stem.node, stem.position);
			get_weight_rec(stem.node);
			Eigen::Matrix3f rot;
			rot = rot.Identity();
			apply_gravity_rec(stem.node, rot);
		}
	}

	execute_children(stems, id);
}
} // namespace Mtree

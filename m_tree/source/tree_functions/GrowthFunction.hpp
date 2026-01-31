#pragma once
#include "source/tree_functions/base_types/TreeFunction.hpp"
#include <vector>

namespace Mtree
{
class GrowthFunction : public TreeFunction
{
  private:
	float update_vigor_ratio_rec(Node& node);
	void update_vigor_rec(Node& node, float vigor);
	void simulate_growth_rec(Node& node, int id);
	void get_weight_rec(Node& node);
	void apply_gravity_rec(Node& node, Eigen::Matrix3f curent_rotation);
	void update_absolute_position_rec(Node& node, const Vector3& node_position);

  public:
	int iterations = 5;
	int preview_iteration = -1;  // -1 means run all iterations
	float apical_dominance = .7f;
	float grow_threshold = .5f;
	float split_angle = 60;
	float branch_length = 1;
	float gravitropism = .1f;
	float randomness = .1f;
	float cut_threshold = .2f;
	float split_threshold = .7f;
	float gravity_strength = 1;

	float apical_control = .7f;
	float codominant_proba = .1f;
	int codominant_count = 2;
	float branch_angle = 60;
	float philotaxis_angle = 2.399f;
	float flower_threshold = .5f;

	float growth_delta = .1f;
	float flowering_delta = .1f;

	float root_flux = 5;

	// Lateral branching parameters
	bool enable_lateral_branching = true;
	float lateral_start = 0.1f;       // Start position along parent (0-1)
	float lateral_end = 0.9f;         // End position along parent (0-1)
	float lateral_density = 2.0f;     // Potential branch points per unit length
	float lateral_activation = 0.4f;  // Vigor threshold to activate dormant buds
	float lateral_angle = 45.0f;      // Initial angle from parent direction

	void execute(std::vector<Stem>& stems, int id, int parent_id) override;

  private:
	void create_lateral_buds_rec(Node& node, int id, Vector3 pos, float& dist_to_next,
	                             float& current_length, float total_length, float& philo);
};

class BioNodeInfo : public GrowthInfo
{
  public:
	enum class NodeType
	{
		Meristem,
		Branch,
		Cut,
		Ignored,
		Dormant
	} type;
	float branch_weight = 0;
	Vector3 center_of_mass;
	Vector3 absolute_position;
	float vigor_ratio = 1;
	float vigor = 0;
	int age = 0;
	float philotaxis_angle = 0;
	bool is_lateral = false;  // Track if this branch originated from a lateral bud

	BioNodeInfo(NodeType type, int age = 0, float philotaxis_angle = 0, bool is_lateral = false)
	{
		this->type = type;
		this->age = age;
		this->philotaxis_angle = philotaxis_angle;
		this->is_lateral = is_lateral;
	};
};

} // namespace Mtree

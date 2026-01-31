#pragma once
#include "./base_types/TreeFunction.hpp"
#include "CrownShape.hpp"
#include "source/tree_functions/base_types/Property.hpp"
#include "source/utilities/GeometryUtilities.hpp"
#include "source/utilities/NodeUtilities.hpp"
#include <memory>
#include <queue>
#include <vector>

namespace Mtree
{

// Parameter groupings for BranchFunction
struct SplitParams
{
    float radius = 0.9f;       // Radius multiplier for split branches (0 < x < 1)
    float angle = 45.0f;       // Angle between split branches (degrees)
    float probability = 0.5f;  // Probability of a branch splitting (0 < x)
};

struct GravityParams
{
    float strength = 10.0f;      // How much branches bend under their weight
    float stiffness = 0.1f;      // Resistance to bending from gravity
    float up_attraction = 0.25f; // Tendency to grow upward (negative values droop)
};

struct DistributionParams
{
    float start = 0.1f;          // Position along parent where branches start (0-1)
    float end = 1.0f;            // Position along parent where branches end (0-1)
    float density = 2.0f;        // Number of branches per unit length (0 < x)
    float phillotaxis = 137.5f;  // Spiral angle between branches (degrees)
};

class BranchFunction : public TreeFunction
{
  public:
	PropertyWrapper length{ConstantProperty(9)};        // x > 0
	PropertyWrapper start_radius{ConstantProperty(.4)}; // 0 > x > 1
	float end_radius = .05;
	float break_chance = .01; // 0 < x
	float resolution = 3;     // 0 < x
	PropertyWrapper randomness{ConstantProperty(.4)};
	float flatness = .5;                               // 0 < x  < 1
	PropertyWrapper start_angle{ConstantProperty(45)}; // -180 < x < 180

	// Parameter groupings
	std::shared_ptr<SplitParams> split = std::make_shared<SplitParams>();
	std::shared_ptr<GravityParams> gravity = std::make_shared<GravityParams>();
	std::shared_ptr<DistributionParams> distribution = std::make_shared<DistributionParams>();
	std::shared_ptr<CrownParams> crown = std::make_shared<CrownParams>();

	void execute(std::vector<Stem>& stems, int id, int parent_id) override;

	class BranchGrowthInfo : public GrowthInfo
	{
	  public:
		float desired_length;
		float current_length;
		float origin_radius;
		float cumulated_weight = 0;
		float deviation_from_rest_pose;
		float age = 0;
		bool inactive = false;
		Vector3 position;
		BranchGrowthInfo(float desired_length, float origin_radius, Vector3 position,
		                 float current_length = 0, float deviation = 0)
		    : desired_length(desired_length), origin_radius(origin_radius),
		      current_length(current_length), deviation_from_rest_pose(deviation),
		      position(position) {};
	};

  private:
	std::vector<std::reference_wrapper<Node>> get_origins(std::vector<Stem>& stems, const int id,
	                                                      const int parent_id);

	void grow_origins(std::vector<std::reference_wrapper<Node>>&, const int id);

	void grow_node_once(Node& node, const int id,
	                    std::queue<std::reference_wrapper<Node>>& results);

	void apply_gravity_to_branch(Node& node);

	void apply_gravity_rec(Node& node, Eigen::AngleAxisf previous_rotations);

	void update_weight_rec(Node& node);
};

} // namespace Mtree

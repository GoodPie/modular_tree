#pragma once
#include "../base_types/TreeMesher.hpp"
#include <string>
#include <tuple>

namespace Mtree
{

class ManifoldMesher : public TreeMesher
{
  public:
	struct AttributeNames
	{
		inline static const std::string smooth_amount = "smooth_amount";
		inline static const std::string radius = "radius";
		inline static const std::string direction = "direction";
		// Pivot Painter 2.0 attributes
		inline static const std::string stem_id = "stem_id";
		inline static const std::string hierarchy_depth = "hierarchy_depth";
		inline static const std::string pivot_position = "pivot_position";
		inline static const std::string branch_extent = "branch_extent";
	};

	int radial_resolution = 8;
	int smooth_iterations = 4;
	Mesh mesh_tree(Tree& tree) override;
};

} // namespace Mtree

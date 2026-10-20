#include "PipeRadiusFunction.hpp"
#include "source/utilities/GeometryUtilities.hpp"
#include <stdexcept>
namespace Mtree
{
void PipeRadiusFunction::update_radius_rec(Node& node)
{
	if (node.children.size() == 0)
	{
		node.radius = end_radius;
		return;
	}

	float total_children_radius = 0;
	for (auto& child : node.children)
	{
		update_radius_rec(child->node);
		total_children_radius += pow(child->node.radius, power);
	}
	node.radius = pow(total_children_radius, 1 / power) + constant_growth * node.length / 100;
}
void PipeRadiusFunction::execute(std::vector<Stem>& stems, int id, int parent_id)
{
	// negative radii give NaN in pow() or crash the mesher (#41)
	if (!(end_radius > 0) || !(constant_growth >= 0))
		throw std::invalid_argument("Pipe radius end radius must be > 0 and constant growth >= 0");
	rand_gen.set_seed(seed);

	for (auto& stem : stems)
	{
		update_radius_rec(stem.node);
	}
	execute_children(stems, id);
}

} // namespace Mtree

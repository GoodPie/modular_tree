#pragma once
#include "../mesh/Mesh.hpp"
#include <vector>

namespace Mtree
{

class LeafLODGenerator
{
  public:
	/// Generate a LOD 1 card mesh (4-vertex oriented quad) from a high-detail leaf.
	/// The card matches the axis-aligned bounding rectangle of the source mesh.
	/// UVs map to 0-1 range.
	Mesh generate_card(const Mesh& source);

	/// Generate a billboard cloud from a set of leaf instance positions.
	/// Produces num_planes intersecting quads for silhouette coverage.
	Mesh generate_billboard_cloud(const std::vector<Vector3>& positions, int num_planes = 3);

	/// Get evenly distributed directions on the upper hemisphere.
	/// Returns resolution * resolution unit vectors for octahedral impostor baking.
	std::vector<Vector3> get_impostor_view_directions(int resolution = 12);
};

} // namespace Mtree

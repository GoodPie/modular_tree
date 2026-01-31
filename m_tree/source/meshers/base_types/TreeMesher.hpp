#pragma once
#include "source/mesh/Mesh.hpp"
#include "source/tree/Tree.hpp"

namespace Mtree
{
class TreeMesher
{
  public:
	virtual ~TreeMesher() = default;

	virtual Mesh mesh_tree(Tree& tree) = 0;
};
} // namespace Mtree

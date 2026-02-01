#pragma once
#include "source/mesh/Mesh.hpp"
#include "source/tree/Tree.hpp"
#include <concepts>

namespace Mtree
{

template <typename T>
concept Mesher = requires(T& mesher, Tree& tree) {
	{ mesher.mesh_tree(tree) } -> std::same_as<Mesh>;
};

class TreeMesher
{
  public:
	virtual ~TreeMesher() = default;

	virtual Mesh mesh_tree(Tree& tree) = 0;
};
} // namespace Mtree

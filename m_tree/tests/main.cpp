#include <iostream>

#include "source/mesh/Mesh.hpp"
#include "source/tree/Tree.hpp"
#include "source/tree_functions/TrunkFunction.hpp"
#include "source/tree_functions/BranchFunction.hpp"
#include "source/tree_functions/GrowthFunction.hpp"
#include "source/meshers/splines_mesher/BasicMesher.hpp"
#include "source/meshers/manifold_mesher/ManifoldMesher.hpp"


using namespace Mtree;

int main()
{
    std::cout << "Testing BranchFunction (BranchGrowthInfo variant)..." << std::endl;

    // Test 1: BranchFunction uses BranchGrowthInfo
    {
        auto trunk = std::make_shared<TrunkFunction>();
        auto branch = std::make_shared<BranchFunction>();
        trunk->add_child(branch);
        branch->start_radius = ConstantProperty{1.5};
        Tree tree(trunk);
        tree.execute_functions();
        ManifoldMesher mesher;
        mesher.radial_resolution = 32;
        auto mesh = mesher.mesh_tree(tree);
        std::cout << "  Vertices: " << mesh.vertices.size() << std::endl;
    }

    std::cout << "Testing GrowthFunction (BioNodeInfo variant)..." << std::endl;

    // Test 2: GrowthFunction uses BioNodeInfo
    {
        auto trunk = std::make_shared<TrunkFunction>();
        auto growth = std::make_shared<GrowthFunction>();
        growth->iterations = 3;
        growth->enable_lateral_branching = true;
        trunk->add_child(growth);
        Tree tree(trunk);
        tree.execute_functions();
        ManifoldMesher mesher;
        mesher.radial_resolution = 16;
        auto mesh = mesher.mesh_tree(tree);
        std::cout << "  Vertices: " << mesh.vertices.size() << std::endl;
    }

    std::cout << "All tests passed!" << std::endl;
    return 0;
}

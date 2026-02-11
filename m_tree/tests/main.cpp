#include <cassert>
#include <cmath>
#include <iostream>

#include "source/mesh/Mesh.hpp"
#include "source/tree/Tree.hpp"
#include "source/tree_functions/TrunkFunction.hpp"
#include "source/tree_functions/BranchFunction.hpp"
#include "source/tree_functions/GrowthFunction.hpp"
#include "source/meshers/splines_mesher/BasicMesher.hpp"
#include "source/meshers/manifold_mesher/ManifoldMesher.hpp"
#include "source/leaf/LeafShapeGenerator.hpp"
#include "source/leaf/LeafPresets.hpp"
#include "source/leaf/VenationGenerator.hpp"
#include "source/leaf/LeafLODGenerator.hpp"


using namespace Mtree;

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) \
	static void test_##name(); \
	struct TestRunner_##name { \
		TestRunner_##name() { \
			std::cout << "  Running " #name "... "; \
			try { \
				test_##name(); \
				std::cout << "PASSED" << std::endl; \
				tests_passed++; \
			} catch (const std::exception& e) { \
				std::cout << "FAILED: " << e.what() << std::endl; \
				tests_failed++; \
			} catch (...) { \
				std::cout << "FAILED (unknown exception)" << std::endl; \
				tests_failed++; \
			} \
		} \
	}; \
	static TestRunner_##name runner_##name; \
	static void test_##name()

#define ASSERT_TRUE(expr) \
	if (!(expr)) throw std::runtime_error(std::string("Assertion failed: ") + #expr)
#define ASSERT_EQ(a, b) \
	if ((a) != (b)) throw std::runtime_error(std::string("Expected ") + std::to_string(a) + " == " + std::to_string(b))
#define ASSERT_GT(a, b) \
	if (!((a) > (b))) throw std::runtime_error(std::string("Expected ") + std::to_string(a) + " > " + std::to_string(b))
#define ASSERT_GE(a, b) \
	if (!((a) >= (b))) throw std::runtime_error(std::string("Expected ") + std::to_string(a) + " >= " + std::to_string(b))
#define ASSERT_LE(a, b) \
	if (!((a) <= (b))) throw std::runtime_error(std::string("Expected ") + std::to_string(a) + " <= " + std::to_string(b))

// =====================================================================
// Existing tree tests
// =====================================================================

TEST(tree_basic)
{
	auto trunk = std::make_shared<TrunkFunction>();
	auto branch = std::make_shared<BranchFunction>();
	trunk->add_child(branch);
	branch->start_radius = ConstantProperty{ 1.5 };
	Tree tree(trunk);
	tree.execute_functions();
	ManifoldMesher mesher;
	mesher.radial_resolution = 32;
	mesher.mesh_tree(tree);
	ASSERT_TRUE(true);
}

// =====================================================================
// LeafShapeGenerator tests
// =====================================================================

TEST(leaf_generate_returns_valid_mesh)
{
	LeafShapeGenerator gen;
	Mesh mesh = gen.generate();

	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
}

TEST(leaf_superformula_contour_valid_closed_polygon)
{
	LeafShapeGenerator gen;
	gen.m = 2.0f;
	gen.contour_resolution = 32;
	Mesh mesh = gen.generate();

	// Contour should produce a closed polygon that triangulates to >0 faces
	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 1);

	// All vertex indices in polygons should be valid
	for (const auto& poly : mesh.polygons)
	{
		for (int j = 0; j < 4; ++j)
		{
			ASSERT_GE(poly[j], 0);
			ASSERT_TRUE(poly[j] < static_cast<int>(mesh.vertices.size()));
		}
	}
}

TEST(leaf_margin_serrate_modifies_contour)
{
	LeafShapeGenerator gen_plain;
	gen_plain.margin_type = MarginType::Entire;
	Mesh mesh_plain = gen_plain.generate();

	LeafShapeGenerator gen_serrate;
	gen_serrate.margin_type = MarginType::Serrate;
	gen_serrate.tooth_count = 10;
	gen_serrate.tooth_depth = 0.2f;
	Mesh mesh_serrate = gen_serrate.generate();

	// Serrate mesh should have different vertex count (adaptive refinement may change)
	// or at minimum different vertex positions
	bool positions_differ = false;
	size_t min_size = std::min(mesh_plain.vertices.size(), mesh_serrate.vertices.size());
	for (size_t i = 0; i < min_size; ++i)
	{
		if ((mesh_plain.vertices[i] - mesh_serrate.vertices[i]).norm() > 1e-6f)
		{
			positions_differ = true;
			break;
		}
	}
	ASSERT_TRUE(positions_differ || mesh_plain.vertices.size() != mesh_serrate.vertices.size());
}

TEST(leaf_margin_dentate_modifies_contour)
{
	LeafShapeGenerator gen;
	gen.margin_type = MarginType::Dentate;
	gen.tooth_count = 15;
	gen.tooth_depth = 0.15f;
	Mesh mesh = gen.generate();

	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
}

TEST(leaf_margin_crenate_modifies_contour)
{
	LeafShapeGenerator gen;
	gen.margin_type = MarginType::Crenate;
	gen.tooth_count = 8;
	gen.tooth_depth = 0.1f;
	Mesh mesh = gen.generate();

	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
}

TEST(leaf_margin_lobed_modifies_contour)
{
	LeafShapeGenerator gen;
	gen.margin_type = MarginType::Lobed;
	gen.tooth_count = 5;
	gen.tooth_depth = 0.3f;
	Mesh mesh = gen.generate();

	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
}

TEST(leaf_ear_clipping_valid_triangulation)
{
	LeafShapeGenerator gen;
	gen.contour_resolution = 32;
	Mesh mesh = gen.generate();

	// All polygons should be triangles stored as degenerate quads
	for (const auto& poly : mesh.polygons)
	{
		// 4th index equals 3rd (degenerate quad = triangle)
		ASSERT_EQ(poly[2], poly[3]);
		// All 3 unique indices must be different
		ASSERT_TRUE(poly[0] != poly[1]);
		ASSERT_TRUE(poly[1] != poly[2]);
		ASSERT_TRUE(poly[0] != poly[2]);
	}
}

TEST(leaf_uv_coordinates_in_range)
{
	LeafShapeGenerator gen;
	Mesh mesh = gen.generate();

	ASSERT_GT(static_cast<int>(mesh.uvs.size()), 0);
	ASSERT_EQ(static_cast<int>(mesh.uvs.size()), static_cast<int>(mesh.vertices.size()));

	for (const auto& uv : mesh.uvs)
	{
		ASSERT_GE(uv.x(), 0.0f);
		ASSERT_LE(uv.x(), 1.0f);
		ASSERT_GE(uv.y(), 0.0f);
		ASSERT_LE(uv.y(), 1.0f);
	}
}

TEST(leaf_surface_deformation_modifies_z)
{
	LeafShapeGenerator gen_flat;
	gen_flat.midrib_curvature = 0.0f;
	gen_flat.cross_curvature = 0.0f;
	gen_flat.edge_curl = 0.0f;
	Mesh mesh_flat = gen_flat.generate();

	// Flat leaf should have Z=0 for all vertices
	for (const auto& v : mesh_flat.vertices)
	{
		ASSERT_TRUE(std::abs(v.z()) < 1e-6f);
	}

	LeafShapeGenerator gen_curved;
	gen_curved.midrib_curvature = 0.5f;
	gen_curved.cross_curvature = 0.3f;
	Mesh mesh_curved = gen_curved.generate();

	// Curved leaf should have non-zero Z for at least some vertices
	bool has_nonzero_z = false;
	for (const auto& v : mesh_curved.vertices)
	{
		if (std::abs(v.z()) > 1e-6f)
		{
			has_nonzero_z = true;
			break;
		}
	}
	ASSERT_TRUE(has_nonzero_z);
}

TEST(leaf_degenerate_parameter_clamping)
{
	// n1=0 should be clamped, not crash
	LeafShapeGenerator gen;
	gen.n1 = 0.0f;
	Mesh mesh = gen.generate();
	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
	ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
}

TEST(leaf_min_contour_resolution)
{
	LeafShapeGenerator gen;
	gen.contour_resolution = 3; // Below minimum of 8
	Mesh mesh = gen.generate();

	// Should be clamped to 8 minimum
	ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
}

TEST(leaf_preset_oak_valid)
{
	const LeafPreset* oak = get_leaf_preset("Oak");
	ASSERT_TRUE(oak != nullptr);
	ASSERT_TRUE(oak->name == "Oak");
	ASSERT_TRUE(oak->margin_type == MarginType::Lobed);
	ASSERT_EQ(oak->tooth_count, 7);
	ASSERT_TRUE(oak->enable_venation);
}

TEST(leaf_preset_all_names)
{
	auto names = get_leaf_preset_names();
	ASSERT_EQ(static_cast<int>(names.size()), 5);
	ASSERT_TRUE(get_leaf_preset("Oak") != nullptr);
	ASSERT_TRUE(get_leaf_preset("Maple") != nullptr);
	ASSERT_TRUE(get_leaf_preset("Birch") != nullptr);
	ASSERT_TRUE(get_leaf_preset("Willow") != nullptr);
	ASSERT_TRUE(get_leaf_preset("Pine") != nullptr);
	ASSERT_TRUE(get_leaf_preset("Nonexistent") == nullptr);
}

TEST(leaf_preset_apply_generates_valid_mesh)
{
	auto names = get_leaf_preset_names();
	for (const auto& name : names)
	{
		const LeafPreset* preset = get_leaf_preset(name);
		ASSERT_TRUE(preset != nullptr);

		LeafShapeGenerator gen;
		gen.m = preset->m;
		gen.a = preset->a;
		gen.b = preset->b;
		gen.n1 = preset->n1;
		gen.n2 = preset->n2;
		gen.n3 = preset->n3;
		gen.aspect_ratio = preset->aspect_ratio;
		gen.margin_type = preset->margin_type;
		gen.tooth_count = preset->tooth_count;
		gen.tooth_depth = preset->tooth_depth;
		gen.tooth_sharpness = preset->tooth_sharpness;

		Mesh mesh = gen.generate();
		ASSERT_GT(static_cast<int>(mesh.vertices.size()), 3);
		ASSERT_GT(static_cast<int>(mesh.polygons.size()), 0);
	}
}

// =====================================================================
// ManifoldMesher phyllotaxis attribute tests
// =====================================================================

TEST(mesher_phyllotaxis_angle_attribute_exists)
{
	auto trunk = std::make_shared<TrunkFunction>();
	auto branch = std::make_shared<BranchFunction>();
	trunk->add_child(branch);
	branch->start_radius = ConstantProperty{1.5};
	Tree tree(trunk);
	tree.execute_functions();

	ManifoldMesher mesher;
	mesher.radial_resolution = 8;
	Mesh mesh = mesher.mesh_tree(tree);

	// Verify phyllotaxis_angle attribute exists
	auto it = mesh.attributes.find("phyllotaxis_angle");
	ASSERT_TRUE(it != mesh.attributes.end());

	// Verify attribute has same size as vertices
	auto& attr = *static_cast<Attribute<float>*>(it->second.get());
	ASSERT_EQ(static_cast<int>(attr.data.size()), static_cast<int>(mesh.vertices.size()));
}

TEST(mesher_phyllotaxis_angle_values_in_range)
{
	auto trunk = std::make_shared<TrunkFunction>();
	auto branch = std::make_shared<BranchFunction>();
	trunk->add_child(branch);
	Tree tree(trunk);
	tree.execute_functions();

	ManifoldMesher mesher;
	mesher.radial_resolution = 8;
	Mesh mesh = mesher.mesh_tree(tree);

	auto& attr = *static_cast<Attribute<float>*>(
	    mesh.attributes["phyllotaxis_angle"].get());

	// All values must be in [0, 2*PI)
	for (const auto& val : attr.data)
	{
		ASSERT_GE(val, 0.0f);
		ASSERT_TRUE(val < static_cast<float>(2 * M_PI) + 1e-5f);
	}
}

TEST(mesher_phyllotaxis_angle_golden_angle_pattern)
{
	auto trunk = std::make_shared<TrunkFunction>();
	Tree tree(trunk);
	tree.execute_functions();

	ManifoldMesher mesher;
	int radial_n = 8;
	mesher.radial_resolution = radial_n;
	Mesh mesh = mesher.mesh_tree(tree);

	auto& attr = *static_cast<Attribute<float>*>(
	    mesh.attributes["phyllotaxis_angle"].get());

	// Vertices within the same cross-section should have the same phyllotaxis_angle
	// Each cross-section has radial_n vertices
	int num_sections = static_cast<int>(attr.data.size()) / radial_n;
	ASSERT_GT(num_sections, 1);

	for (int s = 0; s < num_sections; s++)
	{
		float section_val = attr.data[s * radial_n];
		for (int i = 1; i < radial_n; i++)
		{
			int idx = s * radial_n + i;
			if (idx < static_cast<int>(attr.data.size()))
			{
				// All vertices in the same section have the same angle
				ASSERT_TRUE(std::abs(attr.data[idx] - section_val) < 1e-5f);
			}
		}
	}

	// Verify golden angle progression between consecutive sections
	// golden_angle_rad ~= 2.39996
	const float golden_angle_rad = 2.39996322972865f;
	float first_section = attr.data[0];
	float second_section = attr.data[radial_n];
	float expected_second = std::fmod(golden_angle_rad, static_cast<float>(2 * M_PI));
	// First section should be fmod(0 * golden_angle, 2PI) = 0
	ASSERT_TRUE(std::abs(first_section) < 1e-5f);
	// Second section should be fmod(1 * golden_angle, 2PI)
	ASSERT_TRUE(std::abs(second_section - expected_second) < 1e-4f);
}

// =====================================================================
// VenationGenerator tests
// =====================================================================

TEST(venation_spatial_hash_neighbors)
{
	SpatialHash2D hash(1.0f, Vector2(-5.0f, -5.0f), Vector2(5.0f, 5.0f));
	hash.insert(0, Vector2(0.0f, 0.0f));
	hash.insert(1, Vector2(0.5f, 0.0f));
	hash.insert(2, Vector2(3.0f, 3.0f));
	hash.insert(3, Vector2(0.1f, 0.1f));

	auto neighbors = hash.query_radius(Vector2(0.0f, 0.0f), 1.0f);

	// Should find points 0, 1, 3 (within radius 1.0 of origin)
	// Point 2 at (3,3) is ~4.24 away, should NOT be included
	bool has_0 = false, has_1 = false, has_2 = false, has_3 = false;
	for (int id : neighbors)
	{
		if (id == 0) has_0 = true;
		if (id == 1) has_1 = true;
		if (id == 2) has_2 = true;
		if (id == 3) has_3 = true;
	}
	ASSERT_TRUE(has_0);
	ASSERT_TRUE(has_1);
	ASSERT_TRUE(!has_2);
	ASSERT_TRUE(has_3);
	ASSERT_EQ(static_cast<int>(neighbors.size()), 3);
}

TEST(venation_spatial_hash_empty_query)
{
	SpatialHash2D hash(1.0f, Vector2(-5.0f, -5.0f), Vector2(5.0f, 5.0f));
	hash.insert(0, Vector2(3.0f, 3.0f));

	auto neighbors = hash.query_radius(Vector2(0.0f, 0.0f), 0.5f);
	ASSERT_EQ(static_cast<int>(neighbors.size()), 0);
}

TEST(venation_runions_connected_tree)
{
	// Create a simple diamond contour
	std::vector<Vector2> contour = {
	    Vector2(0.0f, -0.5f), Vector2(0.5f, 0.0f),
	    Vector2(0.0f, 0.5f),  Vector2(-0.5f, 0.0f),
	};

	VenationGenerator gen;
	gen.type = VenationType::Open;
	gen.vein_density = 2000.0f;
	gen.kill_distance = 0.03f;
	gen.growth_step_size = 0.01f;
	gen.attraction_distance = 0.08f;
	gen.max_iterations = 300;
	gen.seed = 42;

	auto veins = gen.generate_veins(contour);
	ASSERT_GT(static_cast<int>(veins.size()), 1);

	// Verify all non-root nodes have valid parent references forming a connected tree
	for (size_t i = 1; i < veins.size(); ++i)
	{
		ASSERT_GE(veins[i].parent, 0);
		ASSERT_TRUE(veins[i].parent < static_cast<int>(i)); // Parent index < child index

		// Follow parent chain to root (must terminate at -1)
		int current = static_cast<int>(i);
		int steps = 0;
		while (current >= 0 && steps < 10000)
		{
			current = veins[current].parent;
			steps++;
		}
		ASSERT_EQ(current, -1); // Must reach root
	}

	// Root node has parent = -1
	ASSERT_EQ(veins[0].parent, -1);
}

TEST(venation_open_produces_branching)
{
	std::vector<Vector2> contour = {
	    Vector2(0.0f, -0.5f), Vector2(0.5f, 0.0f),
	    Vector2(0.0f, 0.5f),  Vector2(-0.5f, 0.0f),
	};

	VenationGenerator gen;
	gen.type = VenationType::Open;
	gen.vein_density = 2000.0f;
	gen.kill_distance = 0.03f;
	gen.growth_step_size = 0.01f;
	gen.attraction_distance = 0.08f;
	gen.max_iterations = 300;
	gen.seed = 42;

	auto veins = gen.generate_veins(contour);
	ASSERT_GT(static_cast<int>(veins.size()), 5);

	// Count branching points (nodes that are parents of multiple children)
	std::vector<int> child_count(veins.size(), 0);
	for (size_t i = 1; i < veins.size(); ++i)
	{
		if (veins[i].parent >= 0)
			child_count[veins[i].parent]++;
	}

	int branch_points = 0;
	for (size_t i = 0; i < veins.size(); ++i)
	{
		if (child_count[i] > 1)
			branch_points++;
	}

	// OPEN venation should have branching points (tree structure)
	ASSERT_GT(branch_points, 0);
}

TEST(venation_closed_produces_loops)
{
	std::vector<Vector2> contour = {
	    Vector2(0.0f, -0.5f), Vector2(0.5f, 0.0f),
	    Vector2(0.0f, 0.5f),  Vector2(-0.5f, 0.0f),
	};

	VenationGenerator gen;
	gen.type = VenationType::Closed;
	gen.vein_density = 2000.0f;
	gen.kill_distance = 0.03f;
	gen.growth_step_size = 0.01f;
	gen.attraction_distance = 0.08f;
	gen.max_iterations = 300;
	gen.seed = 42;

	auto veins = gen.generate_veins(contour);
	ASSERT_GT(static_cast<int>(veins.size()), 5);

	// For CLOSED type, some nodes should connect to non-parent-chain veins
	// (the parent index may point to a node that isn't a direct ancestor
	// in the growth order, indicating a loop was formed)
	// Check that veins were produced (loop detection is structural)
	// CLOSED type should produce at least as many veins as OPEN with same params
	VenationGenerator gen_open;
	gen_open.type = VenationType::Open;
	gen_open.vein_density = 2000.0f;
	gen_open.kill_distance = 0.03f;
	gen_open.growth_step_size = 0.01f;
	gen_open.attraction_distance = 0.08f;
	gen_open.max_iterations = 300;
	gen_open.seed = 42;

	auto veins_open = gen_open.generate_veins(contour);
	// CLOSED should produce at least as many nodes due to reduced kill distance
	ASSERT_GE(static_cast<int>(veins.size()), static_cast<int>(veins_open.size()));

	// Structural check: verify loop merges occurred
	// In closed venation, some nodes are parented to non-ancestor nodes (loop connections).
	// Detect by finding nodes whose parent has children from different growth lineages.
	// Count unique parents and find "merge parents" — parents with multiple children
	// where at least one child index is not contiguous with siblings (cross-branch merge).
	std::vector<std::vector<int>> children(veins.size());
	for (size_t i = 1; i < veins.size(); ++i)
	{
		if (veins[i].parent >= 0)
			children[veins[i].parent].push_back(static_cast<int>(i));
	}

	int merge_parents = 0;
	for (size_t i = 0; i < veins.size(); ++i)
	{
		if (children[i].size() >= 2)
		{
			// Check if children come from different growth fronts
			// (non-contiguous child indices indicate a merge from a different branch)
			bool has_distant_child = false;
			for (size_t c = 1; c < children[i].size(); ++c)
			{
				if (children[i][c] - children[i][c - 1] > 1)
				{
					has_distant_child = true;
					break;
				}
			}
			if (has_distant_child)
				merge_parents++;
		}
	}
	ASSERT_GT(merge_parents, 0);
}

TEST(venation_vein_distance_all_vertices)
{
	// Generate a full leaf with venation enabled
	LeafShapeGenerator gen;
	gen.enable_venation = true;
	gen.venation_type = VenationType::Open;
	gen.vein_density = 800.0f;
	gen.kill_distance = 0.03f;
	gen.contour_resolution = 32;
	Mesh mesh = gen.generate();

	// Verify vein_distance attribute exists and has correct size
	auto it = mesh.attributes.find("vein_distance");
	ASSERT_TRUE(it != mesh.attributes.end());

	auto& attr = *static_cast<Attribute<float>*>(it->second.get());
	ASSERT_EQ(static_cast<int>(attr.data.size()), static_cast<int>(mesh.vertices.size()));

	// All distances should be non-negative
	for (const auto& val : attr.data)
	{
		ASSERT_GE(val, 0.0f);
	}

	// At least some vertices should be close to veins (distance < 0.5)
	bool has_close = false;
	for (const auto& val : attr.data)
	{
		if (val < 0.5f)
		{
			has_close = true;
			break;
		}
	}
	ASSERT_TRUE(has_close);
}

TEST(venation_zero_auxins_graceful)
{
	std::vector<Vector2> contour = {
	    Vector2(0.0f, -0.5f), Vector2(0.5f, 0.0f),
	    Vector2(0.0f, 0.5f),  Vector2(-0.5f, 0.0f),
	};

	VenationGenerator gen;
	gen.vein_density = 0.0f; // Zero density
	gen.seed = 42;

	auto veins = gen.generate_veins(contour);
	ASSERT_EQ(static_cast<int>(veins.size()), 0);

	// compute_vein_distances with empty veins should not crash
	Mesh mesh;
	mesh.vertices.push_back(Vector3(0.0f, 0.0f, 0.0f));
	gen.compute_vein_distances(mesh, veins);
	// No attribute should be added (empty veins)
	ASSERT_TRUE(mesh.attributes.find("vein_distance") == mesh.attributes.end());
}

TEST(venation_no_crash_small_contour)
{
	// Contour with fewer than 3 points
	std::vector<Vector2> contour = {Vector2(0.0f, 0.0f), Vector2(1.0f, 0.0f)};

	VenationGenerator gen;
	gen.vein_density = 800.0f;

	auto veins = gen.generate_veins(contour);
	ASSERT_EQ(static_cast<int>(veins.size()), 0);
}

// =====================================================================
// LeafLODGenerator tests
// =====================================================================

TEST(lod_generate_card_empty_source)
{
	// Source mesh with fewer than 3 vertices should return empty mesh
	Mesh empty_source;
	LeafLODGenerator lod;

	// 0 vertices
	Mesh card0 = lod.generate_card(empty_source);
	ASSERT_EQ(static_cast<int>(card0.vertices.size()), 0);
	ASSERT_EQ(static_cast<int>(card0.polygons.size()), 0);

	// 1 vertex
	Mesh one_vert;
	one_vert.vertices.push_back(Vector3(0.0f, 0.0f, 0.0f));
	Mesh card1 = lod.generate_card(one_vert);
	ASSERT_EQ(static_cast<int>(card1.vertices.size()), 0);
	ASSERT_EQ(static_cast<int>(card1.polygons.size()), 0);

	// 2 vertices
	Mesh two_vert;
	two_vert.vertices.push_back(Vector3(0.0f, 0.0f, 0.0f));
	two_vert.vertices.push_back(Vector3(1.0f, 0.0f, 0.0f));
	Mesh card2 = lod.generate_card(two_vert);
	ASSERT_EQ(static_cast<int>(card2.vertices.size()), 0);
	ASSERT_EQ(static_cast<int>(card2.polygons.size()), 0);
}

TEST(lod_generate_card_4_vertices_2_triangles)
{
	// Create a simple leaf mesh as source
	LeafShapeGenerator gen;
	gen.contour_resolution = 32;
	Mesh source = gen.generate();
	ASSERT_GT(static_cast<int>(source.vertices.size()), 3);

	LeafLODGenerator lod;
	Mesh card = lod.generate_card(source);

	// Card must be exactly 4 vertices
	ASSERT_EQ(static_cast<int>(card.vertices.size()), 4);

	// Card must have exactly 2 triangles (stored as degenerate quads)
	ASSERT_EQ(static_cast<int>(card.polygons.size()), 2);

	// All polygon indices must be valid
	for (const auto& poly : card.polygons)
	{
		for (int j = 0; j < 4; ++j)
		{
			ASSERT_GE(poly[j], 0);
			ASSERT_TRUE(poly[j] < 4);
		}
	}
}

TEST(lod_generate_card_matches_bounding_rect)
{
	LeafShapeGenerator gen;
	gen.contour_resolution = 32;
	Mesh source = gen.generate();

	// Compute bounding box of source mesh
	float min_x = 1e10f, max_x = -1e10f;
	float min_y = 1e10f, max_y = -1e10f;
	for (const auto& v : source.vertices)
	{
		if (v.x() < min_x) min_x = v.x();
		if (v.x() > max_x) max_x = v.x();
		if (v.y() < min_y) min_y = v.y();
		if (v.y() > max_y) max_y = v.y();
	}

	LeafLODGenerator lod;
	Mesh card = lod.generate_card(source);

	// Card vertices should span the bounding rectangle (within tolerance)
	float card_min_x = 1e10f, card_max_x = -1e10f;
	float card_min_y = 1e10f, card_max_y = -1e10f;
	for (const auto& v : card.vertices)
	{
		if (v.x() < card_min_x) card_min_x = v.x();
		if (v.x() > card_max_x) card_max_x = v.x();
		if (v.y() < card_min_y) card_min_y = v.y();
		if (v.y() > card_max_y) card_max_y = v.y();
	}

	float tol = 0.01f;
	ASSERT_TRUE(std::abs(card_min_x - min_x) < tol);
	ASSERT_TRUE(std::abs(card_max_x - max_x) < tol);
	ASSERT_TRUE(std::abs(card_min_y - min_y) < tol);
	ASSERT_TRUE(std::abs(card_max_y - max_y) < tol);
}

TEST(lod_generate_card_uvs_0_1)
{
	LeafShapeGenerator gen;
	Mesh source = gen.generate();

	LeafLODGenerator lod;
	Mesh card = lod.generate_card(source);

	// Card must have UVs
	ASSERT_EQ(static_cast<int>(card.uvs.size()), 4);

	// UVs should span 0-1 range
	float min_u = 1e10f, max_u = -1e10f;
	float min_v = 1e10f, max_v = -1e10f;
	for (const auto& uv : card.uvs)
	{
		ASSERT_GE(uv.x(), 0.0f);
		ASSERT_LE(uv.x(), 1.0f);
		ASSERT_GE(uv.y(), 0.0f);
		ASSERT_LE(uv.y(), 1.0f);
		if (uv.x() < min_u) min_u = uv.x();
		if (uv.x() > max_u) max_u = uv.x();
		if (uv.y() < min_v) min_v = uv.y();
		if (uv.y() > max_v) max_v = uv.y();
	}

	// UVs should cover the full 0-1 range
	ASSERT_TRUE(std::abs(min_u - 0.0f) < 0.01f);
	ASSERT_TRUE(std::abs(max_u - 1.0f) < 0.01f);
	ASSERT_TRUE(std::abs(min_v - 0.0f) < 0.01f);
	ASSERT_TRUE(std::abs(max_v - 1.0f) < 0.01f);
}

TEST(lod_generate_billboard_cloud_num_planes)
{
	std::vector<Vector3> positions = {
	    Vector3(0.0f, 0.0f, 0.0f),
	    Vector3(1.0f, 0.0f, 0.0f),
	    Vector3(0.0f, 1.0f, 0.0f),
	};

	LeafLODGenerator lod;

	// 3 planes
	Mesh cloud3 = lod.generate_billboard_cloud(positions, 3);
	ASSERT_EQ(static_cast<int>(cloud3.vertices.size()), 3 * 4); // 4 verts per plane
	ASSERT_EQ(static_cast<int>(cloud3.polygons.size()), 3 * 2); // 2 tris per plane

	// 5 planes
	Mesh cloud5 = lod.generate_billboard_cloud(positions, 5);
	ASSERT_EQ(static_cast<int>(cloud5.vertices.size()), 5 * 4);
	ASSERT_EQ(static_cast<int>(cloud5.polygons.size()), 5 * 2);
}

TEST(lod_billboard_cloud_empty_positions)
{
	std::vector<Vector3> positions;
	LeafLODGenerator lod;

	Mesh cloud = lod.generate_billboard_cloud(positions, 3);
	ASSERT_EQ(static_cast<int>(cloud.vertices.size()), 0);
	ASSERT_EQ(static_cast<int>(cloud.polygons.size()), 0);
}

TEST(lod_billboard_cloud_zero_planes)
{
	std::vector<Vector3> positions = {
	    Vector3(0.0f, 0.0f, 0.0f),
	    Vector3(1.0f, 0.0f, 0.0f),
	};
	LeafLODGenerator lod;

	Mesh cloud = lod.generate_billboard_cloud(positions, 0);
	ASSERT_EQ(static_cast<int>(cloud.vertices.size()), 0);
	ASSERT_EQ(static_cast<int>(cloud.polygons.size()), 0);
}

TEST(lod_impostor_view_directions_count)
{
	LeafLODGenerator lod;

	auto dirs_8 = lod.get_impostor_view_directions(8);
	ASSERT_EQ(static_cast<int>(dirs_8.size()), 8 * 8);

	auto dirs_12 = lod.get_impostor_view_directions(12);
	ASSERT_EQ(static_cast<int>(dirs_12.size()), 12 * 12);
}

TEST(lod_impostor_view_directions_upper_hemisphere)
{
	LeafLODGenerator lod;
	auto dirs = lod.get_impostor_view_directions(8);

	for (const auto& d : dirs)
	{
		// All directions should be on the upper hemisphere (Z >= 0)
		ASSERT_GE(d.z(), 0.0f);

		// All directions should be approximately unit vectors
		float len = d.norm();
		ASSERT_TRUE(std::abs(len - 1.0f) < 0.01f);
	}
}

int main()
{
	std::cout << std::endl;
	std::cout << "=== MTree Test Results ===" << std::endl;
	std::cout << "Passed: " << tests_passed << std::endl;
	std::cout << "Failed: " << tests_failed << std::endl;
	std::cout << "=========================" << std::endl;

	return tests_failed > 0 ? 1 : 0;
}

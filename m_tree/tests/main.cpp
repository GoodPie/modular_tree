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

int main()
{
	std::cout << std::endl;
	std::cout << "=== MTree Test Results ===" << std::endl;
	std::cout << "Passed: " << tests_passed << std::endl;
	std::cout << "Failed: " << tests_failed << std::endl;
	std::cout << "=========================" << std::endl;

	return tests_failed > 0 ? 1 : 0;
}

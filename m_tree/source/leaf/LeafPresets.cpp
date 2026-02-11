#include "LeafPresets.hpp"
#include <vector>

namespace Mtree
{

// Test fixtures for C++ unit tests. The authoritative Blender UI presets
// live in python_classes/presets/leaf_presets.py and are independent.
static const std::vector<LeafPreset>& get_presets()
{
	static const std::vector<LeafPreset> presets = {
	    {"Oak", 7.0f, 1.0f, 1.0f, 2.0f, 4.0f, 4.0f, 0.7f, MarginType::Lobed, 7, 0.3f, 0.5f, true,
	     VenationType::Open, 800.0f, 3.0f, 0.0f, 0.0f, 0.0f},
	    {"Maple", 5.0f, 1.0f, 1.0f, 1.5f, 3.0f, 3.0f, 0.95f, MarginType::Lobed, 5, 0.5f, 0.5f, true,
	     VenationType::Open, 1000.0f, 2.5f, 0.0f, 0.0f, 0.0f},
	    {"Birch", 2.0f, 1.0f, 0.6f, 2.5f, 8.0f, 8.0f, 0.6f, MarginType::Serrate, 24, 0.05f, 0.5f,
	     true, VenationType::Open, 600.0f, 3.0f, 0.0f, 0.0f, 0.0f},
	    {"Willow", 2.0f, 1.0f, 0.3f, 3.0f, 10.0f, 10.0f, 0.2f, MarginType::Entire, 0, 0.0f, 0.5f,
	     true, VenationType::Open, 400.0f, 4.0f, 0.0f, 0.0f, 0.0f},
	    {"Pine", 2.0f, 1.0f, 0.05f, 4.0f, 20.0f, 20.0f, 0.05f, MarginType::Entire, 0, 0.0f, 0.5f,
	     false, VenationType::Open, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f},
	};
	return presets;
}

const LeafPreset* get_leaf_preset(const std::string& name)
{
	for (const auto& preset : get_presets())
	{
		if (preset.name == name)
		{
			return &preset;
		}
	}
	return nullptr;
}

std::vector<std::string> get_leaf_preset_names()
{
	const auto& presets = get_presets();
	std::vector<std::string> names;
	names.reserve(presets.size());
	for (const auto& preset : presets)
	{
		names.push_back(preset.name);
	}
	return names;
}

} // namespace Mtree

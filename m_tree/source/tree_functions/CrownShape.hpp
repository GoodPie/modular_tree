#pragma once
#include <algorithm>
#include <cmath>

namespace Mtree
{

enum class CrownShape
{
    Conical = 0,
    Spherical = 1,
    Hemispherical = 2,
    Cylindrical = 3,
    TaperedCylindrical = 4,
    Flame = 5,
    InverseConical = 6,
    TendFlame = 7
};

namespace CrownShapeUtils
{
// Shape envelope constants
constexpr float MIN_RATIO = 0.2f;      // Minimum branch length multiplier
constexpr float RATIO_RANGE = 0.8f;    // Variable range (1.0 - MIN_RATIO)
constexpr float TAPER_BASE = 0.5f;     // Base value for tapered shapes
constexpr float TAPER_RANGE = 0.5f;    // Variable range for tapered shapes
constexpr float FLAME_PEAK = 0.7f;     // Height where flame shape peaks
constexpr float FLAME_FALLOFF = 0.3f;  // Falloff zone (1.0 - FLAME_PEAK)

inline float get_shape_ratio(CrownShape shape, float ratio)
{
    ratio = std::clamp(ratio, 0.0f, 1.0f);

    switch (shape)
    {
        case CrownShape::Conical:
            return MIN_RATIO + RATIO_RANGE * ratio;
        case CrownShape::Spherical:
            return MIN_RATIO + RATIO_RANGE * std::sin(static_cast<float>(M_PI) * ratio);
        case CrownShape::Hemispherical:
            return MIN_RATIO + RATIO_RANGE * std::sin(static_cast<float>(M_PI_2) * ratio);
        case CrownShape::Cylindrical:
            return 1.0f;
        case CrownShape::TaperedCylindrical:
            return TAPER_BASE + TAPER_RANGE * ratio;
        case CrownShape::Flame:
            return ratio <= FLAME_PEAK ? ratio / FLAME_PEAK : (1.0f - ratio) / FLAME_FALLOFF;
        case CrownShape::InverseConical:
            return 1.0f - RATIO_RANGE * ratio;
        case CrownShape::TendFlame:
            return ratio <= FLAME_PEAK
                ? TAPER_BASE + TAPER_RANGE * ratio / FLAME_PEAK
                : TAPER_BASE + TAPER_RANGE * (1.0f - ratio) / FLAME_FALLOFF;
        default:
            return 1.0f;
    }
}

} // namespace CrownShapeUtils
} // namespace Mtree

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
constexpr float PI = 3.14159265358979323846f;

inline float get_shape_ratio(CrownShape shape, float ratio)
{
    ratio = std::max(0.0f, std::min(1.0f, ratio));

    switch (shape)
    {
        case CrownShape::Conical:
            return 0.2f + 0.8f * ratio;
        case CrownShape::Spherical:
            return 0.2f + 0.8f * std::sin(PI * ratio);
        case CrownShape::Hemispherical:
            return 0.2f + 0.8f * std::sin(0.5f * PI * ratio);
        case CrownShape::Cylindrical:
            return 1.0f;
        case CrownShape::TaperedCylindrical:
            return 0.5f + 0.5f * ratio;
        case CrownShape::Flame:
            return ratio <= 0.7f ? ratio / 0.7f : (1.0f - ratio) / 0.3f;
        case CrownShape::InverseConical:
            return 1.0f - 0.8f * ratio;
        case CrownShape::TendFlame:
            return ratio <= 0.7f
                ? 0.5f + 0.5f * ratio / 0.7f
                : 0.5f + 0.5f * (1.0f - ratio) / 0.3f;
        default:
            return 1.0f;
    }
}

} // namespace CrownShapeUtils
} // namespace Mtree

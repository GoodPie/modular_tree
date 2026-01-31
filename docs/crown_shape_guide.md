# Crown Shape User Guide

## Introduction

Crown Shape controls how branch lengths vary based on their height on the tree. Instead of all branches being the same length, you can make branches longer or shorter depending on where they grow on the trunk—creating realistic tree silhouettes like cones, spheres, or flames.

Think of it as an invisible envelope around your tree that limits how far branches can reach at different heights.

### Pipeline Position

Crown Shape is a parameter of the **Branch Node**:

```
Mesher Node → Trunk Node → Branch Node (with Crown Shape)
```

The crown shape envelope is calculated relative to the trunk height and modifies branch lengths accordingly.

## Available Shapes

| Shape | Best For | Description |
|-------|----------|-------------|
| Cylindrical | Default | All branches same length. No envelope effect. |
| Conical | Pine, Fir, Spruce | Longer branches at top, shorter at bottom. Classic Christmas tree shape. |
| Spherical | Oak, Maple | Longest branches in the middle, shorter at top and bottom. Round, ball-like crown. |
| Hemispherical | Umbrella trees | Dome-shaped. Branches longest at bottom of crown, tapering to top. |
| Tapered Cylindrical | Gradual variation | Gentle taper from bottom to top. Subtler than conical. |
| Flame | Cedar, Cypress | Pointed top with widest point at 70% height. Sharp, flame-like silhouette. |
| Inverse Conical | Spreading canopy | Opposite of conical—longer branches at bottom. Fan or mushroom shape. |
| Tend Flame | Natural variation | Softer flame shape with less extreme taper. Good for organic looks. |

### Shape Formulas

For technical users, each shape uses a mathematical formula based on the Weber & Penn paper "Creation and Rendering of Realistic Trees" (1995). The `ratio` represents the normalized height position (0 = crown base, 1 = top):

| Shape | Formula |
|-------|---------|
| Conical | `0.2 + 0.8 * ratio` |
| Spherical | `0.2 + 0.8 * sin(π * ratio)` |
| Hemispherical | `0.2 + 0.8 * sin(π/2 * ratio)` |
| Cylindrical | `1.0` |
| Tapered Cylindrical | `0.5 + 0.5 * ratio` |
| Flame | `ratio / 0.7` when ratio ≤ 0.7, else `(1 - ratio) / 0.3` |
| Inverse Conical | `1.0 - 0.8 * ratio` |
| Tend Flame | `0.5 + 0.5 * ratio / 0.7` when ratio ≤ 0.7, else `0.5 + 0.5 * (1 - ratio) / 0.3` |

## Parameter Reference

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Crown Shape | enum | Cylindrical | see above | Shape of the crown envelope |
| Angle Spread | float | 0.0 | -45 to 45 | Height-based angle variation in degrees |
| Show Preview | bool | false | - | Display envelope wireframe in viewport |

### Angle Spread

The **Angle Spread** parameter adjusts branch angles based on height:

- **Positive values**: Branches point more upward near the top, more outward/downward near the base
- **Negative values**: Opposite effect
- **Zero**: No height-based angle variation

This mimics how real trees often have upward-reaching branches near the crown and more horizontal branches lower down.

## How To Use

1. Select your **Branch Node** in the Mtree node editor
2. Open the **N-panel** (Properties sidebar) by pressing `N`
3. Expand the **Crown Shape** section
4. Choose a shape from the dropdown
5. Optionally enable **Preview in Viewport** to see the envelope wireframe
6. Adjust **Angle Spread** if desired

## Tips

- **Start with Cylindrical** to design your base branch settings, then add a crown shape
- **Spherical** works great for deciduous trees like oaks and maples
- **Conical** is essential for realistic conifers
- **Combine with Angle Spread** for more natural-looking results
- The preview envelope shows maximum branch reach—actual branches will vary based on your other settings
- For weeping trees, try **Inverse Conical** with negative **Up Attraction** values

## References

The crown shape implementation follows the Weber & Penn paper:

> Weber, J., & Penn, J. (1995). "Creation and Rendering of Realistic Trees." *SIGGRAPH 95 Conference Proceedings*, pp. 119-128.

Section 4.3 "Stem Children" defines the `ShapeRatio` function that this feature implements.

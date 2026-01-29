# UE5 Pivot Painter 2.0 Material Setup

This guide explains how to set up wind animation in Unreal Engine 5 using the Pivot Painter textures exported from Mtree and Epic's built-in material functions.

## Exported Files

The exporter creates two textures in Epic's Pivot Painter 2.0 format:

| Texture | RGB Channels | Alpha Channel |
|---------|--------------|---------------|
| `{Name}_PivotPos_Index.exr` | World-space pivot position (X, Y, Z) | Hierarchy depth |
| `{Name}_XVector_Extent.exr` | Branch direction vector (normalized) | Branch length |

Plus a **UV2 layer** on the mesh that maps each vertex to its stem's pixel in the textures.

## UE5 Texture Import Settings

For both textures, configure these settings:

| Setting | Value |
|---------|-------|
| **Mip Gen Settings** | NoMipMaps |
| **Compression** | VectorDisplacementmap (RGBA8) or HDR (RGB, no sRGB) |
| **sRGB** | **Unchecked** (critical - data textures, not color) |
| **Filter** | Nearest |

## Using Epic's Built-in Material Function

Epic provides `PivotPainter2FoliageShader` which handles all the wind animation logic. **Do not build the material from scratch** - use this function.

### Step 1: Create Material

1. Create a new Material
2. In Material Details panel, **disable "Tangent Space Normals"**

### Step 2: Add the Foliage Shader Function

1. Right-click in material graph, search for `PivotPainter2FoliageShader`
2. Add it to your graph
3. Connect its output to the **Material Attributes** input (before final output)

### Step 3: Create Material Instance

1. Right-click your material → Create Material Instance
2. The instance exposes wind parameters automatically

### Step 4: Configure Textures in Material Instance

In the Material Instance, assign:
- **Position/Index Texture**: `{Name}_PivotPos_Index.exr`
- **X-Vector/Extent Texture**: `{Name}_XVector_Extent.exr`

### Step 5: Enable Wind Settings

The material function has 4 wind setting groups (hierarchy levels):
- **Wind Setting 1**: Controls trunk
- **Wind Setting 2**: Controls main branches
- **Wind Setting 3**: Controls sub-branches
- **Wind Setting 4**: Controls twigs/leaves

Enable the levels you need and adjust parameters:
- **Wind Intensity**: Overall wind strength
- **Wind Speed**: Animation speed
- **Wind Turbulence**: Randomness/gusting

## How It Works

The `PivotPainter2FoliageShader` function:

1. Reads pivot position and direction from textures via UV2
2. Calculates rotation axis: `cross(XVector, WindDirection)`
3. Applies hierarchical rotation around each branch's pivot point
4. Accumulates parent motion so child branches inherit parent movement

This produces natural tree animation where:
- Each branch rotates around its own pivot (no stretching)
- Child branches follow parent movement
- Different hierarchy levels can have different wind responses

## Optimization

The shader can be expensive with all features enabled. Optimize by:

- **Trunk material**: Only enable Wind Setting 1
- **Branch material**: Enable Wind Settings 1-2
- **Leaf material**: Enable all Wind Settings (leaves need to inherit all parent motion)

## Troubleshooting

### No animation
- Check UV channel 1 is imported (FBX import settings)
- Verify textures are assigned in material instance
- Ensure at least one Wind Setting is enabled

### Mesh stretches or explodes
- Verify using `PivotPainter2FoliageShader` function, not custom nodes
- Check texture compression is VectorDisplacementmap, not Default
- Ensure sRGB is disabled on both textures

### Animation looks wrong
- Check "Tangent Space Normals" is disabled in material
- Verify texture filter is set to Nearest
- Try adjusting Wind Intensity to a smaller value (start with 0.1)

### Branches vibrate too fast
- **Reduce Wind Speed** to 0.1 or lower (default is often too high for trees)
- Reduce Wind Turbulence if movement looks jittery
- Start with very low values and increase gradually:
  - Wind Speed: 0.05 - 0.2
  - Wind Intensity: 0.1 - 0.5
  - Wind Turbulence: 0.1 - 0.3

### Branches don't move independently
- Check the X-Vector texture has valid direction data
- Verify hierarchy depth values vary between branches

## FBX Export Settings (Blender)

When exporting from Blender:
- Enable "Selected Objects"
- Under Geometry: Enable "UVs"
- The UV2 layer (PivotPainterUV) will be included automatically

### Troubleshooting Custom Material

| Problem | Cause | Solution |
|---------|-------|----------|
| All branches move together | Missing phase offset | Add PivotPos.X to Time before Sine |
| No movement at all | UV1 not imported | Check FBX import includes UV channel 1 |
| Black texture preview | Wrong compression | Use VectorDisplacementmap, disable sRGB |
| Extreme movement | Amplitude too high | Reduce the 0.1 multiplier |

## References

- [Epic's Pivot Painter 2.0 Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/pivot-painter-tool-2.0-in-unreal-engine)
- [Material Functions Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/painter-tool-2.0-material-functions-in-unreal-engine)

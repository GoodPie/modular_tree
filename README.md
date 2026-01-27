# Mtree

A procedural tree generator addon for Blender using a node-based workflow.

> **Note:** Maintained fork of [Mtree by MaximeHerpin](https://github.com/MaximeHerpin/modular_tree).

## Features

- **Quick Generate** - One-click tree generation with presets (Oak, Pine, Willow)
- **Node-based workflow** - Build trees visually by connecting nodes for full control
- **Procedural generation** - Control trunk, branches, and leaves with parameters
- **Multi-level branching** - Chain branch nodes for complex tree structures
- **L-system growth** - Biologically-inspired growth simulation with apical dominance
- **Realistic physics** - Gravity, stiffness, and natural spiral patterns (phyllotaxis)
- **Leaf distribution** - Automatic leaf placement on thin branches via geometry nodes
- **Non-destructive** - Adjust parameters and regenerate anytime

## Requirements

- Blender 5.0 or later
  - This is simply because I haven't tested it on earlier versions

## Installation

1. Download the latest release for your OS from [Releases](https://github.com/GoodPie/modular_tree/releases)
2. In Blender: Edit -> Preferences -> Add-ons -> Install
3. Select the downloaded `.zip` file
4. Enable "Modular Tree" in the addon list

## Quick Start

### Quick Generate (Easiest)
1. Open the **3D View** sidebar (press `N`)
2. Select the **MTree** tab
3. Click **Generate Tree** and choose a preset (Oak, Pine, Willow, or Random)

### Node Editor (Full Control)
1. Open a **Node Editor** and select **Mtree** from the tree type dropdown
2. Add a **Tree Mesher** node (Shift+A)
3. Add a **Trunk** node and connect Tree Mesher's output to Trunk's input
4. Add a **Branches** node and connect Trunk's output to Branches' input
5. Click **Generate Tree** in the Tree Mesher node
6. (Optional) Click **Add Leaves** to distribute leaves on the tree

**Tip:** Select a Branch node and press `N` to see organized parameter sections with descriptions.

## Node Types

| Node | Description |
|------|-------------|
| **Tree Mesher** | Generates the final mesh; connect to Trunk |
| **Trunk** | Creates the main trunk with length, radius, and shape controls |
| **Branches** | Adds branches with density, angle, gravity, and split options |
| **Growth** | L-system style growth with apical dominance and iterations |
| **Radius Override** | Fine-tunes branch thickness along their length |
| **Random Value** | Generates random values for parameter variation |
| **Ramp** | Creates gradient values from start to end of branches |

## Customization

### Branch Parameters
- **Seed** - Controls randomization (same seed = same tree)
- **Length/Radius** - Size and thickness
- **Up Attraction/Gravity** - How branches grow relative to gravity
- **Split** - Probability and angle of branch splitting
- **Phyllotaxis** - Spiral angle between branches (137.5 is the golden angle)

### Growth Parameters (L-system)
- **Iterations** - Number of growth cycles
- **Apical Dominance** - How much the main stem suppresses side branches
- **Grow/Split/Cut Thresholds** - Control branching behavior
- **Gravitropism** - Response to gravity direction

### Leaf Distribution
After generating a tree, click "Add Leaves" in Tree Mesher to configure:
- **Density** - Leaves per area
- **Max Radius** - Only place leaves on thin branches
- **Scale/Rotation Variation** - Natural randomness
- **Leaf Object** - Use a custom leaf mesh

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and build instructions.

## License

- Blender addon: [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
- Core library: [MIT](https://choosealicense.com/licenses/mit/)

## Credits

**Maintainer:** [GoodPie](https://github.com/GoodPie)
**Original Author:** [MaximeHerpin](https://github.com/MaximeHerpin)

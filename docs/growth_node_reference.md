# Growth Node Parameter Reference

## Introduction

The Growth Node simulates biological tree growth using an L-system inspired approach. It models how trees grow over multiple iterations (years), with each iteration producing new branches based on vigor distribution, apical dominance, and environmental factors.

### Pipeline Position

The Growth Node fits into the tree generation pipeline as follows:

```
Mesher Node → Trunk Node → Growth Node
```

The Mesher Node is the starting point. It connects to the Trunk Node, which creates the initial stem structure. The Growth Node then simulates multiple years of growth to produce a complete branching structure. When you click "Generate Tree" on the Mesher Node, it traverses the connected nodes to build the tree and convert it to a 3D mesh.

## Parameter Reference

### Basic Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Seed | int | random | 0+ | Random seed for reproducible results |
| Iterations | int | 5 | 1+ | Number of growth cycles (years of growth) |
| Preview Iteration | int | -1 | -1+ | Preview growth at this iteration (-1 for all) |
| Branch Length | float | 1.0 | 0.01+ | Length of each branch segment |

### Growth Control Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Apical Dominance | float | 0.7 | 0-1 | How much the main leader suppresses side branches (0=equal, 1=dominant) |
| Grow Threshold | float | 0.5 | 0-1 | Minimum vigor for a meristem to grow |
| Cut Threshold | float | 0.2 | 0-1 | Vigor below which branches are pruned |

### Splitting Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Split Threshold | float | 0.7 | 0-1 | Vigor above which branches split |
| Split Angle | float | 60 | 0-180 | Angle between split branches (degrees) |

### Physics Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Gravitropism | float | 0.1 | unbounded | Tendency to grow upward (negative=downward) |
| Gravity Strength | float | 1.0 | unbounded | How much branches bend under their weight |
| Randomness | float | 0.1 | 0+ | Random variation in branch direction |

### Lateral Branching Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Enable Lateral Branching | bool | true | - | Enable branches along parent stems (not just from tips) |
| Lateral Start | float | 0.1 | 0-1 | Start position for lateral buds (0=base, 1=tip) |
| Lateral End | float | 0.9 | 0-1 | End position for lateral buds (0=base, 1=tip) |
| Lateral Density | float | 2.0 | 0.1+ | Potential branch points per unit length |
| Lateral Activation | float | 0.4 | 0-1 | Vigor threshold to activate dormant buds |
| Lateral Angle | float | 45 | 0-90 | Initial angle of lateral branches from parent (degrees) |

### Flowering Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| Enable Flowering | bool | false | - | Create flower attachment points at low-vigor tips |
| Flower Threshold | float | 0.4 | 0-1 | Vigor below which meristems become flower points |

## Presets

The Growth Node includes four presets that configure parameters for common tree shapes:

### STRUCTURED

Orderly growth with strong apical dominance, producing well-defined leader branches.

| Parameter | Value |
|-----------|-------|
| Iterations | 6 |
| Apical Dominance | 0.85 |
| Split Threshold | 0.8 |
| Grow Threshold | 0.4 |
| Gravitropism | 0.15 |
| Randomness | 0.05 |

### SPREADING

Wide, spreading canopy with many branches and reduced apical dominance.

| Parameter | Value |
|-----------|-------|
| Iterations | 5 |
| Apical Dominance | 0.5 |
| Split Threshold | 0.6 |
| Grow Threshold | 0.3 |
| Gravity Strength | 1.5 |

### WEEPING

Drooping branches like a willow, with negative gravitropism and high gravity strength.

| Parameter | Value |
|-----------|-------|
| Iterations | 7 |
| Apical Dominance | 0.6 |
| Gravitropism | -0.1 |
| Gravity Strength | 3.0 |
| Branch Length | 1.5 |
| Randomness | 0.15 |

### GNARLED

Twisted, organic growth pattern with low apical dominance and high randomness.

| Parameter | Value |
|-----------|-------|
| Iterations | 8 |
| Apical Dominance | 0.4 |
| Split Threshold | 0.5 |
| Randomness | 0.3 |
| Gravity Strength | 2.0 |

## Concepts Explained

### Vigor

Vigor represents the energy available to each branch point (meristem). It starts at 1.0 at the tree's base and is distributed among child branches based on apical dominance. Vigor determines whether a branch can:
- Grow (vigor > Grow Threshold)
- Split into multiple branches (vigor > Split Threshold)
- Survive (vigor > Cut Threshold)
- Produce flowers (vigor < Flower Threshold)

### Apical Dominance

In real trees, the main growing tip (apical meristem) produces hormones that suppress growth in side branches. The Apical Dominance parameter models this:
- **0.0**: Equal vigor distribution to all branches
- **1.0**: The main leader takes all available vigor

Higher values produce trees with a strong central leader (like conifers), while lower values produce spreading, multi-trunk forms.

### Meristem

A meristem is an active growth tip on the tree. Each iteration, meristems with sufficient vigor extend the branch, potentially split, or (if flowering is enabled) convert to flower attachment points.

### Dormant Bud

Dormant buds are potential branch points along existing stems. When lateral branching is enabled, these buds can activate if:
- The parent branch has sufficient vigor
- The bud position is between Lateral Start and Lateral End
- The local vigor exceeds Lateral Activation threshold

This simulates how trees develop new branches from dormant buds when conditions are favorable (e.g., after pruning or when the crown opens up).

### Gravitropism vs Gravity Strength

These two parameters model different physical effects:

- **Gravitropism**: The biological tendency of branches to grow toward or away from gravity. Positive values cause upward growth (negative geotropism), while negative values cause downward growth.

- **Gravity Strength**: The mechanical bending of branches under their own weight. This is a physical effect independent of growth direction.

A weeping tree might have negative gravitropism (branches grow downward) combined with high gravity strength (branches droop further from weight).

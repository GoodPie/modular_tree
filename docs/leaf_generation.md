# Leaf Generation Guide

## Introduction

Mtree can generate realistic 3D leaves entirely from math — no textures or hand-modeling required. Each leaf is built through a pipeline of steps that handle the outline shape, edge detail, vein patterns, and surface curvature. This page explains what each step does and why it matters.

## The Pipeline

Every leaf goes through these stages in order:

```
Shape Outline → Edge Detail → Triangulation → UVs → Vein Network → Surface Deformation
```

Each stage feeds into the next, so the vein network grows inside the outline, and the surface deformation uses vein positions to raise ridges in the right places.

## 1. Shape Outline (Superformula)

The leaf's overall shape — whether it's round, pointed, heart-shaped, or star-like — is defined by a single mathematical formula called the **Superformula** (Gielis 2003).

Think of it like drawing with a compass that changes its radius as it sweeps around a circle. Instead of drawing a perfect circle, the radius grows and shrinks to create lobes, points, or elongated shapes.

The key parameters are:

| Parameter | What It Does |
|-----------|-------------|
| **m** | Number of symmetry axes. Higher values create more lobes. |
| **n1, n2, n3** | Control how sharp or rounded the lobes are. |
| **aspect_ratio** | Stretches the shape to make it taller than it is wide (like most real leaves). |

The formula samples points around the full 360 degrees, then **refines** areas where the outline curves sharply by adding extra points. This keeps smooth areas efficient while capturing fine detail where it matters.

## 2. Edge Detail (Margin Types)

Real leaves rarely have perfectly smooth edges. The margin system modifies the outline to add teeth, scallops, or lobes — the small-scale features you see when you look closely at a leaf's edge.

Each margin type uses a different wave pattern applied around the perimeter:

| Type | Shape | Real-World Example |
|------|-------|-------------------|
| **Entire** | Smooth, no modification | Magnolia |
| **Serrate** | Asymmetric saw-teeth pointing toward the tip | Elm, Cherry |
| **Dentate** | Symmetric pointed teeth | Chestnut |
| **Crenate** | Rounded scallops | Beech |
| **Lobed** | Deep rounded indentations | Oak, Maple |

The **tooth count** controls how many teeth or scallops appear, **tooth depth** controls how pronounced they are, and **tooth sharpness** (for serrate margins) controls whether teeth lean forward or are more upright.

An optional **asymmetry seed** adds slight random variation to each tooth, so the left and right sides of the leaf aren't perfectly mirrored — just like real leaves.

## 3. Triangulation

The 2D outline needs to be filled with triangles to become a 3D mesh. The generator does this by creating several **concentric rings** that shrink inward toward the center of the leaf, like a topographic map. Adjacent rings are connected with triangle strips, and the innermost ring connects to a single center point in a fan pattern.

This approach ensures even triangle distribution across the leaf surface, which is important for the deformation step later — poorly distributed triangles would create visible creases or flat spots.

## 4. Vein Network (Space Colonization)

This is the most sophisticated algorithm in the pipeline. It simulates how veins actually develop in real leaves using a technique called **space colonization** (Runions et al. 2005).

### How It Works

Imagine scattering hundreds of tiny "growth hormone" points (called **auxin sources**) randomly across the leaf surface. Then place a single vein starting point at the base of the leaf — this is where the stem connects.

The algorithm then runs in cycles:

1. **Each auxin source looks around** for the nearest vein within a certain distance (the **attraction distance**).
2. **Each vein node that has attractors** computes the average direction toward all of them and grows a small step in that direction.
3. **Any auxin source that a vein gets too close to** is removed (the **kill distance**).
4. Repeat until no auxin sources remain or growth stalls.

This naturally produces a branching tree structure that fills the available space — exactly how real leaf veins behave. The vein density, kill distance, and attraction distance control how fine or coarse the resulting network is.

### Open vs. Closed Venation

The algorithm supports two venation patterns found in nature:

- **Open venation** — Veins branch but never reconnect. Each vein tip is a dead end. This is common in ferns and some simpler leaves.
- **Closed venation** — Veins can form loops by connecting to nearby non-ancestor veins. This creates the net-like pattern you see in most flowering plant leaves (like the fine mesh visible in a maple leaf held up to light).

### Vein Thickness (Pipe Model)

After the vein network is grown, each vein segment gets a width based on the **pipe model** (Shinozaki 1964). The idea is simple: every leaf tip contributes one unit of "flow," and these accumulate as you trace back toward the root. A square root is applied so thickness scales realistically — the midrib (central vein) ends up much thicker than the fine outer veins, just like in a real leaf.

### Performance

The algorithm uses a **spatial hash grid** for fast neighbor lookups, so finding nearby veins for each auxin source is nearly instant regardless of how many veins exist. This keeps generation fast even with dense vein networks (up to 5000 auxin sources).

## 5. Surface Deformation

A flat leaf mesh doesn't look convincing, so four deformations bend and curl it into a natural shape:

| Deformation | What It Does |
|-------------|-------------|
| **Midrib curvature** | Bends the leaf along its length, like it's curving upward or downward from base to tip. |
| **Cross curvature** | Cups the leaf across its width, making it slightly bowl-shaped. |
| **Edge curl** | Curls the edges of the leaf inward — vertices near the outline lift more than those near the center. |
| **Vein displacement** | Raises the surface along vein paths, creating the subtle ridges you can feel when you run your finger across a real leaf. Thicker veins create broader, more pronounced ridges. |

The vein displacement works by using an **influence field** computed from the vein network — each vertex gets a value based on how close it is to a vein and how thick that vein is. Thicker veins (like the midrib) affect a wider area, creating the visible raised spine down the center of the leaf.

## 6. LOD Generation

For scenes with thousands of leaves, Mtree generates simplified versions at different levels of detail:

- **LOD 0** — Full detail leaf mesh (used for close-up views)
- **LOD 1 (Card)** — A simple flat rectangle matching the leaf's bounding box, meant to display a texture of the full leaf
- **Billboard cloud** — Multiple intersecting rectangles that approximate the leaf's appearance from different angles
- **Impostor views** — Camera directions distributed across the upper hemisphere for baking leaf appearance from all angles

## Species Presets

Mtree includes presets that combine all of these parameters to match real tree species:

| Preset | Shape | Margin | Venation | Notes |
|--------|-------|--------|----------|-------|
| **Oak** | Wide, lobed | Lobed (7 lobes) | Open, dense | Deep lobes, moderate curvature |
| **Maple** | Star-shaped | Lobed (5 lobes) | Closed, fine veins | Palmate shape with net venation |
| **Birch** | Elongated oval | Serrate | Open | Small sharp teeth, gentle curl |
| **Willow** | Narrow, long | Entire (smooth) | Open, sparse | Very high aspect ratio |
| **Pine** | Needle-shaped | Entire (smooth) | Disabled | Tiny, narrow — technically a needle |

## References

- Gielis, J. (2003). "A generic geometric transformation that unifies a wide range of natural and abstract shapes." *American Journal of Botany*, 90(3), pp. 333-338.
- Runions, A., Fuhrer, M., Lane, B., Federl, P., Rolland-Lagan, A.-G., & Prusinkiewicz, P. (2005). "Modeling and visualization of leaf venation patterns." *ACM Transactions on Graphics*, 24(3), pp. 702-711.
- Shinozaki, K., Yoda, K., Hozumi, K., & Kira, T. (1964). "A quantitative analysis of plant form — the pipe model theory." *Japanese Journal of Ecology*, 14(3), pp. 97-105.

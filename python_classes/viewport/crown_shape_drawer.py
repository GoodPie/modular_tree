"""Viewport draw handler for crown shape envelope visualization."""

from __future__ import annotations

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from .shape_formulas import BLENDER_SHAPE_MAP, CrownShape, generate_envelope_geometry

# Draw handler reference
_draw_handler = None

# Visual style
ENVELOPE_COLOR = (0.4, 0.8, 0.4, 0.5)  # Semi-transparent green
LINE_WIDTH = 1.5


def get_all_mtree_node_trees():
    """Get all MTree node trees in the blend file."""
    node_trees = []
    for node_tree in bpy.data.node_groups:
        if node_tree.bl_idname == "mt_MtreeNodeTree":
            node_trees.append(node_tree)
    return node_trees


def get_tree_object_from_node_tree(node_tree):
    """Find the tree object associated with an MTree node tree."""
    if node_tree is None:
        return None

    # Look for a TreeMesherNode in the node tree
    for node in node_tree.nodes:
        if node.bl_idname == "mt_MesherNode":
            tree_name = getattr(node, "tree_object", "")
            if tree_name:
                return bpy.context.scene.objects.get(tree_name)

    return None


def get_trunk_length_from_node_tree(node_tree) -> float:
    """Get the trunk length from the trunk node in the tree."""
    if node_tree is None:
        return 10.0

    for node in node_tree.nodes:
        if node.bl_idname == "mt_TrunkNode":
            # Find the length socket
            for socket in node.inputs:
                if hasattr(socket, "property_name") and socket.property_name == "length":
                    return socket.property_value

    return 10.0


def get_branch_length_from_node(node) -> float:
    """Get the branch length from a branch node."""
    for socket in node.inputs:
        if hasattr(socket, "property_name") and socket.property_name == "length":
            return socket.property_value
    return 5.0


def draw_crown_envelope():
    """Main draw callback - checks for Branch nodes with preview enabled and draws envelopes."""
    try:
        # Iterate through all MTree node trees
        for node_tree in get_all_mtree_node_trees():
            # Find Branch nodes with preview enabled
            branch_nodes_to_draw = []
            for node in node_tree.nodes:
                if node.bl_idname == "mt_BranchNode":
                    if getattr(node, "show_crown_preview", False):
                        branch_nodes_to_draw.append(node)

            if not branch_nodes_to_draw:
                continue

            # Get tree object location for positioning
            tree_object = get_tree_object_from_node_tree(node_tree)
            if tree_object:
                world_matrix = tree_object.matrix_world.copy()
            else:
                world_matrix = Matrix.Identity(4)

            # Get trunk length for envelope height
            trunk_length = get_trunk_length_from_node_tree(node_tree)

            # Draw envelope for each branch node with preview enabled
            for node in branch_nodes_to_draw:
                shape_name = getattr(node, "crown_shape", "CYLINDRICAL")
                shape = BLENDER_SHAPE_MAP.get(shape_name, CrownShape.Cylindrical)
                branch_length = get_branch_length_from_node(node)

                draw_envelope(shape, trunk_length, branch_length, world_matrix)

    except Exception:
        # Silently ignore errors during drawing to avoid spamming the console
        pass


def draw_envelope(
    shape: CrownShape,
    height: float,
    base_radius: float,
    world_matrix: Matrix,
):
    """Draw the crown envelope wireframe in the 3D viewport.

    Args:
        shape: Crown shape type
        height: Height of the envelope (from trunk length)
        base_radius: Maximum radius (from branch length)
        world_matrix: World transformation matrix for positioning
    """
    # Generate envelope geometry
    vertices, lines = generate_envelope_geometry(shape, height, base_radius)

    # Transform vertices to world space
    world_vertices = []
    for v in vertices:
        local_point = Vector(v)
        world_point = world_matrix @ local_point
        world_vertices.append(world_point)

    # Create line vertices (pairs of start/end points)
    line_coords = []
    for start_idx, end_idx in lines:
        line_coords.append(world_vertices[start_idx])
        line_coords.append(world_vertices[end_idx])

    if not line_coords:
        return

    # Set up GPU state for alpha blending
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(LINE_WIDTH)

    # Use built-in polyline shader for smooth lines
    shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
    batch = batch_for_shader(shader, "LINES", {"pos": line_coords})

    # Get viewport dimensions for line width calculation
    region = bpy.context.region
    shader.uniform_float("viewportSize", (region.width, region.height))
    shader.uniform_float("lineWidth", LINE_WIDTH)
    shader.uniform_float("color", ENVELOPE_COLOR)

    batch.draw(shader)

    # Restore GPU state
    gpu.state.blend_set("NONE")
    gpu.state.line_width_set(1.0)


def register():
    """Register the draw handler."""
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_crown_envelope, (), "WINDOW", "POST_VIEW"
        )


def unregister():
    """Unregister the draw handler."""
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None

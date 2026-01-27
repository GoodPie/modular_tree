from __future__ import annotations

import math

import bpy
from bpy.types import NodeTree, Object

# =============================================================================
# Version constant - increment when changing node group implementation
# =============================================================================
NODE_GROUP_VERSION = 1

# =============================================================================
# Node layout constants
# =============================================================================
NODE_SPACING_X = 200
NODE_SPACING_Y = 150

# Base positions for node columns
_COL_INPUT = -1400
_COL_DISTRIBUTE = -1000
_COL_SAMPLE_RADIUS = -700
_COL_DELETE = -300
_COL_SAMPLE_DIR = 0
_COL_ALIGN = 200
_COL_ROTATE = 400
_COL_INSTANCE = 600
_COL_REALIZE = 800
_COL_JOIN = 1000
_COL_OUTPUT = 1200

# =============================================================================
# Default parameter values
# =============================================================================
DEFAULT_LEAF_DENSITY = 200.0
DEFAULT_MAX_RADIUS = 0.02
DEFAULT_LEAF_SCALE = 0.1
DEFAULT_SCALE_VARIATION = 0.3
DEFAULT_ROTATION_VARIATION = 0.5
DEFAULT_SEED = 0

# =============================================================================
# Resource names
# =============================================================================
DEFAULT_LEAF_NAME = "MTree_Default_Leaf"
RESOURCE_COLLECTION_NAME = "MTree_Resources"
LEAVES_MODIFIER_NAME = "leaves"

# Socket identifier stored at creation time for reliable lookup
_LEAF_OBJECT_SOCKET_IDENTIFIER: str | None = None


def create_default_leaf_object() -> Object:
    """Create a simple quad plane as default leaf mesh.

    Returns:
        The created or existing default leaf object.

    Raises:
        RuntimeError: If object creation fails.
    """
    # Check if it already exists
    existing = bpy.data.objects.get(DEFAULT_LEAF_NAME)
    if existing is not None:
        return existing

    mesh = None
    obj = None
    collection = None

    try:
        # Create a simple quad mesh
        mesh = bpy.data.meshes.new(DEFAULT_LEAF_NAME)

        # Define vertices for a simple quad (leaf shape)
        # Oriented so that +Z is "up" from the leaf surface
        verts = [
            (-0.5, 0.0, 0.0),  # bottom left
            (0.5, 0.0, 0.0),  # bottom right
            (0.5, 1.0, 0.0),  # top right
            (-0.5, 1.0, 0.0),  # top left
        ]
        faces = [(0, 1, 2, 3)]

        mesh.from_pydata(verts, [], faces)

        # Add UV coordinates
        uv_layer = mesh.uv_layers.new(name="UVMap")
        uv_data = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        for i, uv in enumerate(uv_data):
            uv_layer.data[i].uv = uv

        mesh.update()

        # Create object
        obj = bpy.data.objects.new(DEFAULT_LEAF_NAME, mesh)

        # Get or create a hidden collection for MTree resources
        collection = bpy.data.collections.get(RESOURCE_COLLECTION_NAME)
        if collection is None:
            collection = bpy.data.collections.new(RESOURCE_COLLECTION_NAME)

            # Context-safe collection linking
            # Check if scene context is available and collection isn't already linked
            scene = (
                bpy.context.scene
                if bpy.context.scene
                else (bpy.data.scenes[0] if bpy.data.scenes else None)
            )
            if scene is not None:
                linked_names = [c.name for c in scene.collection.children]
                if RESOURCE_COLLECTION_NAME not in linked_names:
                    scene.collection.children.link(collection)

            # Hide the collection in viewport
            collection.hide_viewport = True
            collection.hide_render = True

        collection.objects.link(obj)

        return obj

    except Exception:
        # Clean up orphaned resources on failure
        if obj is not None and obj.users == 0:
            bpy.data.objects.remove(obj)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        raise


def create_leaves_distribution_node_group() -> NodeTree:
    """Create geometry nodes for distributing leaves on tree branches.

    Uses Sample Nearest Surface nodes to sample vertex attributes (radius, direction)
    from the original tree mesh at distributed point positions. This correctly reads
    attributes because Named Attribute evaluates in the mesh context (not point context).

    Returns:
        The created node group.
    """
    global _LEAF_OBJECT_SOCKET_IDENTIFIER

    # Create new node group with versioned name
    node_group_name = f"MTree_Leaves_Distribution_v{NODE_GROUP_VERSION}"
    ng = bpy.data.node_groups.new(node_group_name, "GeometryNodeTree")

    # Create interface sockets (inputs and outputs)
    # Input: Geometry (tree mesh)
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    # Input: Density
    density_socket = ng.interface.new_socket(
        name="Density", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    density_socket.default_value = DEFAULT_LEAF_DENSITY
    density_socket.min_value = 0.0

    # Input: Max Radius - controls which branches get leaves
    max_radius_socket = ng.interface.new_socket(
        name="Max Radius", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    max_radius_socket.default_value = DEFAULT_MAX_RADIUS
    max_radius_socket.min_value = 0.0

    # Input: Scale
    scale_socket = ng.interface.new_socket(
        name="Scale", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    scale_socket.default_value = DEFAULT_LEAF_SCALE
    scale_socket.min_value = 0.0

    # Input: Scale Variation
    scale_var_socket = ng.interface.new_socket(
        name="Scale Variation", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    scale_var_socket.default_value = DEFAULT_SCALE_VARIATION
    scale_var_socket.min_value = 0.0
    scale_var_socket.max_value = 1.0

    # Input: Rotation Variation
    rot_var_socket = ng.interface.new_socket(
        name="Rotation Variation", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    rot_var_socket.default_value = DEFAULT_ROTATION_VARIATION
    rot_var_socket.min_value = 0.0
    rot_var_socket.max_value = 1.0

    # Input: Seed
    seed_socket = ng.interface.new_socket(name="Seed", in_out="INPUT", socket_type="NodeSocketInt")
    seed_socket.default_value = DEFAULT_SEED

    # Input: Leaf Object - store identifier for reliable lookup later
    leaf_socket = ng.interface.new_socket(
        name="Leaf Object", in_out="INPUT", socket_type="NodeSocketObject"
    )
    _LEAF_OBJECT_SOCKET_IDENTIFIER = leaf_socket.identifier

    # Output: Geometry
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    # Create nodes
    # Group Input/Output
    group_input = nodes.new("NodeGroupInput")
    group_input.location = (_COL_INPUT, 0)

    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (_COL_OUTPUT, 0)

    # Distribute Points on Faces
    distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.location = (_COL_DISTRIBUTE, 0)
    distribute.distribute_method = "RANDOM"
    links.new(group_input.outputs["Geometry"], distribute.inputs["Mesh"])
    links.new(group_input.outputs["Density"], distribute.inputs["Density"])
    links.new(group_input.outputs["Seed"], distribute.inputs["Seed"])

    # === SAMPLE RADIUS FROM ORIGINAL MESH ===
    # Sample Nearest Surface samples attribute values FROM a mesh AT specified positions.
    # - Mesh input: geometry to sample FROM (original tree mesh)
    # - Value input: evaluates in context of Mesh input (so Named Attribute reads from tree mesh)
    # - Sample Position: evaluates in current flow context (the distributed points)

    sample_radius = nodes.new("GeometryNodeSampleNearestSurface")
    sample_radius.location = (_COL_SAMPLE_RADIUS, 0)
    sample_radius.data_type = "FLOAT"
    # Connect original tree mesh as the mesh to sample from
    links.new(group_input.outputs["Geometry"], sample_radius.inputs["Mesh"])

    # Named Attribute for radius - evaluates in context of the Mesh input (tree mesh)
    named_attr_radius = nodes.new("GeometryNodeInputNamedAttribute")
    named_attr_radius.location = (_COL_SAMPLE_RADIUS - NODE_SPACING_X, -NODE_SPACING_Y)
    named_attr_radius.data_type = "FLOAT"
    named_attr_radius.inputs["Name"].default_value = "radius"
    links.new(named_attr_radius.outputs["Attribute"], sample_radius.inputs["Value"])

    # Position node for sample position - evaluates in current flow context (distributed points)
    # NOTE: Two separate Position nodes are necessary because they evaluate in different contexts:
    # - This one evaluates BEFORE delete_geo (all distributed points)
    # - position_dir (below) evaluates AFTER delete_geo (filtered points only)
    # Both sample from the original mesh, but at different point sets.
    position_radius = nodes.new("GeometryNodeInputPosition")
    position_radius.location = (_COL_SAMPLE_RADIUS - NODE_SPACING_X, -NODE_SPACING_Y * 2.3)
    links.new(position_radius.outputs["Position"], sample_radius.inputs["Sample Position"])

    # Compare: sampled_radius < max_radius
    compare = nodes.new("FunctionNodeCompare")
    compare.location = (_COL_SAMPLE_RADIUS + NODE_SPACING_X, -NODE_SPACING_Y)
    compare.data_type = "FLOAT"
    compare.operation = "LESS_THAN"
    links.new(sample_radius.outputs["Value"], compare.inputs["A"])
    links.new(group_input.outputs["Max Radius"], compare.inputs["B"])

    # Delete Geometry - remove points where radius >= max_radius (on thick branches)
    delete_geo = nodes.new("GeometryNodeDeleteGeometry")
    delete_geo.location = (_COL_DELETE, 0)
    delete_geo.domain = "POINT"
    delete_geo.mode = "ALL"
    links.new(distribute.outputs["Points"], delete_geo.inputs["Geometry"])

    # Invert selection - delete where NOT (radius < max_radius)
    bool_not = nodes.new("FunctionNodeBooleanMath")
    bool_not.location = (_COL_DELETE - NODE_SPACING_X / 2, -NODE_SPACING_Y)
    bool_not.operation = "NOT"
    links.new(compare.outputs["Result"], bool_not.inputs[0])
    links.new(bool_not.outputs["Boolean"], delete_geo.inputs["Selection"])

    # === SAMPLE DIRECTION FROM ORIGINAL MESH ===
    # Same pattern - sample direction attribute from original mesh at filtered point positions

    sample_direction = nodes.new("GeometryNodeSampleNearestSurface")
    sample_direction.location = (_COL_SAMPLE_DIR, 0)
    sample_direction.data_type = "FLOAT_VECTOR"
    # Connect original tree mesh as the mesh to sample from
    links.new(group_input.outputs["Geometry"], sample_direction.inputs["Mesh"])

    # Named Attribute for direction - evaluates in context of the Mesh input (tree mesh)
    named_attr_dir = nodes.new("GeometryNodeInputNamedAttribute")
    named_attr_dir.location = (_COL_SAMPLE_DIR - NODE_SPACING_X, -NODE_SPACING_Y * 2.3)
    named_attr_dir.data_type = "FLOAT_VECTOR"
    named_attr_dir.inputs["Name"].default_value = "direction"
    links.new(named_attr_dir.outputs["Attribute"], sample_direction.inputs["Value"])

    # Position node for sample position - evaluates in context of filtered points
    # NOTE: This is a separate Position node from position_radius because this one
    # evaluates AFTER delete_geo, so it only sees the filtered point positions.
    # The position values themselves come from the current geometry flow (filtered points),
    # not from the mesh being sampled.
    position_dir = nodes.new("GeometryNodeInputPosition")
    position_dir.location = (_COL_SAMPLE_DIR - NODE_SPACING_X, -NODE_SPACING_Y * 3.3)
    links.new(position_dir.outputs["Position"], sample_direction.inputs["Sample Position"])

    # Align Euler to Vector - orient leaves along branch direction
    align_euler = nodes.new("FunctionNodeAlignEulerToVector")
    align_euler.location = (_COL_ALIGN, -NODE_SPACING_Y)
    align_euler.axis = "Z"
    links.new(sample_direction.outputs["Value"], align_euler.inputs["Vector"])

    # Random rotation variation
    random_rot = nodes.new("FunctionNodeRandomValue")
    random_rot.location = (_COL_ALIGN, -NODE_SPACING_Y * 2.6)
    random_rot.data_type = "FLOAT_VECTOR"
    random_rot.inputs["Min"].default_value = (-math.pi, -math.pi, -math.pi)
    random_rot.inputs["Max"].default_value = (math.pi, math.pi, math.pi)

    # Multiply rotation variation by the variation parameter
    multiply_rot = nodes.new("ShaderNodeVectorMath")
    multiply_rot.location = (_COL_ROTATE, -NODE_SPACING_Y * 2.6)
    multiply_rot.operation = "SCALE"
    links.new(random_rot.outputs["Value"], multiply_rot.inputs[0])
    links.new(group_input.outputs["Rotation Variation"], multiply_rot.inputs["Scale"])

    # Combine rotations using Rotate Euler
    rotate_euler = nodes.new("FunctionNodeRotateEuler")
    rotate_euler.location = (_COL_ROTATE, -NODE_SPACING_Y)
    # Note: 'type' defaults to 'EULER' in Blender 5.0+ and is read-only
    links.new(align_euler.outputs["Rotation"], rotate_euler.inputs["Rotation"])
    links.new(multiply_rot.outputs["Vector"], rotate_euler.inputs["Rotate By"])

    # Random scale
    random_scale = nodes.new("FunctionNodeRandomValue")
    random_scale.location = (_COL_ALIGN, -NODE_SPACING_Y * 4)
    random_scale.data_type = "FLOAT"
    random_scale.inputs["Min"].default_value = 0.0
    random_scale.inputs["Max"].default_value = 1.0

    # Calculate scale: base_scale * (1 - variation + random * variation * 2)
    # Simplified: base_scale * (1 + (random - 0.5) * 2 * variation)
    # Even simpler: base_scale * lerp(1-variation, 1+variation, random)

    # Subtract 0.5 from random
    subtract_half = nodes.new("ShaderNodeMath")
    subtract_half.location = (_COL_ROTATE, -NODE_SPACING_Y * 4)
    subtract_half.operation = "SUBTRACT"
    links.new(random_scale.outputs["Value"], subtract_half.inputs[0])
    subtract_half.inputs[1].default_value = 0.5

    # Multiply by 2
    mult_two = nodes.new("ShaderNodeMath")
    mult_two.location = (_COL_ROTATE + NODE_SPACING_X * 0.75, -NODE_SPACING_Y * 4)
    mult_two.operation = "MULTIPLY"
    links.new(subtract_half.outputs["Value"], mult_two.inputs[0])
    mult_two.inputs[1].default_value = 2.0

    # Multiply by scale variation
    mult_var = nodes.new("ShaderNodeMath")
    mult_var.location = (_COL_ROTATE + NODE_SPACING_X * 1.5, -NODE_SPACING_Y * 4)
    mult_var.operation = "MULTIPLY"
    links.new(mult_two.outputs["Value"], mult_var.inputs[0])
    links.new(group_input.outputs["Scale Variation"], mult_var.inputs[1])

    # Add 1
    add_one = nodes.new("ShaderNodeMath")
    add_one.location = (_COL_ROTATE + NODE_SPACING_X * 2.25, -NODE_SPACING_Y * 4)
    add_one.operation = "ADD"
    links.new(mult_var.outputs["Value"], add_one.inputs[0])
    add_one.inputs[1].default_value = 1.0

    # Multiply by base scale
    final_scale = nodes.new("ShaderNodeMath")
    final_scale.location = (_COL_ROTATE + NODE_SPACING_X * 3, -NODE_SPACING_Y * 4)
    final_scale.operation = "MULTIPLY"
    links.new(add_one.outputs["Value"], final_scale.inputs[0])
    links.new(group_input.outputs["Scale"], final_scale.inputs[1])

    # Object Info node to extract geometry from leaf object
    object_info = nodes.new("GeometryNodeObjectInfo")
    object_info.location = (_COL_ROTATE, NODE_SPACING_Y * 0.7)
    object_info.transform_space = "RELATIVE"
    links.new(group_input.outputs["Leaf Object"], object_info.inputs["Object"])

    # Instance on Points
    instance = nodes.new("GeometryNodeInstanceOnPoints")
    instance.location = (_COL_INSTANCE, 0)
    links.new(delete_geo.outputs["Geometry"], instance.inputs["Points"])
    links.new(object_info.outputs["Geometry"], instance.inputs["Instance"])
    links.new(rotate_euler.outputs["Rotation"], instance.inputs["Rotation"])
    links.new(final_scale.outputs["Value"], instance.inputs["Scale"])

    # Realize Instances
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (_COL_REALIZE, 0)
    links.new(instance.outputs["Instances"], realize.inputs["Geometry"])

    # Join Geometry with original tree mesh
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (_COL_JOIN, 0)
    # For multi-input sockets, use index 0 for all connections -
    # Blender automatically creates new slots for each connection
    links.new(group_input.outputs["Geometry"], join.inputs[0])
    links.new(realize.outputs["Geometry"], join.inputs[0])

    # Output
    links.new(join.outputs["Geometry"], group_output.inputs["Geometry"])

    return ng


def _get_or_create_leaves_node_group() -> NodeTree:
    """Get existing versioned node group or create a new one.

    This ensures that when the node group implementation changes (version incremented),
    users get the updated version instead of using a stale cached node group.

    Returns:
        The leaves distribution node group.
    """
    node_group_name = f"MTree_Leaves_Distribution_v{NODE_GROUP_VERSION}"
    node_group = bpy.data.node_groups.get(node_group_name)
    if node_group is None:
        node_group = create_leaves_distribution_node_group()
    return node_group


def _find_leaf_object_socket_identifier(node_group: NodeTree) -> str | None:
    """Find the Leaf Object socket identifier in the node group.

    Args:
        node_group: The node group to search.

    Returns:
        The socket identifier, or None if not found.
    """
    global _LEAF_OBJECT_SOCKET_IDENTIFIER

    # Use cached identifier if available
    if _LEAF_OBJECT_SOCKET_IDENTIFIER is not None:
        return _LEAF_OBJECT_SOCKET_IDENTIFIER

    # Otherwise search for it
    for item in node_group.interface.items_tree:
        if item.name == "Leaf Object" and hasattr(item, "identifier"):
            _LEAF_OBJECT_SOCKET_IDENTIFIER = item.identifier
            return item.identifier

    return None


def distribute_leaves(ob: Object, leaf_object: Object | None = None) -> None:
    """Add leaves distribution modifier to a tree object.

    Args:
        ob: The tree object to add leaves to. Must have 'radius' and 'direction'
            vertex attributes (generated by the tree mesher).
        leaf_object: Optional custom leaf object. If None, creates a default quad.

    Raises:
        ValueError: If the object is missing required vertex attributes.
    """
    # Prevent duplicate modifiers
    if ob.modifiers.get(LEAVES_MODIFIER_NAME) is not None:
        return

    # Validate required attributes exist on the mesh
    mesh = ob.data
    if not hasattr(mesh, "attributes"):
        raise ValueError(f"Object '{ob.name}' has no mesh data. Cannot distribute leaves.")

    if "radius" not in mesh.attributes:
        raise ValueError(
            f"Object '{ob.name}' is missing 'radius' attribute. "
            "Generate a tree mesh first using MTree."
        )

    if "direction" not in mesh.attributes:
        raise ValueError(
            f"Object '{ob.name}' is missing 'direction' attribute. "
            "Generate a tree mesh first using MTree."
        )

    # Get or create the versioned node group
    node_group = _get_or_create_leaves_node_group()

    modifier = ob.modifiers.new(LEAVES_MODIFIER_NAME, "NODES")
    modifier.node_group = node_group

    # Set default leaf object if not provided
    if leaf_object is None:
        leaf_object = create_default_leaf_object()

    # Find the Leaf Object socket identifier and set it
    # In Blender 5.0+, modifier inputs are accessed via identifiers
    socket_id = _find_leaf_object_socket_identifier(node_group)
    if socket_id is not None:
        modifier[socket_id] = leaf_object

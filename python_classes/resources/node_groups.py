from __future__ import annotations

import math

import bpy
from bpy.types import NodeTree, Object

# =============================================================================
# Version constant - increment when changing node group implementation
# =============================================================================
NODE_GROUP_VERSION = 2

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


def create_leaves_distribution_v2_node_group() -> NodeTree:
    """Create v2 geometry nodes for distributing leaves on tree branches.

    Extends v1 with:
    - Distribution Mode input (0=Random, 1=Phyllotactic)
    - Phyllotaxis Angle input (default 137.5, scales the pre-computed attribute)
    - LOD switching (LOD 1 Object, LOD 1 Distance)
    - Distance-based culling (Cull Distance)
    - Billboard rotation (Billboard Mode: 0=Off, 1=Axial, 2=Camera-Facing)
    - Camera input for distance computation and billboard orientation

    Returns:
        The created node group.
    """
    node_group_name = f"MTree_Leaves_Distribution_v{NODE_GROUP_VERSION}"
    ng = bpy.data.node_groups.new(node_group_name, "GeometryNodeTree")  # type: ignore[arg-type]

    # =========================================================================
    # Interface sockets (v1 sockets + v2 additions)
    # =========================================================================
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    density_socket = ng.interface.new_socket(
        name="Density", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    density_socket.default_value = DEFAULT_LEAF_DENSITY
    density_socket.min_value = 0.0

    max_radius_socket = ng.interface.new_socket(
        name="Max Radius", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    max_radius_socket.default_value = DEFAULT_MAX_RADIUS
    max_radius_socket.min_value = 0.0

    scale_socket = ng.interface.new_socket(
        name="Scale", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    scale_socket.default_value = DEFAULT_LEAF_SCALE
    scale_socket.min_value = 0.0

    scale_var_socket = ng.interface.new_socket(
        name="Scale Variation", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    scale_var_socket.default_value = DEFAULT_SCALE_VARIATION
    scale_var_socket.min_value = 0.0
    scale_var_socket.max_value = 1.0

    rot_var_socket = ng.interface.new_socket(
        name="Rotation Variation", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    rot_var_socket.default_value = DEFAULT_ROTATION_VARIATION
    rot_var_socket.min_value = 0.0
    rot_var_socket.max_value = 1.0

    seed_socket = ng.interface.new_socket(name="Seed", in_out="INPUT", socket_type="NodeSocketInt")
    seed_socket.default_value = DEFAULT_SEED

    ng.interface.new_socket(name="Leaf Object", in_out="INPUT", socket_type="NodeSocketObject")

    # --- v2 sockets ---
    dist_mode_socket = ng.interface.new_socket(
        name="Distribution Mode", in_out="INPUT", socket_type="NodeSocketInt"
    )
    dist_mode_socket.default_value = 0
    dist_mode_socket.min_value = 0
    dist_mode_socket.max_value = 1

    phyllotaxis_socket = ng.interface.new_socket(
        name="Phyllotaxis Angle", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    phyllotaxis_socket.default_value = 137.5
    phyllotaxis_socket.min_value = 0.0
    phyllotaxis_socket.max_value = 360.0

    # --- LOD/Billboard sockets ---
    ng.interface.new_socket(name="LOD 1 Object", in_out="INPUT", socket_type="NodeSocketObject")

    lod1_dist_socket = ng.interface.new_socket(
        name="LOD 1 Distance", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    lod1_dist_socket.default_value = 20.0
    lod1_dist_socket.min_value = 0.0

    cull_dist_socket = ng.interface.new_socket(
        name="Cull Distance", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    cull_dist_socket.default_value = 100.0
    cull_dist_socket.min_value = 0.0

    billboard_mode_socket = ng.interface.new_socket(
        name="Billboard Mode", in_out="INPUT", socket_type="NodeSocketInt"
    )
    billboard_mode_socket.default_value = 0
    billboard_mode_socket.min_value = 0
    billboard_mode_socket.max_value = 2

    ng.interface.new_socket(name="Camera", in_out="INPUT", socket_type="NodeSocketObject")

    enable_normal_socket = ng.interface.new_socket(
        name="Enable Normal Transfer", in_out="INPUT", socket_type="NodeSocketBool"
    )
    enable_normal_socket.default_value = True

    # Output
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    # =========================================================================
    # v1 core nodes (identical to v1)
    # =========================================================================
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
    sample_radius = nodes.new("GeometryNodeSampleNearestSurface")
    sample_radius.location = (_COL_SAMPLE_RADIUS, 0)
    sample_radius.data_type = "FLOAT"
    links.new(group_input.outputs["Geometry"], sample_radius.inputs["Mesh"])

    named_attr_radius = nodes.new("GeometryNodeInputNamedAttribute")
    named_attr_radius.location = (_COL_SAMPLE_RADIUS - NODE_SPACING_X, -NODE_SPACING_Y)
    named_attr_radius.data_type = "FLOAT"
    named_attr_radius.inputs["Name"].default_value = "radius"
    links.new(named_attr_radius.outputs["Attribute"], sample_radius.inputs["Value"])

    position_radius = nodes.new("GeometryNodeInputPosition")
    position_radius.location = (_COL_SAMPLE_RADIUS - NODE_SPACING_X, -NODE_SPACING_Y * 2.3)
    links.new(position_radius.outputs["Position"], sample_radius.inputs["Sample Position"])

    compare = nodes.new("FunctionNodeCompare")
    compare.location = (_COL_SAMPLE_RADIUS + NODE_SPACING_X, -NODE_SPACING_Y)
    compare.data_type = "FLOAT"
    compare.operation = "LESS_THAN"
    links.new(sample_radius.outputs["Value"], compare.inputs["A"])
    links.new(group_input.outputs["Max Radius"], compare.inputs["B"])

    # Delete Geometry - remove points on thick branches
    delete_geo = nodes.new("GeometryNodeDeleteGeometry")
    delete_geo.location = (_COL_DELETE, 0)
    delete_geo.domain = "POINT"
    delete_geo.mode = "ALL"
    links.new(distribute.outputs["Points"], delete_geo.inputs["Geometry"])

    bool_not = nodes.new("FunctionNodeBooleanMath")
    bool_not.location = (_COL_DELETE - NODE_SPACING_X / 2, -NODE_SPACING_Y)
    bool_not.operation = "NOT"
    links.new(compare.outputs["Result"], bool_not.inputs[0])
    links.new(bool_not.outputs["Boolean"], delete_geo.inputs["Selection"])

    # === SAMPLE DIRECTION FROM ORIGINAL MESH ===
    sample_direction = nodes.new("GeometryNodeSampleNearestSurface")
    sample_direction.location = (_COL_SAMPLE_DIR, 0)
    sample_direction.data_type = "FLOAT_VECTOR"
    links.new(group_input.outputs["Geometry"], sample_direction.inputs["Mesh"])

    named_attr_dir = nodes.new("GeometryNodeInputNamedAttribute")
    named_attr_dir.location = (_COL_SAMPLE_DIR - NODE_SPACING_X, -NODE_SPACING_Y * 2.3)
    named_attr_dir.data_type = "FLOAT_VECTOR"
    named_attr_dir.inputs["Name"].default_value = "direction"
    links.new(named_attr_dir.outputs["Attribute"], sample_direction.inputs["Value"])

    position_dir = nodes.new("GeometryNodeInputPosition")
    position_dir.location = (_COL_SAMPLE_DIR - NODE_SPACING_X, -NODE_SPACING_Y * 3.3)
    links.new(position_dir.outputs["Position"], sample_direction.inputs["Sample Position"])

    # Align Euler to Vector
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

    # Scale random rotation by variation parameter
    multiply_rot = nodes.new("ShaderNodeVectorMath")
    multiply_rot.location = (_COL_ROTATE, -NODE_SPACING_Y * 2.6)
    multiply_rot.operation = "SCALE"
    links.new(random_rot.outputs["Value"], multiply_rot.inputs[0])
    links.new(group_input.outputs["Rotation Variation"], multiply_rot.inputs["Scale"])

    # =========================================================================
    # v2 phyllotaxis nodes
    # =========================================================================

    # === SAMPLE PHYLLOTAXIS ANGLE FROM ORIGINAL MESH ===
    sample_phyllotaxis = nodes.new("GeometryNodeSampleNearestSurface")
    sample_phyllotaxis.location = (_COL_SAMPLE_DIR, -NODE_SPACING_Y * 5)
    sample_phyllotaxis.data_type = "FLOAT"
    links.new(group_input.outputs["Geometry"], sample_phyllotaxis.inputs["Mesh"])

    named_attr_phyllotaxis = nodes.new("GeometryNodeInputNamedAttribute")
    named_attr_phyllotaxis.location = (_COL_SAMPLE_DIR - NODE_SPACING_X, -NODE_SPACING_Y * 6)
    named_attr_phyllotaxis.data_type = "FLOAT"
    named_attr_phyllotaxis.inputs["Name"].default_value = "phyllotaxis_angle"
    links.new(named_attr_phyllotaxis.outputs["Attribute"], sample_phyllotaxis.inputs["Value"])

    # Reuse position_dir for phyllotaxis sample position (same filtered point context)
    links.new(position_dir.outputs["Position"], sample_phyllotaxis.inputs["Sample Position"])

    # Scale phyllotaxis angle by user input: effective = sampled * (input / 137.5)
    # This allows user to customize divergence angle without re-meshing
    golden_angle_deg = 137.5
    divide_angle = nodes.new("ShaderNodeMath")
    divide_angle.location = (_COL_ALIGN, -NODE_SPACING_Y * 5)
    divide_angle.operation = "DIVIDE"
    links.new(group_input.outputs["Phyllotaxis Angle"], divide_angle.inputs[0])
    divide_angle.inputs[1].default_value = golden_angle_deg

    scale_phyllotaxis = nodes.new("ShaderNodeMath")
    scale_phyllotaxis.location = (_COL_ALIGN + NODE_SPACING_X, -NODE_SPACING_Y * 5)
    scale_phyllotaxis.operation = "MULTIPLY"
    links.new(sample_phyllotaxis.outputs["Value"], scale_phyllotaxis.inputs[0])
    links.new(divide_angle.outputs["Value"], scale_phyllotaxis.inputs[1])

    # Create phyllotaxis rotation vector (0, 0, scaled_angle)
    combine_phyllotaxis = nodes.new("ShaderNodeCombineXYZ")
    combine_phyllotaxis.location = (_COL_ROTATE - NODE_SPACING_X / 2, -NODE_SPACING_Y * 5)
    combine_phyllotaxis.inputs["X"].default_value = 0.0
    combine_phyllotaxis.inputs["Y"].default_value = 0.0
    links.new(scale_phyllotaxis.outputs["Value"], combine_phyllotaxis.inputs["Z"])

    # Compare: Distribution Mode > 0 (i.e., mode == 1 for Phyllotactic)
    compare_mode = nodes.new("FunctionNodeCompare")
    compare_mode.location = (_COL_ROTATE - NODE_SPACING_X / 2, -NODE_SPACING_Y * 6.5)
    compare_mode.data_type = "INT"
    compare_mode.operation = "GREATER_THAN"
    links.new(group_input.outputs["Distribution Mode"], compare_mode.inputs["A"])
    compare_mode.inputs["B"].default_value = 0

    # Switch: select rotation based on distribution mode
    # False (mode=0, Random) -> random rotation from multiply_rot
    # True (mode=1, Phyllotactic) -> phyllotaxis rotation from combine_phyllotaxis
    switch_rotation = nodes.new("GeometryNodeSwitch")
    switch_rotation.location = (_COL_ROTATE, -NODE_SPACING_Y * 4)
    switch_rotation.input_type = "VECTOR"
    links.new(compare_mode.outputs["Result"], switch_rotation.inputs["Switch"])
    links.new(multiply_rot.outputs["Vector"], switch_rotation.inputs["False"])
    links.new(combine_phyllotaxis.outputs["Vector"], switch_rotation.inputs["True"])

    # =========================================================================
    # Combine rotations (v2: uses switch output instead of direct multiply_rot)
    # =========================================================================
    rotate_euler = nodes.new("FunctionNodeRotateEuler")
    rotate_euler.location = (_COL_ROTATE, -NODE_SPACING_Y)
    links.new(align_euler.outputs["Rotation"], rotate_euler.inputs["Rotation"])
    # v2 change: rotation comes from switch (random or phyllotaxis)
    links.new(switch_rotation.outputs["Output"], rotate_euler.inputs["Rotate By"])

    # =========================================================================
    # Scale computation (same as v1)
    # =========================================================================
    random_scale = nodes.new("FunctionNodeRandomValue")
    random_scale.location = (_COL_ALIGN, -NODE_SPACING_Y * 8)
    random_scale.data_type = "FLOAT"
    random_scale.inputs["Min"].default_value = 0.0
    random_scale.inputs["Max"].default_value = 1.0

    subtract_half = nodes.new("ShaderNodeMath")
    subtract_half.location = (_COL_ROTATE, -NODE_SPACING_Y * 8)
    subtract_half.operation = "SUBTRACT"
    links.new(random_scale.outputs["Value"], subtract_half.inputs[0])
    subtract_half.inputs[1].default_value = 0.5

    mult_two = nodes.new("ShaderNodeMath")
    mult_two.location = (_COL_ROTATE + NODE_SPACING_X * 0.75, -NODE_SPACING_Y * 8)
    mult_two.operation = "MULTIPLY"
    links.new(subtract_half.outputs["Value"], mult_two.inputs[0])
    mult_two.inputs[1].default_value = 2.0

    mult_var = nodes.new("ShaderNodeMath")
    mult_var.location = (_COL_ROTATE + NODE_SPACING_X * 1.5, -NODE_SPACING_Y * 8)
    mult_var.operation = "MULTIPLY"
    links.new(mult_two.outputs["Value"], mult_var.inputs[0])
    links.new(group_input.outputs["Scale Variation"], mult_var.inputs[1])

    add_one = nodes.new("ShaderNodeMath")
    add_one.location = (_COL_ROTATE + NODE_SPACING_X * 2.25, -NODE_SPACING_Y * 8)
    add_one.operation = "ADD"
    links.new(mult_var.outputs["Value"], add_one.inputs[0])
    add_one.inputs[1].default_value = 1.0

    final_scale = nodes.new("ShaderNodeMath")
    final_scale.location = (_COL_ROTATE + NODE_SPACING_X * 3, -NODE_SPACING_Y * 8)
    final_scale.operation = "MULTIPLY"
    links.new(add_one.outputs["Value"], final_scale.inputs[0])
    links.new(group_input.outputs["Scale"], final_scale.inputs[1])

    # =========================================================================
    # Camera + distance computation (LOD/Billboard/Cull)
    # =========================================================================

    # Camera Object Info
    camera_info = nodes.new("GeometryNodeObjectInfo")
    camera_info.location = (550, NODE_SPACING_Y * 3)
    camera_info.transform_space = "ORIGINAL"
    links.new(group_input.outputs["Camera"], camera_info.inputs["Object"])

    # Point position (for distance to camera)
    position_leaf = nodes.new("GeometryNodeInputPosition")
    position_leaf.location = (550, NODE_SPACING_Y * 1.5)

    # Direction: camera_pos - point_pos
    subtract_cam = nodes.new("ShaderNodeVectorMath")
    subtract_cam.location = (700, NODE_SPACING_Y * 2)
    subtract_cam.operation = "SUBTRACT"
    links.new(camera_info.outputs["Location"], subtract_cam.inputs[0])
    links.new(position_leaf.outputs["Position"], subtract_cam.inputs[1])

    # Distance to camera (scalar)
    distance_cam = nodes.new("ShaderNodeVectorMath")
    distance_cam.location = (850, NODE_SPACING_Y * 2)
    distance_cam.operation = "LENGTH"
    links.new(subtract_cam.outputs["Vector"], distance_cam.inputs[0])

    # Normalize direction for billboard rotation
    normalize_cam = nodes.new("ShaderNodeVectorMath")
    normalize_cam.location = (850, NODE_SPACING_Y * 3.5)
    normalize_cam.operation = "NORMALIZE"
    links.new(subtract_cam.outputs["Vector"], normalize_cam.inputs[0])

    # =========================================================================
    # Cull: Delete points beyond cull distance
    # =========================================================================

    compare_cull = nodes.new("FunctionNodeCompare")
    compare_cull.location = (1000, NODE_SPACING_Y * 2)
    compare_cull.data_type = "FLOAT"
    compare_cull.operation = "GREATER_THAN"
    links.new(distance_cam.outputs["Value"], compare_cull.inputs["A"])
    links.new(group_input.outputs["Cull Distance"], compare_cull.inputs["B"])

    delete_cull = nodes.new("GeometryNodeDeleteGeometry")
    delete_cull.location = (1000, 0)
    delete_cull.domain = "POINT"
    delete_cull.mode = "ALL"
    links.new(delete_geo.outputs["Geometry"], delete_cull.inputs["Geometry"])
    links.new(compare_cull.outputs["Result"], delete_cull.inputs["Selection"])

    # =========================================================================
    # LOD selection: LOD0 (close) vs LOD1 (far)
    # =========================================================================

    compare_lod = nodes.new("FunctionNodeCompare")
    compare_lod.location = (1000, NODE_SPACING_Y * 3.5)
    compare_lod.data_type = "FLOAT"
    compare_lod.operation = "GREATER_THAN"
    links.new(distance_cam.outputs["Value"], compare_lod.inputs["A"])
    links.new(group_input.outputs["LOD 1 Distance"], compare_lod.inputs["B"])

    # NOT lod1_selection = lod0_selection
    bool_not_lod = nodes.new("FunctionNodeBooleanMath")
    bool_not_lod.location = (1150, NODE_SPACING_Y * 3)
    bool_not_lod.operation = "NOT"
    links.new(compare_lod.outputs["Result"], bool_not_lod.inputs[0])

    # =========================================================================
    # Billboard rotation
    # =========================================================================

    # Camera-facing: align Z axis toward camera direction
    align_billboard_camera = nodes.new("FunctionNodeAlignEulerToVector")
    align_billboard_camera.location = (1000, NODE_SPACING_Y * 6)
    align_billboard_camera.axis = "Z"
    links.new(normalize_cam.outputs["Vector"], align_billboard_camera.inputs["Vector"])

    # Axial: branch-aligned Z, rotate X toward camera
    align_billboard_axial = nodes.new("FunctionNodeAlignEulerToVector")
    align_billboard_axial.location = (1000, NODE_SPACING_Y * 5)
    align_billboard_axial.axis = "X"
    align_billboard_axial.pivot_axis = "Z"
    links.new(align_euler.outputs["Rotation"], align_billboard_axial.inputs["Rotation"])
    links.new(normalize_cam.outputs["Vector"], align_billboard_axial.inputs["Vector"])

    # Switch 1: Billboard Mode > 0 → axial, else existing rotation
    compare_billboard_1 = nodes.new("FunctionNodeCompare")
    compare_billboard_1.location = (1150, NODE_SPACING_Y * 7)
    compare_billboard_1.data_type = "INT"
    compare_billboard_1.operation = "GREATER_THAN"
    links.new(group_input.outputs["Billboard Mode"], compare_billboard_1.inputs["A"])
    compare_billboard_1.inputs["B"].default_value = 0

    switch_billboard_1 = nodes.new("GeometryNodeSwitch")
    switch_billboard_1.location = (1300, NODE_SPACING_Y * 5)
    switch_billboard_1.input_type = "ROTATION"
    links.new(compare_billboard_1.outputs["Result"], switch_billboard_1.inputs["Switch"])
    links.new(rotate_euler.outputs["Rotation"], switch_billboard_1.inputs["False"])
    links.new(align_billboard_axial.outputs["Rotation"], switch_billboard_1.inputs["True"])

    # Switch 2: Billboard Mode > 1 → camera-facing, else axial/existing
    compare_billboard_2 = nodes.new("FunctionNodeCompare")
    compare_billboard_2.location = (1300, NODE_SPACING_Y * 7)
    compare_billboard_2.data_type = "INT"
    compare_billboard_2.operation = "GREATER_THAN"
    links.new(group_input.outputs["Billboard Mode"], compare_billboard_2.inputs["A"])
    compare_billboard_2.inputs["B"].default_value = 1

    switch_billboard_final = nodes.new("GeometryNodeSwitch")
    switch_billboard_final.location = (1450, NODE_SPACING_Y * 5.5)
    switch_billboard_final.input_type = "ROTATION"
    links.new(compare_billboard_2.outputs["Result"], switch_billboard_final.inputs["Switch"])
    links.new(switch_billboard_1.outputs["Output"], switch_billboard_final.inputs["False"])
    links.new(align_billboard_camera.outputs["Rotation"], switch_billboard_final.inputs["True"])

    # =========================================================================
    # LOD instancing
    # =========================================================================

    # LOD 0: Full detail leaf object
    object_info = nodes.new("GeometryNodeObjectInfo")
    object_info.location = (1400, NODE_SPACING_Y * 0.7)
    object_info.transform_space = "RELATIVE"
    links.new(group_input.outputs["Leaf Object"], object_info.inputs["Object"])

    # Instance LOD 0 on close points
    instance_lod0 = nodes.new("GeometryNodeInstanceOnPoints")
    instance_lod0.location = (1550, 0)
    links.new(delete_cull.outputs["Geometry"], instance_lod0.inputs["Points"])
    links.new(object_info.outputs["Geometry"], instance_lod0.inputs["Instance"])
    links.new(switch_billboard_final.outputs["Output"], instance_lod0.inputs["Rotation"])
    links.new(final_scale.outputs["Value"], instance_lod0.inputs["Scale"])
    links.new(bool_not_lod.outputs["Boolean"], instance_lod0.inputs["Selection"])

    # LOD 1: Simplified card object
    lod1_object_info = nodes.new("GeometryNodeObjectInfo")
    lod1_object_info.location = (1400, -NODE_SPACING_Y * 2.5)
    lod1_object_info.transform_space = "RELATIVE"
    links.new(group_input.outputs["LOD 1 Object"], lod1_object_info.inputs["Object"])

    # Instance LOD 1 on far points
    instance_lod1 = nodes.new("GeometryNodeInstanceOnPoints")
    instance_lod1.location = (1550, -NODE_SPACING_Y * 3.5)
    links.new(delete_cull.outputs["Geometry"], instance_lod1.inputs["Points"])
    links.new(lod1_object_info.outputs["Geometry"], instance_lod1.inputs["Instance"])
    links.new(switch_billboard_final.outputs["Output"], instance_lod1.inputs["Rotation"])
    links.new(final_scale.outputs["Value"], instance_lod1.inputs["Scale"])
    links.new(compare_lod.outputs["Result"], instance_lod1.inputs["Selection"])

    # =========================================================================
    # Realize + join
    # =========================================================================

    realize_lod0 = nodes.new("GeometryNodeRealizeInstances")
    realize_lod0.location = (1750, 0)
    links.new(instance_lod0.outputs["Instances"], realize_lod0.inputs["Geometry"])

    realize_lod1 = nodes.new("GeometryNodeRealizeInstances")
    realize_lod1.location = (1750, -NODE_SPACING_Y * 3.5)
    links.new(instance_lod1.outputs["Instances"], realize_lod1.inputs["Geometry"])

    # Join LOD0 + LOD1 leaves
    join_leaves = nodes.new("GeometryNodeJoinGeometry")
    join_leaves.location = (1950, -NODE_SPACING_Y)
    links.new(realize_lod0.outputs["Geometry"], join_leaves.inputs[0])
    links.new(realize_lod1.outputs["Geometry"], join_leaves.inputs[0])

    # =========================================================================
    # Normal transfer: sample proxy volume normals onto leaf surfaces
    # =========================================================================

    # Bounding box of tree geometry for proxy sizing
    bound_box = nodes.new("GeometryNodeBoundBox")
    bound_box.location = (1950, NODE_SPACING_Y * 6)
    links.new(group_input.outputs["Geometry"], bound_box.inputs["Geometry"])

    # Ico sphere as proxy volume
    ico_sphere = nodes.new("GeometryNodeMeshIcoSphere")
    ico_sphere.location = (1950, NODE_SPACING_Y * 8)
    ico_sphere.inputs["Subdivisions"].default_value = 3
    ico_sphere.inputs["Radius"].default_value = 1.0

    # Compute bbox center: (min + max) / 2
    add_bounds = nodes.new("ShaderNodeVectorMath")
    add_bounds.location = (2150, NODE_SPACING_Y * 7)
    add_bounds.operation = "ADD"
    links.new(bound_box.outputs["Min"], add_bounds.inputs[0])
    links.new(bound_box.outputs["Max"], add_bounds.inputs[1])

    center_bounds = nodes.new("ShaderNodeVectorMath")
    center_bounds.location = (2300, NODE_SPACING_Y * 7)
    center_bounds.operation = "SCALE"
    links.new(add_bounds.outputs["Vector"], center_bounds.inputs[0])
    center_bounds.inputs["Scale"].default_value = 0.5

    # Compute bbox half-extents: (max - min) * 0.6 (slightly larger for coverage)
    sub_bounds = nodes.new("ShaderNodeVectorMath")
    sub_bounds.location = (2150, NODE_SPACING_Y * 8.5)
    sub_bounds.operation = "SUBTRACT"
    links.new(bound_box.outputs["Max"], sub_bounds.inputs[0])
    links.new(bound_box.outputs["Min"], sub_bounds.inputs[1])

    radius_bounds = nodes.new("ShaderNodeVectorMath")
    radius_bounds.location = (2300, NODE_SPACING_Y * 8.5)
    radius_bounds.operation = "SCALE"
    links.new(sub_bounds.outputs["Vector"], radius_bounds.inputs[0])
    radius_bounds.inputs["Scale"].default_value = 0.6

    # Transform ico sphere to cover tree bounding volume
    transform_proxy = nodes.new("GeometryNodeTransform")
    transform_proxy.location = (2450, NODE_SPACING_Y * 8)
    links.new(ico_sphere.outputs["Mesh"], transform_proxy.inputs["Geometry"])
    links.new(center_bounds.outputs["Vector"], transform_proxy.inputs["Translation"])
    links.new(radius_bounds.outputs["Vector"], transform_proxy.inputs["Scale"])

    # Sample normals from proxy at leaf positions
    sample_proxy_normal = nodes.new("GeometryNodeSampleNearestSurface")
    sample_proxy_normal.location = (2450, NODE_SPACING_Y * 5)
    sample_proxy_normal.data_type = "FLOAT_VECTOR"
    links.new(transform_proxy.outputs["Geometry"], sample_proxy_normal.inputs["Mesh"])

    # Normal field evaluated on proxy surface
    proxy_normal_input = nodes.new("GeometryNodeInputNormal")
    proxy_normal_input.location = (2300, NODE_SPACING_Y * 4.5)
    links.new(proxy_normal_input.outputs["Normal"], sample_proxy_normal.inputs["Value"])

    # Leaf vertex positions for sampling
    position_leaf_normal = nodes.new("GeometryNodeInputPosition")
    position_leaf_normal.location = (2300, NODE_SPACING_Y * 3.5)
    links.new(
        position_leaf_normal.outputs["Position"],
        sample_proxy_normal.inputs["Sample Position"],
    )

    # Store sampled normals as "leaf_normal" attribute
    store_leaf_normal = nodes.new("GeometryNodeStoreNamedAttribute")
    store_leaf_normal.location = (2650, NODE_SPACING_Y * 3)
    store_leaf_normal.data_type = "FLOAT_VECTOR"
    store_leaf_normal.domain = "POINT"
    store_leaf_normal.inputs["Name"].default_value = "leaf_normal"
    links.new(join_leaves.outputs["Geometry"], store_leaf_normal.inputs["Geometry"])
    links.new(sample_proxy_normal.outputs["Value"], store_leaf_normal.inputs["Value"])

    # Switch: enable/disable normal transfer
    switch_normal_transfer = nodes.new("GeometryNodeSwitch")
    switch_normal_transfer.location = (2850, NODE_SPACING_Y * 1)
    switch_normal_transfer.input_type = "GEOMETRY"
    links.new(
        group_input.outputs["Enable Normal Transfer"],
        switch_normal_transfer.inputs["Switch"],
    )
    links.new(join_leaves.outputs["Geometry"], switch_normal_transfer.inputs["False"])
    links.new(store_leaf_normal.outputs["Geometry"], switch_normal_transfer.inputs["True"])

    # =========================================================================
    # Join leaves (with or without normal transfer) + tree geometry
    # =========================================================================
    join_all = nodes.new("GeometryNodeJoinGeometry")
    join_all.location = (3050, 0)
    links.new(group_input.outputs["Geometry"], join_all.inputs[0])
    links.new(switch_normal_transfer.outputs["Output"], join_all.inputs[0])

    group_output.location = (3250, 0)
    links.new(join_all.outputs["Geometry"], group_output.inputs["Geometry"])

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
        node_group = create_leaves_distribution_v2_node_group()
    return node_group


def _find_socket_identifier(node_group: NodeTree, name: str) -> str | None:
    """Find a socket identifier by name in the node group interface.

    Args:
        node_group: The node group to search.
        name: The socket name to find.

    Returns:
        The socket identifier, or None if not found.
    """
    for item in node_group.interface.items_tree:
        if item.name == name and hasattr(item, "identifier"):
            return item.identifier
    return None


def _find_leaf_object_socket_identifier(node_group: NodeTree) -> str | None:
    """Find the Leaf Object socket identifier in the node group.

    Args:
        node_group: The node group to search.

    Returns:
        The socket identifier, or None if not found.
    """
    return _find_socket_identifier(node_group, "Leaf Object")


def distribute_leaves(
    ob: Object,
    leaf_object: Object | None = None,
    distribution_mode: int = 0,
    phyllotaxis_angle: float = 137.5,
    lod_1_object: Object | None = None,
    billboard_mode: str = "OFF",
    lod_1_distance: float = 20.0,
    cull_distance: float = 100.0,
    camera: Object | None = None,
    enable_normal_transfer: bool = True,
) -> None:
    """Add leaves distribution modifier to a tree object.

    Args:
        ob: The tree object to add leaves to. Must have 'radius' and 'direction'
            vertex attributes (generated by the tree mesher).
        leaf_object: Optional custom leaf object. If None, creates a default quad.
        distribution_mode: 0=Random (v1 behavior), 1=Phyllotactic.
        phyllotaxis_angle: Divergence angle in degrees (default 137.5 = golden angle).
        lod_1_object: Optional simplified leaf for LOD 1 (card mesh).
        billboard_mode: "OFF", "AXIAL", or "CAMERA" billboard rotation mode.
        lod_1_distance: Distance threshold for LOD 1 switching.
        cull_distance: Distance beyond which leaves are culled.
        camera: Camera object for distance-based LOD and billboard rotation.
        enable_normal_transfer: Whether to transfer proxy volume normals to leaves.

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

    # Set v2 distribution parameters
    if distribution_mode != 0:
        socket_id = _find_socket_identifier(node_group, "Distribution Mode")
        if socket_id is not None:
            modifier[socket_id] = distribution_mode

    if phyllotaxis_angle != 137.5:
        socket_id = _find_socket_identifier(node_group, "Phyllotaxis Angle")
        if socket_id is not None:
            modifier[socket_id] = phyllotaxis_angle

    # Set LOD/Billboard parameters
    if lod_1_object is not None:
        socket_id = _find_socket_identifier(node_group, "LOD 1 Object")
        if socket_id is not None:
            modifier[socket_id] = lod_1_object

    if lod_1_distance != 20.0:
        socket_id = _find_socket_identifier(node_group, "LOD 1 Distance")
        if socket_id is not None:
            modifier[socket_id] = lod_1_distance

    if cull_distance != 100.0:
        socket_id = _find_socket_identifier(node_group, "Cull Distance")
        if socket_id is not None:
            modifier[socket_id] = cull_distance

    if billboard_mode != "OFF":
        _billboard_mode_map = {"OFF": 0, "AXIAL": 1, "CAMERA": 2}
        socket_id = _find_socket_identifier(node_group, "Billboard Mode")
        if socket_id is not None:
            modifier[socket_id] = _billboard_mode_map[billboard_mode]

    if camera is not None:
        socket_id = _find_socket_identifier(node_group, "Camera")
        if socket_id is not None:
            modifier[socket_id] = camera

    if not enable_normal_transfer:
        socket_id = _find_socket_identifier(node_group, "Enable Normal Transfer")
        if socket_id is not None:
            modifier[socket_id] = enable_normal_transfer

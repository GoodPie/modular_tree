import bpy


def create_default_leaf_object():
    """Create a simple quad plane as default leaf mesh."""
    leaf_name = "MTree_Default_Leaf"

    # Check if it already exists
    existing = bpy.data.objects.get(leaf_name)
    if existing is not None:
        return existing

    # Create a simple quad mesh
    mesh = bpy.data.meshes.new(leaf_name)

    # Define vertices for a simple quad (leaf shape)
    # Oriented so that +Z is "up" from the leaf surface
    verts = [
        (-0.5, 0.0, 0.0),   # bottom left
        (0.5, 0.0, 0.0),    # bottom right
        (0.5, 1.0, 0.0),    # top right
        (-0.5, 1.0, 0.0),   # top left
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
    obj = bpy.data.objects.new(leaf_name, mesh)

    # Get or create a hidden collection for MTree resources
    collection_name = "MTree_Resources"
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        # Hide the collection in viewport
        collection.hide_viewport = True
        collection.hide_render = True

    collection.objects.link(obj)

    return obj


def create_leaves_distribution_node_group():
    """Create geometry nodes for distributing leaves on tree branches.

    Uses Sample Nearest Surface nodes to sample vertex attributes (radius, direction)
    from the original tree mesh at distributed point positions. This correctly reads
    attributes because Named Attribute evaluates in the mesh context (not point context).
    """

    # Create new node group
    ng = bpy.data.node_groups.new("leaves_distribution", 'GeometryNodeTree')

    # Create interface sockets (inputs and outputs)
    # Input: Geometry (tree mesh)
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    # Input: Density
    density_socket = ng.interface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
    density_socket.default_value = 100.0
    density_socket.min_value = 0.0
    # Input: Max Radius - increased default to ensure leaves appear on more branches
    max_radius_socket = ng.interface.new_socket(name="Max Radius", in_out='INPUT', socket_type='NodeSocketFloat')
    max_radius_socket.default_value = 0.15
    max_radius_socket.min_value = 0.0
    # Input: Scale
    scale_socket = ng.interface.new_socket(name="Scale", in_out='INPUT', socket_type='NodeSocketFloat')
    scale_socket.default_value = 0.1
    scale_socket.min_value = 0.0
    # Input: Scale Variation
    scale_var_socket = ng.interface.new_socket(name="Scale Variation", in_out='INPUT', socket_type='NodeSocketFloat')
    scale_var_socket.default_value = 0.3
    scale_var_socket.min_value = 0.0
    scale_var_socket.max_value = 1.0
    # Input: Rotation Variation
    rot_var_socket = ng.interface.new_socket(name="Rotation Variation", in_out='INPUT', socket_type='NodeSocketFloat')
    rot_var_socket.default_value = 0.5
    rot_var_socket.min_value = 0.0
    rot_var_socket.max_value = 1.0
    # Input: Seed
    seed_socket = ng.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    seed_socket.default_value = 0
    # Input: Leaf Object
    ng.interface.new_socket(name="Leaf Object", in_out='INPUT', socket_type='NodeSocketObject')

    # Output: Geometry
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Create nodes
    # Group Input/Output
    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-1400, 0)

    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (1200, 0)

    # Distribute Points on Faces
    distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute.location = (-1000, 0)
    distribute.distribute_method = 'RANDOM'
    links.new(group_input.outputs['Geometry'], distribute.inputs['Mesh'])
    links.new(group_input.outputs['Density'], distribute.inputs['Density'])
    links.new(group_input.outputs['Seed'], distribute.inputs['Seed'])

    # === SAMPLE RADIUS FROM ORIGINAL MESH ===
    # Sample Nearest Surface samples attribute values FROM a mesh AT specified positions.
    # - Mesh input: geometry to sample FROM (original tree mesh)
    # - Value input: evaluates in context of Mesh input (so Named Attribute reads from tree mesh)
    # - Sample Position: evaluates in current flow context (the distributed points)

    sample_radius = nodes.new('GeometryNodeSampleNearestSurface')
    sample_radius.location = (-700, 0)
    sample_radius.data_type = 'FLOAT'
    # Connect original tree mesh as the mesh to sample from
    links.new(group_input.outputs['Geometry'], sample_radius.inputs['Mesh'])

    # Named Attribute for radius - evaluates in context of the Mesh input (tree mesh)
    named_attr_radius = nodes.new('GeometryNodeInputNamedAttribute')
    named_attr_radius.location = (-900, -200)
    named_attr_radius.data_type = 'FLOAT'
    named_attr_radius.inputs['Name'].default_value = 'radius'
    links.new(named_attr_radius.outputs['Attribute'], sample_radius.inputs['Value'])

    # Position node for sample position - evaluates in current flow context (distributed points)
    position_radius = nodes.new('GeometryNodeInputPosition')
    position_radius.location = (-900, -350)
    links.new(position_radius.outputs['Position'], sample_radius.inputs['Sample Position'])

    # Compare: sampled_radius < max_radius
    compare = nodes.new('FunctionNodeCompare')
    compare.location = (-500, -200)
    compare.data_type = 'FLOAT'
    compare.operation = 'LESS_THAN'
    links.new(sample_radius.outputs['Value'], compare.inputs['A'])
    links.new(group_input.outputs['Max Radius'], compare.inputs['B'])

    # Delete Geometry - remove points where radius >= max_radius (on thick branches)
    delete_geo = nodes.new('GeometryNodeDeleteGeometry')
    delete_geo.location = (-300, 0)
    delete_geo.domain = 'POINT'
    delete_geo.mode = 'ALL'
    links.new(distribute.outputs['Points'], delete_geo.inputs['Geometry'])
    # Invert selection - delete where NOT (radius < max_radius)
    bool_not = nodes.new('FunctionNodeBooleanMath')
    bool_not.location = (-400, -150)
    bool_not.operation = 'NOT'
    links.new(compare.outputs['Result'], bool_not.inputs[0])
    links.new(bool_not.outputs['Boolean'], delete_geo.inputs['Selection'])

    # === SAMPLE DIRECTION FROM ORIGINAL MESH ===
    # Same pattern - sample direction attribute from original mesh at filtered point positions

    sample_direction = nodes.new('GeometryNodeSampleNearestSurface')
    sample_direction.location = (0, 0)
    sample_direction.data_type = 'FLOAT_VECTOR'
    # Connect original tree mesh as the mesh to sample from
    links.new(group_input.outputs['Geometry'], sample_direction.inputs['Mesh'])

    # Named Attribute for direction - evaluates in context of the Mesh input (tree mesh)
    named_attr_dir = nodes.new('GeometryNodeInputNamedAttribute')
    named_attr_dir.location = (-200, -350)
    named_attr_dir.data_type = 'FLOAT_VECTOR'
    named_attr_dir.inputs['Name'].default_value = 'direction'
    links.new(named_attr_dir.outputs['Attribute'], sample_direction.inputs['Value'])

    # Position node for sample position - evaluates in context of filtered points
    position_dir = nodes.new('GeometryNodeInputPosition')
    position_dir.location = (-200, -500)
    links.new(position_dir.outputs['Position'], sample_direction.inputs['Sample Position'])

    # Align Euler to Vector - orient leaves along branch direction
    align_euler = nodes.new('FunctionNodeAlignEulerToVector')
    align_euler.location = (200, -200)
    align_euler.axis = 'Z'
    links.new(sample_direction.outputs['Value'], align_euler.inputs['Vector'])

    # Random rotation variation
    random_rot = nodes.new('FunctionNodeRandomValue')
    random_rot.location = (200, -400)
    random_rot.data_type = 'FLOAT_VECTOR'
    random_rot.inputs['Min'].default_value = (-3.14159, -3.14159, -3.14159)
    random_rot.inputs['Max'].default_value = (3.14159, 3.14159, 3.14159)

    # Multiply rotation variation by the variation parameter
    multiply_rot = nodes.new('ShaderNodeVectorMath')
    multiply_rot.location = (400, -400)
    multiply_rot.operation = 'SCALE'
    links.new(random_rot.outputs['Value'], multiply_rot.inputs[0])
    links.new(group_input.outputs['Rotation Variation'], multiply_rot.inputs['Scale'])

    # Combine rotations using Rotate Euler
    rotate_euler = nodes.new('FunctionNodeRotateEuler')
    rotate_euler.location = (400, -200)
    # Note: 'type' defaults to 'EULER' in Blender 5.0+ and is read-only
    links.new(align_euler.outputs['Rotation'], rotate_euler.inputs['Rotation'])
    links.new(multiply_rot.outputs['Vector'], rotate_euler.inputs['Rotate By'])

    # Random scale
    random_scale = nodes.new('FunctionNodeRandomValue')
    random_scale.location = (200, -600)
    random_scale.data_type = 'FLOAT'
    random_scale.inputs['Min'].default_value = 0.0
    random_scale.inputs['Max'].default_value = 1.0

    # Calculate scale: base_scale * (1 - variation + random * variation * 2)
    # Simplified: base_scale * (1 + (random - 0.5) * 2 * variation)
    # Even simpler: base_scale * lerp(1-variation, 1+variation, random)

    # Subtract 0.5 from random
    subtract_half = nodes.new('ShaderNodeMath')
    subtract_half.location = (400, -600)
    subtract_half.operation = 'SUBTRACT'
    links.new(random_scale.outputs['Value'], subtract_half.inputs[0])
    subtract_half.inputs[1].default_value = 0.5

    # Multiply by 2
    mult_two = nodes.new('ShaderNodeMath')
    mult_two.location = (550, -600)
    mult_two.operation = 'MULTIPLY'
    links.new(subtract_half.outputs['Value'], mult_two.inputs[0])
    mult_two.inputs[1].default_value = 2.0

    # Multiply by scale variation
    mult_var = nodes.new('ShaderNodeMath')
    mult_var.location = (700, -600)
    mult_var.operation = 'MULTIPLY'
    links.new(mult_two.outputs['Value'], mult_var.inputs[0])
    links.new(group_input.outputs['Scale Variation'], mult_var.inputs[1])

    # Add 1
    add_one = nodes.new('ShaderNodeMath')
    add_one.location = (850, -600)
    add_one.operation = 'ADD'
    links.new(mult_var.outputs['Value'], add_one.inputs[0])
    add_one.inputs[1].default_value = 1.0

    # Multiply by base scale
    final_scale = nodes.new('ShaderNodeMath')
    final_scale.location = (1000, -600)
    final_scale.operation = 'MULTIPLY'
    links.new(add_one.outputs['Value'], final_scale.inputs[0])
    links.new(group_input.outputs['Scale'], final_scale.inputs[1])

    # Object Info node to extract geometry from leaf object
    object_info = nodes.new('GeometryNodeObjectInfo')
    object_info.location = (400, 100)
    object_info.transform_space = 'RELATIVE'
    links.new(group_input.outputs['Leaf Object'], object_info.inputs['Object'])

    # Instance on Points
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (600, 0)
    links.new(delete_geo.outputs['Geometry'], instance.inputs['Points'])
    links.new(object_info.outputs['Geometry'], instance.inputs['Instance'])
    links.new(rotate_euler.outputs['Rotation'], instance.inputs['Rotation'])
    links.new(final_scale.outputs['Value'], instance.inputs['Scale'])

    # Realize Instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (800, 0)
    links.new(instance.outputs['Instances'], realize.inputs['Geometry'])

    # Join Geometry with original tree mesh
    join = nodes.new('GeometryNodeJoinGeometry')
    join.location = (1000, 0)
    # For multi-input sockets, use index 0 for all connections -
    # Blender automatically creates new slots for each connection
    links.new(group_input.outputs['Geometry'], join.inputs[0])
    links.new(realize.outputs['Geometry'], join.inputs[0])

    # Output
    links.new(join.outputs['Geometry'], group_output.inputs['Geometry'])

    return ng


def distribute_leaves(ob, leaf_object=None):
    """Add leaves distribution modifier to a tree object."""
    if ob.modifiers.get("leaves") is not None:
        return

    # Get or create the node group (Python-generated)
    # Use a unique name to avoid conflicts with old .blend-based node groups
    node_group_name = "MTree_Leaves_Distribution"
    node_group = bpy.data.node_groups.get(node_group_name)
    if node_group is None:
        node_group = create_leaves_distribution_node_group()
        node_group.name = node_group_name

    modifier = ob.modifiers.new("leaves", 'NODES')
    modifier.node_group = node_group

    # Set default leaf object if not provided
    if leaf_object is None:
        leaf_object = create_default_leaf_object()

    # Find the Leaf Object socket identifier and set it
    # In Blender 5.0+, modifier inputs are accessed via identifiers
    for item in node_group.interface.items_tree:
        if item.name == "Leaf Object" and hasattr(item, 'identifier'):
            modifier[item.identifier] = leaf_object
            break

from __future__ import annotations

from random import randint
import time

import bpy
import bmesh
import gpu
import numpy as np
from bpy.utils import register_class, unregister_class
from gpu_extras.batch import batch_for_shader

from .m_tree_wrapper import lazy_m_tree as m_tree
from .presets import apply_preset, get_preset_items
from .resources.node_groups import distribute_leaves


class ExecuteNodeFunction(bpy.types.Operator):
    bl_idname = "mtree.node_function"
    bl_label = "Node Function callback"
    bl_options = {'REGISTER', 'UNDO'}

    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()
    function_name : bpy.props.StringProperty()

    def execute(self, context):
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_name]
        getattr(node, self.function_name)()
        return {'FINISHED'}


class AddLeavesModifier(bpy.types.Operator):
    bl_idname = "mtree.add_leaves"
    bl_label = "Add leaves distribution modifier to tree"
    bl_options = {'REGISTER', 'UNDO'}

    object_id: bpy.props.StringProperty()

    def execute(self, context):
        ob = bpy.data.objects.get(self.object_id)
        if ob is not None:
            distribute_leaves(ob)
        return {'FINISHED'}


class QuickGenerateTree(bpy.types.Operator):
    """Generate a random tree with preset settings"""
    bl_idname = "mtree.quick_generate"
    bl_label = "Generate Random Tree"
    bl_options = {'REGISTER', 'UNDO'}

    seed: bpy.props.IntProperty(
        name="Seed",
        default=0,
        min=0,
        description="Random seed (0 = random)"
    )
    preset: bpy.props.EnumProperty(
        name="Preset",
        items=get_preset_items(),
        default='RANDOM'
    )
    add_leaves: bpy.props.BoolProperty(
        name="Add Leaves",
        default=True,
        description="Automatically add leaf distribution"
    )

    def execute(self, context):
        try:
            seed = self.seed if self.seed != 0 else randint(0, 10000)
            start_time = time.time()

            # Create tree using C++ API
            tree = m_tree.Tree()

            # Configure trunk
            trunk = m_tree.TrunkFunction()
            trunk.seed = seed
            trunk.length = 14
            trunk.start_radius = 0.3
            trunk.end_radius = 0.05
            trunk.resolution = 3

            # Configure branches using preset
            branches = m_tree.BranchFunction()
            branches.seed = seed + 1
            apply_preset(branches, self.preset)

            trunk.add_child(branches)
            tree.set_trunk_function(trunk)
            tree.execute_functions()

            # Mesh the tree
            mesher = m_tree.ManifoldMesher()
            mesher.radial_n_points = 32
            mesher.smooth_iterations = 4
            mesh_data = mesher.mesh_tree(tree)

            # Create Blender object
            self._create_blender_object(context, mesh_data, f"Tree_{seed}")

            # Add leaves if enabled
            if self.add_leaves:
                obj = context.view_layer.objects.active
                distribute_leaves(obj)

            elapsed = time.time() - start_time
            self.report({'INFO'}, f"Generated tree (seed={seed}) in {elapsed:.2f}s")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to generate tree: {str(e)}")
            return {'CANCELLED'}

    def _create_blender_object(self, context, cpp_mesh, name: str) -> None:
        """Create Blender mesh object from C++ mesh data."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # Copy mesh data
        verts = cpp_mesh.get_vertices()
        faces = np.copy(cpp_mesh.get_polygons()[::-1])
        radii = cpp_mesh.get_float_attribute("radius")
        directions = cpp_mesh.get_vector3_attribute("direction")

        mesh.vertices.add(len(verts) // 3)
        mesh.vertices.foreach_set("co", verts)
        mesh.attributes.new(name='radius', type='FLOAT', domain='POINT')
        mesh.attributes['radius'].data.foreach_set('value', radii)
        mesh.attributes.new(name='direction', type='FLOAT_VECTOR', domain='POINT')
        mesh.attributes['direction'].data.foreach_set('vector', directions)

        mesh.loops.add(len(faces))
        mesh.loops.foreach_set("vertex_index", faces)

        loop_start = np.arange(0, len(faces), 4, dtype=np.int32)
        loop_total = np.ones(len(faces) // 4, dtype=np.int32) * 4
        mesh.polygons.add(len(faces) // 4)
        mesh.polygons.foreach_set("loop_start", loop_start)
        mesh.polygons.foreach_set("loop_total", loop_total)
        mesh.polygons.foreach_set('use_smooth', np.ones(len(faces) // 4, dtype=bool))

        # UVs
        uv_data = cpp_mesh.get_uvs()
        uv_data.shape = (len(uv_data) // 2, 2)
        uv_loops = np.copy(cpp_mesh.get_uv_loops()[::-1])
        uvs = uv_data[uv_loops].flatten()
        uv_layer = mesh.uv_layers.new() if len(mesh.uv_layers) == 0 else mesh.uv_layers[0]
        uv_layer.data.foreach_set("uv", uvs)

        mesh.update(calc_edges=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset")
        layout.prop(self, "seed")
        layout.prop(self, "add_leaves")


def register():
    register_class(ExecuteNodeFunction)
    register_class(AddLeavesModifier)
    register_class(QuickGenerateTree)


def unregister():
    unregister_class(ExecuteNodeFunction)
    unregister_class(AddLeavesModifier)
    unregister_class(QuickGenerateTree)

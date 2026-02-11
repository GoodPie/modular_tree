"""Blender operators for MTree addon."""

from __future__ import annotations

import time
from random import randint

import bpy
from bpy.utils import register_class, unregister_class

from .m_tree_wrapper import lazy_m_tree as m_tree
from .mesh_utils import create_mesh_from_cpp
from .pivot_painter import ExportFormat, PivotPainterExporter
from .presets import apply_preset, apply_trunk_preset, get_growth_preset_items, get_preset_items
from .presets.leaf_presets import get_leaf_preset_items
from .resources.node_groups import distribute_leaves


class ExecuteNodeFunction(bpy.types.Operator):
    """Execute a function on a node by name."""

    bl_idname = "mtree.node_function"
    bl_label = "Node Function callback"
    bl_options = {"REGISTER", "UNDO"}

    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()
    function_name: bpy.props.StringProperty()

    def execute(self, context):
        node = bpy.data.node_groups[self.node_tree_name].nodes[self.node_name]
        getattr(node, self.function_name)()
        return {"FINISHED"}


class AddLeavesModifier(bpy.types.Operator):
    """Add leaves distribution modifier to tree."""

    bl_idname = "mtree.add_leaves"
    bl_label = "Add leaves distribution modifier to tree"
    bl_options = {"REGISTER", "UNDO"}

    object_id: bpy.props.StringProperty()
    distribution_mode: bpy.props.IntProperty(
        name="Distribution Mode",
        description="0=Random, 1=Phyllotactic",
        default=0,
        min=0,
        max=1,
    )
    phyllotaxis_angle: bpy.props.FloatProperty(
        name="Phyllotaxis Angle",
        description="Divergence angle in degrees (137.5 = golden angle)",
        default=137.5,
        min=0.0,
        max=360.0,
    )
    billboard_mode: bpy.props.EnumProperty(
        name="Billboard Mode",
        items=[
            ("OFF", "Off", "No billboard rotation"),
            ("AXIAL", "Axial", "Rotate around branch axis toward camera"),
            ("CAMERA", "Camera-Facing", "Fully face the camera"),
        ],
        default="OFF",
    )
    lod_1_distance: bpy.props.FloatProperty(
        name="LOD 1 Distance",
        description="Distance threshold for LOD 1 switching",
        default=20.0,
        min=0.0,
    )
    cull_distance: bpy.props.FloatProperty(
        name="Cull Distance",
        description="Distance beyond which leaves are removed",
        default=100.0,
        min=0.0,
    )

    def execute(self, context):
        ob = bpy.data.objects.get(self.object_id)
        if ob is not None:
            distribute_leaves(
                ob,
                distribution_mode=self.distribution_mode,
                phyllotaxis_angle=self.phyllotaxis_angle,
                billboard_mode=self.billboard_mode,
                lod_1_distance=self.lod_1_distance,
                cull_distance=self.cull_distance,
                camera=bpy.context.scene.camera,
            )
        return {"FINISHED"}


class QuickGenerateTree(bpy.types.Operator):
    """Generate a random tree with preset settings."""

    bl_idname = "mtree.quick_generate"
    bl_label = "Generate Random Tree"
    bl_options = {"REGISTER", "UNDO"}

    seed: bpy.props.IntProperty(
        name="Seed", default=0, min=0, description="Random seed (0 = random)"
    )
    preset: bpy.props.EnumProperty(name="Preset", items=get_preset_items(), default="RANDOM")
    add_leaves: bpy.props.BoolProperty(
        name="Add Leaves", default=True, description="Automatically add leaf distribution"
    )

    def execute(self, context):
        try:
            seed = self.seed if self.seed != 0 else randint(0, 10000)
            start_time = time.time()

            cpp_mesh = self._generate_tree(seed)
            self._create_blender_object(context, cpp_mesh, f"Tree_{seed}")

            if self.add_leaves:
                active_obj = context.view_layer.objects.active
                if active_obj is not None:
                    distribute_leaves(active_obj)

            elapsed = time.time() - start_time
            self.report({"INFO"}, f"Generated tree (seed={seed}) in {elapsed:.2f}s")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to generate tree: {str(e)}")
            return {"CANCELLED"}

    def _generate_tree(self, seed: int):
        """Generate tree using C++ library."""
        tree = m_tree.Tree()

        trunk = m_tree.TrunkFunction()
        trunk.seed = seed
        apply_trunk_preset(trunk, self.preset)

        branches = m_tree.BranchFunction()
        branches.seed = seed + 1
        apply_preset(branches, self.preset)

        trunk.add_child(branches)
        tree.set_trunk_function(trunk)
        tree.execute_functions()

        mesher = m_tree.ManifoldMesher()
        mesher.radial_n_points = 32
        mesher.smooth_iterations = 4
        return mesher.mesh_tree(tree)

    def _create_blender_object(self, context, cpp_mesh, name: str) -> None:
        """Create Blender mesh object from C++ mesh data."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        create_mesh_from_cpp(mesh, cpp_mesh)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset")
        layout.prop(self, "seed")
        layout.prop(self, "add_leaves")


class ExportPivotPainter(bpy.types.Operator):
    """Export Pivot Painter 2.0 data for game engines."""

    bl_idname = "mtree.export_pivot_painter"
    bl_label = "Export Pivot Painter"
    bl_options = {"REGISTER", "UNDO"}

    object_name: bpy.props.StringProperty(name="Object")
    export_format: bpy.props.EnumProperty(
        name="Format",
        items=[
            ("UE5", "Unreal Engine 5", "Export for UE5 with Nanite support"),
            ("UE4", "Unreal Engine 4", "Export for UE4 Pivot Painter 2.0"),
            ("UNITY", "Unity", "Export vertex colors for Unity"),
        ],
        default="UE5",
    )
    texture_size: bpy.props.IntProperty(name="Texture Size", default=1024, min=64, max=4096)
    export_path: bpy.props.StringProperty(
        name="Export Path",
        subtype="DIR_PATH",
        default="//pivot_painter/",
    )

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH":
            self.report({"ERROR"}, "Invalid mesh object")
            return {"CANCELLED"}

        mesh_data = obj.data
        if not isinstance(mesh_data, bpy.types.Mesh):
            self.report({"ERROR"}, "Object data is not a mesh")
            return {"CANCELLED"}

        exporter = PivotPainterExporter(
            mesh=mesh_data,
            export_format=ExportFormat[self.export_format],
            texture_size=self.texture_size,
            export_path=self.export_path,
        )

        result = exporter.export(obj.name)

        if result.success:
            self.report({"INFO"}, result.message)
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, result.message)
            return {"CANCELLED"}

    def invoke(self, context, event):
        if context.active_object and context.active_object.type == "MESH":
            self.object_name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "object_name")
        layout.prop(self, "export_format")
        if self.export_format != "UNITY":
            layout.prop(self, "texture_size")
            layout.prop(self, "export_path")


class GenerateLeaf(bpy.types.Operator):
    """Generate a procedural leaf mesh from LeafShapeNode parameters."""

    bl_idname = "mtree.generate_leaf"
    bl_label = "Generate Leaf"
    bl_options = {"REGISTER", "UNDO"}

    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            self.report({"ERROR"}, "Node tree not found")
            return {"CANCELLED"}
        node = node_tree.nodes.get(self.node_name)
        if node and hasattr(node, "generate_leaf"):
            node.generate_leaf()
            return {"FINISHED"}
        self.report({"ERROR"}, "Leaf shape node not found")
        return {"CANCELLED"}


class ApplyLeafPreset(bpy.types.Operator):
    """Apply a species preset to a LeafShapeNode."""

    bl_idname = "mtree.apply_leaf_preset"
    bl_label = "Apply Leaf Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        items=get_leaf_preset_items(),
    )
    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            return {"CANCELLED"}
        node = node_tree.nodes.get(self.node_name)
        if node and hasattr(node, "apply_preset"):
            node.apply_preset(self.preset)
        return {"FINISHED"}


class ApplyBranchNodePreset(bpy.types.Operator):
    """Apply a preset to a branch node."""

    bl_idname = "mtree.apply_branch_node_preset"
    bl_label = "Apply Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(name="Preset", items=get_preset_items())
    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            return {"CANCELLED"}
        node = node_tree.nodes.get(self.node_name)
        if node and hasattr(node, "apply_preset"):
            node.apply_preset(self.preset)
        return {"FINISHED"}


class ApplyTrunkNodePreset(bpy.types.Operator):
    """Apply a preset to a trunk node."""

    bl_idname = "mtree.apply_trunk_node_preset"
    bl_label = "Apply Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(name="Preset", items=get_preset_items())
    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            return {"CANCELLED"}
        node = node_tree.nodes.get(self.node_name)
        if node and hasattr(node, "apply_preset"):
            node.apply_preset(self.preset)
        return {"FINISHED"}


class ApplyGrowthNodePreset(bpy.types.Operator):
    """Apply a preset to a growth node."""

    bl_idname = "mtree.apply_growth_node_preset"
    bl_label = "Apply Growth Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(name="Preset", items=get_growth_preset_items())
    node_tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            return {"CANCELLED"}
        node = node_tree.nodes.get(self.node_name)
        if node and hasattr(node, "apply_preset"):
            node.apply_preset(self.preset)
        return {"FINISHED"}


# Registration

_classes = [
    ExecuteNodeFunction,
    AddLeavesModifier,
    QuickGenerateTree,
    ExportPivotPainter,
    GenerateLeaf,
    ApplyLeafPreset,
    ApplyBranchNodePreset,
    ApplyTrunkNodePreset,
    ApplyGrowthNodePreset,
]


def register():
    for cls in _classes:
        register_class(cls)


def unregister():
    for cls in _classes:
        unregister_class(cls)

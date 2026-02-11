"""Tree mesher node for generating tree meshes."""

from __future__ import annotations

import time

import bpy

from ...m_tree_wrapper import lazy_m_tree as m_tree
from ...mesh_utils import create_mesh_from_cpp
from ..base_types.node import MtreeNode


def on_update_prop(node, context):
    node.build_tree()


class TreeMesherNode(bpy.types.Node, MtreeNode):
    """Node that generates tree meshes from tree functions."""

    bl_idname = "mt_MesherNode"
    bl_label = "Tree Mesher"

    radial_resolution: bpy.props.IntProperty(
        name="Radial Resolution", default=32, min=3, update=on_update_prop
    )
    smoothness: bpy.props.IntProperty(name="smoothness", default=4, min=0, update=on_update_prop)
    tree_object: bpy.props.StringProperty(default="")

    # Status feedback properties
    status_message: bpy.props.StringProperty(default="")
    status_is_error: bpy.props.BoolProperty(default=False)

    def init(self, context):
        self.add_output("mt_TreeSocket", "Tree", is_property=False)

    def draw(self, context, layout):
        valid_tree = self.get_tree_validity()

        if self.status_message:
            status_row = layout.row()
            status_row.alert = self.status_is_error
            icon = "ERROR" if self.status_is_error else "CHECKMARK"
            status_row.label(text=self.status_message, icon=icon)

        generate_row = layout.row()
        generate_row.enabled = valid_tree
        self._draw_generate_button(generate_row)

        self._draw_tree_object_selector(layout, context)
        self._draw_properties(layout)

        leaves_row = layout.row()
        leaves_row.enabled = valid_tree
        self._draw_leaves_button(leaves_row)

    def _draw_generate_button(self, container):
        props = container.operator("mtree.node_function", text="Generate Tree")
        props.node_tree_name = self.get_node_tree().name
        props.node_name = self.name
        props.function_name = "build_tree"

    def _draw_tree_object_selector(self, container, context):
        container.prop_search(
            self,
            property="tree_object",
            search_data=context.scene,
            search_property="objects",
            text="",
        )

    def _draw_properties(self, container):
        container.prop(self, "radial_resolution")
        container.prop(self, "smoothness")

    def _draw_leaves_button(self, container):
        if self._has_valid_tree_object():
            props = container.operator("mtree.add_leaves", text="Add leaves")
            props.object_id = self.get_current_tree_object().name

    def _has_valid_tree_object(self):
        return bpy.context.scene.objects.get(self.tree_object, None) is not None

    def build_tree(self):
        """Build the tree mesh from connected function nodes."""
        if not self.get_tree_validity():
            self.status_message = "Connect a Trunk node to generate"
            self.status_is_error = True
            return

        self.status_message = ""
        self.status_is_error = False

        try:
            start_time = time.time()

            tree = m_tree.Tree()
            output_links = self.outputs[0].links
            if not output_links:
                raise ValueError("No connected trunk node")
            trunk_function = output_links[0].to_node.construct_function()
            if trunk_function is None:
                raise ValueError("Connected node returned no tree function")
            tree.set_trunk_function(trunk_function)
            tree.execute_functions()

            cpp_mesh = self._mesh_tree(tree)
            self._output_to_blender(cpp_mesh)

            elapsed = time.time() - start_time
            self.status_message = f"Generated in {elapsed:.2f}s"
            self.status_is_error = False

        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            self.status_is_error = True

    def _mesh_tree(self, tree):
        """Convert tree structure to mesh using ManifoldMesher."""
        mesher = m_tree.ManifoldMesher()
        mesher.radial_n_points = self.radial_resolution
        mesher.smooth_iterations = self.smoothness
        return mesher.mesh_tree(tree)

    def get_current_tree_object(self):
        """Get or create the Blender object for this tree."""
        tree_obj = bpy.context.scene.objects.get(self.tree_object, None)
        if tree_obj is None:
            tree_mesh = bpy.data.meshes.new("tree")
            tree_obj = bpy.data.objects.new("tree", tree_mesh)
            bpy.context.collection.objects.link(tree_obj)
            self.tree_object = tree_obj.name
            bpy.context.view_layer.objects.active = tree_obj
            tree_obj.select_set(True)
        return tree_obj

    def _output_to_blender(self, cpp_mesh):
        """Output the C++ mesh to a Blender object."""
        tree_obj = self.get_current_tree_object()
        tree_mesh = tree_obj.data
        if not isinstance(tree_mesh, bpy.types.Mesh):
            raise TypeError("Tree object data is not a Mesh")
        tree_mesh.clear_geometry()
        bpy.context.view_layer.objects.active = tree_obj

        create_mesh_from_cpp(tree_mesh, cpp_mesh)

    def get_tree_validity(self):
        """Check if the tree node setup is valid."""
        output_links = self.outputs[0].links
        has_valid_child = output_links is not None and len(output_links) == 1
        loops_detected = self._detect_loop_rec(self)
        return has_valid_child and not loops_detected

    def _detect_loop_rec(self, node=None, seen_nodes=None):
        """Recursively detect loops in the node graph."""
        if node is None:
            node = self
        if seen_nodes is None:
            seen_nodes = set()

        for output in node.outputs:
            if output.links is None:
                continue
            for link in output.links:
                destination_node = link.to_node
                if destination_node in seen_nodes:
                    return True
                seen_nodes.add(destination_node)
                self._detect_loop_rec(destination_node, seen_nodes)

        return False

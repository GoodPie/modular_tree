import bpy

from ...m_tree_wrapper import lazy_m_tree
from ..base_types.socket import MtreeSocket
from ..tree_function_nodes.tree_mesher_node import debounced_build


class MtreePropertySocket(bpy.types.NodeSocket, MtreeSocket):
    bl_idname = "mt_PropertySocket"
    bl_label = "Mtree Property Socket"

    color = (0.8, 0.8, 0.8, 0.5)

    min_value: bpy.props.FloatProperty(default=-float("inf"))
    max_value: bpy.props.FloatProperty(default=float("inf"))

    def update_value(self, context):
        self["property_value"] = max(self.min_value, min(self.max_value, self.property_value))
        mesher = self.node.get_mesher()
        if mesher is not None:
            if getattr(mesher, "auto_update", True):
                debounced_build(mesher)
            else:
                mesher.build_tree()

    property_value: bpy.props.FloatProperty(default=0, update=update_value)

    def get_property(self):
        if self.is_linked and self.links:
            property = self.links[0].from_node.get_property()
            return lazy_m_tree.PropertyWrapper(property)
        else:
            property = lazy_m_tree.ConstantProperty(float(self.property_value))
            wrapper = lazy_m_tree.PropertyWrapper()
            wrapper.set_constant_property(property)
            return wrapper

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "property_value", text=text)

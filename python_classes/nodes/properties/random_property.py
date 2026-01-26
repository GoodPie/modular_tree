import bpy
from ..base_types.node import MtreePropertyNode
from ...m_tree_wrapper import lazy_m_tree

class RandomPropertyNode(bpy.types.Node, MtreePropertyNode):
    bl_idname = "mt_RandomPropertyNode"
    bl_label = "Random Value"

    @property
    def property_type(self):
        return lazy_m_tree.RandomProperty

    def init(self, context):
        self.add_input("mt_PropertySocket", "min", property_name="min", property_value=.01)
        self.add_input("mt_PropertySocket", "max", property_name="max", property_value=1)
        self.add_output("mt_PropertySocket", "value", is_property=False)
        
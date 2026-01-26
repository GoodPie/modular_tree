import bpy
from ..base_types.node import MtreePropertyNode
from ...m_tree_wrapper import lazy_m_tree

class RampPropertyNode(bpy.types.Node, MtreePropertyNode):
    bl_idname = "mt_RampPropertyNode"
    bl_label = "Ramp"

    @property
    def property_type(self):
        return lazy_m_tree.SimpleCurveProperty

    def init(self, context):
        self.add_input("mt_PropertySocket", "start", property_name="y_min", property_value=.01)
        self.add_input("mt_PropertySocket", "end", property_name="y_max", property_value=1)
        self.add_input("mt_PropertySocket", "power", property_name="power", property_value=1)
        self.add_output("mt_PropertySocket", "value", is_property=False)
        
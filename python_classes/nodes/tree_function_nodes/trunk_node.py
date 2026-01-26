from random import randint
import bpy
from ..base_types.node import MtreeFunctionNode
from ...m_tree_wrapper import lazy_m_tree

class TrunkNode(bpy.types.Node, MtreeFunctionNode):
    bl_idname = "mt_TrunkNode"
    bl_label = "Trunk"

    @property
    def tree_function(self):
        return lazy_m_tree.TrunkFunction

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)
        self.add_input("mt_IntSocket", "Seed", min_value=0, property_name="seed", property_value=randint(0,1000))
        self.add_input("mt_FloatSocket", "Length", min_value=0, property_name="length", property_value=14)
        self.add_input("mt_FloatSocket", "Start Radius", min_value=0.0001, property_name="start_radius", property_value=.3)
        self.add_input("mt_FloatSocket", "End Radius", min_value=0.0001, property_name="end_radius", property_value=.05)
        self.add_input("mt_FloatSocket", "Shape", min_value=0.0001, property_name="shape", property_value=.7)
        self.add_input("mt_FloatSocket", "Up Attraction", property_name="up_attraction", property_value=.6)
        self.add_input("mt_FloatSocket", "Resolution", min_value=0.0001, property_name="resolution", property_value=3)
        self.add_input("mt_FloatSocket", "Randomness", property_name="randomness", property_value=1)

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

from __future__ import annotations

from random import randint
import bpy
from ..base_types.node import MtreeFunctionNode
from ...m_tree_wrapper import lazy_m_tree


class GrowthNode(bpy.types.Node, MtreeFunctionNode):
    """L-system style growth simulation for biologically-inspired tree generation"""
    bl_idname = "mt_GrowthNode"
    bl_label = "Growth"

    @property
    def tree_function(self):
        return lazy_m_tree.GrowthFunction

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)

        # Core parameters
        self.add_input("mt_IntSocket", "Seed", min_value=0, property_name="seed", property_value=randint(0, 1000))
        self.add_input("mt_IntSocket", "Iterations", min_value=1, property_name="iterations", property_value=5)
        self.add_input("mt_FloatSocket", "Branch Length", min_value=0.01, property_name="branch_length", property_value=1)

        # Growth control
        self.add_input("mt_FloatSocket", "Apical Dominance", min_value=0, max_value=1, property_name="apical_dominance", property_value=0.7)
        self.add_input("mt_FloatSocket", "Grow Threshold", min_value=0, max_value=1, property_name="grow_threshold", property_value=0.5)
        self.add_input("mt_FloatSocket", "Cut Threshold", min_value=0, max_value=1, property_name="cut_threshold", property_value=0.2)

        # Splitting
        self.add_input("mt_FloatSocket", "Split Threshold", min_value=0, max_value=1, property_name="split_threshold", property_value=0.7)
        self.add_input("mt_FloatSocket", "Split Angle", min_value=0, max_value=180, property_name="split_angle", property_value=60)

        # Physical simulation
        self.add_input("mt_FloatSocket", "Gravitropism", property_name="gravitropism", property_value=0.1)
        self.add_input("mt_FloatSocket", "Gravity Strength", property_name="gravity_strength", property_value=1)
        self.add_input("mt_FloatSocket", "Randomness", min_value=0, property_name="randomness", property_value=0.1)

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

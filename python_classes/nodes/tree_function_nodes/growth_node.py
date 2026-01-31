from __future__ import annotations

from random import randint

import bpy

from ...m_tree_wrapper import lazy_m_tree
from ..base_types.node import MtreeFunctionNode

# Parameter groupings for organized UI
BASIC_PARAMS = ["seed", "iterations", "branch_length"]
GROWTH_PARAMS = ["apical_dominance", "grow_threshold", "cut_threshold"]
SPLIT_PARAMS = ["split_threshold", "split_angle"]
PHYSICS_PARAMS = ["gravitropism", "gravity_strength", "randomness"]

# Parameter descriptions for tooltips
PARAM_DESCRIPTIONS = {
    "seed": "Random seed for reproducible results",
    "iterations": "Number of growth cycles (years of growth)",
    "branch_length": "Length of each branch segment",
    "apical_dominance": "How much the main leader suppresses side branches (0=equal, 1=dominant)",
    "grow_threshold": "Minimum vigor for a meristem to grow",
    "cut_threshold": "Vigor below which branches are pruned",
    "split_threshold": "Vigor above which branches split",
    "split_angle": "Angle between split branches",
    "gravitropism": "Tendency to grow upward (negative=downward)",
    "gravity_strength": "How much branches bend under their weight",
    "randomness": "Random variation in branch direction",
}


class GrowthNode(bpy.types.Node, MtreeFunctionNode):
    """L-system style growth simulation for biologically-inspired tree generation"""

    bl_idname = "mt_GrowthNode"
    bl_label = "Growth"

    # Collapsible section states for inspector panel
    show_basic: bpy.props.BoolProperty(name="Basic", default=True)
    show_growth: bpy.props.BoolProperty(name="Growth Control", default=True)
    show_split: bpy.props.BoolProperty(name="Splitting", default=False)
    show_physics: bpy.props.BoolProperty(name="Physics", default=False)

    @property
    def tree_function(self):
        return lazy_m_tree.GrowthFunction

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)

        # Core parameters
        self.add_input(
            "mt_IntSocket",
            "Seed",
            min_value=0,
            property_name="seed",
            property_value=randint(0, 1000),
        )
        self.add_input(
            "mt_IntSocket", "Iterations", min_value=1, property_name="iterations", property_value=5
        )
        self.add_input(
            "mt_FloatSocket",
            "Branch Length",
            min_value=0.01,
            property_name="branch_length",
            property_value=1,
        )

        # Growth control
        self.add_input(
            "mt_FloatSocket",
            "Apical Dominance",
            min_value=0,
            max_value=1,
            property_name="apical_dominance",
            property_value=0.7,
        )
        self.add_input(
            "mt_FloatSocket",
            "Grow Threshold",
            min_value=0,
            max_value=1,
            property_name="grow_threshold",
            property_value=0.5,
        )
        self.add_input(
            "mt_FloatSocket",
            "Cut Threshold",
            min_value=0,
            max_value=1,
            property_name="cut_threshold",
            property_value=0.2,
        )

        # Splitting
        self.add_input(
            "mt_FloatSocket",
            "Split Threshold",
            min_value=0,
            max_value=1,
            property_name="split_threshold",
            property_value=0.7,
        )
        self.add_input(
            "mt_FloatSocket",
            "Split Angle",
            min_value=0,
            max_value=180,
            property_name="split_angle",
            property_value=60,
        )

        # Physical simulation
        self.add_input(
            "mt_FloatSocket", "Gravitropism", property_name="gravitropism", property_value=0.1
        )
        self.add_input(
            "mt_FloatSocket", "Gravity Strength", property_name="gravity_strength", property_value=1
        )
        self.add_input(
            "mt_FloatSocket",
            "Randomness",
            min_value=0,
            property_name="randomness",
            property_value=0.1,
        )

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

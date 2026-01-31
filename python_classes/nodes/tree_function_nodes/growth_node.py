from __future__ import annotations

from random import randint

import bpy

from ...m_tree_wrapper import lazy_m_tree
from ..base_types.node import MtreeFunctionNode

# Parameter groupings for organized UI
BASIC_PARAMS = ["seed", "iterations", "preview_iteration", "branch_length"]
GROWTH_PARAMS = ["apical_dominance", "grow_threshold", "cut_threshold"]
SPLIT_PARAMS = ["split_threshold", "split_angle"]
PHYSICS_PARAMS = ["gravitropism", "gravity_strength", "randomness"]
LATERAL_PARAMS = [
    "enable_lateral_branching",
    "lateral_start",
    "lateral_end",
    "lateral_density",
    "lateral_activation",
    "lateral_angle",
]
FLOWER_PARAMS = ["enable_flowering", "flower_threshold"]

# Parameter descriptions for tooltips
PARAM_DESCRIPTIONS = {
    "seed": "Random seed for reproducible results",
    "iterations": "Number of growth cycles (years of growth)",
    "preview_iteration": "Preview growth at this iteration (-1 for all)",
    "branch_length": "Length of each branch segment",
    "apical_dominance": "How much the main leader suppresses side branches (0=equal, 1=dominant)",
    "grow_threshold": "Minimum vigor for a meristem to grow",
    "cut_threshold": "Vigor below which branches are pruned",
    "split_threshold": "Vigor above which branches split",
    "split_angle": "Angle between split branches",
    "gravitropism": "Tendency to grow upward (negative=downward)",
    "gravity_strength": "How much branches bend under their weight",
    "randomness": "Random variation in branch direction",
    # Lateral branching
    "enable_lateral_branching": "Enable branches along parent stems (not just from tips)",
    "lateral_start": "Start position for lateral buds (0=base, 1=tip)",
    "lateral_end": "End position for lateral buds (0=base, 1=tip)",
    "lateral_density": "Potential branch points per unit length",
    "lateral_activation": "Vigor threshold to activate dormant buds",
    "lateral_angle": "Initial angle of lateral branches from parent",
    # Flowering
    "enable_flowering": "Create flower attachment points at low-vigor tips",
    "flower_threshold": "Vigor below which meristems become flower points (must be > cut threshold)",
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
    show_lateral: bpy.props.BoolProperty(name="Lateral Branching", default=True)
    show_flowering: bpy.props.BoolProperty(name="Flowering", default=False)

    # Minimum gap between cut_threshold and flower_threshold for flowering to work
    THRESHOLD_GAP = 0.05

    @property
    def tree_function(self):
        return lazy_m_tree.GrowthFunction

    def construct_function(self):
        """Override to validate threshold constraints before constructing the C++ function."""
        # Get current values from sockets
        cut_socket = self._get_socket_by_property("cut_threshold")
        flower_socket = self._get_socket_by_property("flower_threshold")
        flowering_socket = self._get_socket_by_property("enable_flowering")

        if cut_socket and flower_socket and flowering_socket:
            cut_val = cut_socket.property_value
            flower_val = flower_socket.property_value
            flowering_enabled = flowering_socket.property_value

            # Validate: flower_threshold must be > cut_threshold for flowering to work
            if flowering_enabled and flower_val <= cut_val:
                # Adjust flower_threshold to be above cut_threshold
                flower_socket.property_value = cut_val + self.THRESHOLD_GAP

        # Call parent implementation
        return super().construct_function()

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)

        # Basic parameters
        self.add_input(
            "mt_IntSocket",
            "Seed",
            min_value=0,
            property_name="seed",
            property_value=randint(0, 1000),
            description=PARAM_DESCRIPTIONS["seed"],
        )
        self.add_input(
            "mt_IntSocket",
            "Iterations",
            min_value=1,
            property_name="iterations",
            property_value=5,
            description=PARAM_DESCRIPTIONS["iterations"],
        )
        self.add_input(
            "mt_IntSocket",
            "Preview Iteration",
            min_value=-1,
            property_name="preview_iteration",
            property_value=-1,
            description=PARAM_DESCRIPTIONS["preview_iteration"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Branch Length",
            min_value=0.01,
            property_name="branch_length",
            property_value=1,
            description=PARAM_DESCRIPTIONS["branch_length"],
        )

        # Growth control
        self.add_input(
            "mt_FloatSocket",
            "Apical Dominance",
            min_value=0,
            max_value=1,
            property_name="apical_dominance",
            property_value=0.7,
            description=PARAM_DESCRIPTIONS["apical_dominance"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Grow Threshold",
            min_value=0,
            max_value=1,
            property_name="grow_threshold",
            property_value=0.5,
            description=PARAM_DESCRIPTIONS["grow_threshold"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Cut Threshold",
            min_value=0,
            max_value=1,
            property_name="cut_threshold",
            property_value=0.2,
            description=PARAM_DESCRIPTIONS["cut_threshold"],
        )

        # Splitting
        self.add_input(
            "mt_FloatSocket",
            "Split Threshold",
            min_value=0,
            max_value=1,
            property_name="split_threshold",
            property_value=0.7,
            description=PARAM_DESCRIPTIONS["split_threshold"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Split Angle",
            min_value=0,
            max_value=180,
            property_name="split_angle",
            property_value=60,
            description=PARAM_DESCRIPTIONS["split_angle"],
        )

        # Physical simulation
        self.add_input(
            "mt_FloatSocket",
            "Gravitropism",
            property_name="gravitropism",
            property_value=0.1,
            description=PARAM_DESCRIPTIONS["gravitropism"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Gravity Strength",
            property_name="gravity_strength",
            property_value=1,
            description=PARAM_DESCRIPTIONS["gravity_strength"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Randomness",
            min_value=0,
            property_name="randomness",
            property_value=0.1,
            description=PARAM_DESCRIPTIONS["randomness"],
        )

        # Lateral branching
        self.add_input(
            "mt_BoolSocket",
            "Enable Lateral Branching",
            property_name="enable_lateral_branching",
            property_value=True,
            description=PARAM_DESCRIPTIONS["enable_lateral_branching"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lateral Start",
            min_value=0,
            max_value=1,
            property_name="lateral_start",
            property_value=0.1,
            description=PARAM_DESCRIPTIONS["lateral_start"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lateral End",
            min_value=0,
            max_value=1,
            property_name="lateral_end",
            property_value=0.9,
            description=PARAM_DESCRIPTIONS["lateral_end"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lateral Density",
            min_value=0.1,
            property_name="lateral_density",
            property_value=2.0,
            description=PARAM_DESCRIPTIONS["lateral_density"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lateral Activation",
            min_value=0,
            max_value=1,
            property_name="lateral_activation",
            property_value=0.4,
            description=PARAM_DESCRIPTIONS["lateral_activation"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lateral Angle",
            min_value=0,
            max_value=90,
            property_name="lateral_angle",
            property_value=45,
            description=PARAM_DESCRIPTIONS["lateral_angle"],
        )

        # Flowering
        self.add_input(
            "mt_BoolSocket",
            "Enable Flowering",
            property_name="enable_flowering",
            property_value=False,
            description=PARAM_DESCRIPTIONS["enable_flowering"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Flower Threshold",
            min_value=0,
            max_value=1,
            property_name="flower_threshold",
            property_value=0.4,
            description=PARAM_DESCRIPTIONS["flower_threshold"],
        )

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

    def _get_socket_by_property(self, property_name: str):
        """Find input socket by property_name attribute."""
        for socket in self.inputs:
            if hasattr(socket, "property_name") and socket.property_name == property_name:
                return socket
        return None

    def apply_preset(self, preset_name: str):
        """Apply a preset by setting socket property values."""
        from ...presets import GROWTH_PRESETS

        preset = GROWTH_PRESETS.get(preset_name)
        if not preset:
            return

        for param_name, param_value in preset.items():
            socket = self._get_socket_by_property(param_name)
            if socket:
                socket.property_value = param_value

    def _draw_section(self, layout, title: str, show_prop: str, params: list) -> None:
        """Draw a collapsible section with parameters."""
        box = layout.box()
        row = box.row()
        show = getattr(self, show_prop)
        row.prop(
            self,
            show_prop,
            icon="TRIA_DOWN" if show else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text=title)

        if show:
            for param in params:
                socket = self._get_socket_by_property(param)
                if socket and socket.is_property:
                    col = box.column()
                    socket.draw(bpy.context, col, self, socket.name)
                    # Add description as sub-label
                    if param in PARAM_DESCRIPTIONS:
                        sub = col.row()
                        sub.scale_y = 0.6
                        sub.label(text=f"  {PARAM_DESCRIPTIONS[param]}")

    def draw_inspector(self, context, layout):
        """Draw organized parameters in the Properties panel (N key)."""
        # Preset buttons
        box = layout.box()
        box.label(text="Presets", icon="PRESET")
        row = box.row(align=True)
        for preset_name in ["STRUCTURED", "SPREADING"]:
            op = row.operator("mtree.apply_growth_node_preset", text=preset_name.capitalize())
            op.preset = preset_name
            op.node_tree_name = self.id_data.name
            op.node_name = self.name
        row = box.row(align=True)
        for preset_name in ["WEEPING", "GNARLED"]:
            op = row.operator("mtree.apply_growth_node_preset", text=preset_name.capitalize())
            op.preset = preset_name
            op.node_tree_name = self.id_data.name
            op.node_name = self.name

        # Parameter sections
        self._draw_section(layout, "Basic", "show_basic", BASIC_PARAMS)
        self._draw_section(layout, "Growth Control", "show_growth", GROWTH_PARAMS)
        self._draw_section(layout, "Splitting", "show_split", SPLIT_PARAMS)
        self._draw_section(layout, "Physics", "show_physics", PHYSICS_PARAMS)
        self._draw_section(layout, "Lateral Branching", "show_lateral", LATERAL_PARAMS)
        self._draw_section(layout, "Flowering", "show_flowering", FLOWER_PARAMS)

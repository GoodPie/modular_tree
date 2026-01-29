from __future__ import annotations

from random import randint

import bpy

from ...m_tree_wrapper import lazy_m_tree
from ..base_types.node import MtreeFunctionNode

# Parameter groupings for organized UI
BASIC_PARAMS = ["seed", "length", "start_radius", "end_radius"]
SHAPE_PARAMS = ["shape", "up_attraction", "resolution", "randomness"]

# Parameter descriptions for tooltips
PARAM_DESCRIPTIONS = {
    "seed": "Random seed for reproducible results",
    "length": "Total length of the trunk",
    "start_radius": "Trunk radius at the base",
    "end_radius": "Trunk radius at the tip",
    "shape": "Controls radius falloff curve (lower = more taper near base)",
    "up_attraction": "Tendency to grow upward vs. wandering",
    "resolution": "Number of segments per unit length",
    "randomness": "Amount of random variation in trunk direction",
}


class TrunkNode(bpy.types.Node, MtreeFunctionNode):
    bl_idname = "mt_TrunkNode"
    bl_label = "Trunk"

    # Collapsible section states for inspector panel
    show_basic: bpy.props.BoolProperty(name="Basic", default=True)
    show_shape: bpy.props.BoolProperty(name="Shape", default=True)

    @property
    def tree_function(self):
        return lazy_m_tree.TrunkFunction

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)
        self.add_input(
            "mt_IntSocket",
            "Seed",
            min_value=0,
            property_name="seed",
            property_value=randint(0, 1000),
            description=PARAM_DESCRIPTIONS["seed"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Length",
            min_value=0,
            property_name="length",
            property_value=14,
            description=PARAM_DESCRIPTIONS["length"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Start Radius",
            min_value=0.0001,
            property_name="start_radius",
            property_value=0.3,
            description=PARAM_DESCRIPTIONS["start_radius"],
        )
        self.add_input(
            "mt_FloatSocket",
            "End Radius",
            min_value=0.0001,
            property_name="end_radius",
            property_value=0.05,
            description=PARAM_DESCRIPTIONS["end_radius"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Shape",
            min_value=0.0001,
            property_name="shape",
            property_value=0.7,
            description=PARAM_DESCRIPTIONS["shape"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Up Attraction",
            property_name="up_attraction",
            property_value=0.6,
            description=PARAM_DESCRIPTIONS["up_attraction"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Resolution",
            min_value=0.0001,
            property_name="resolution",
            property_value=3,
            description=PARAM_DESCRIPTIONS["resolution"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Randomness",
            property_name="randomness",
            property_value=1,
            description=PARAM_DESCRIPTIONS["randomness"],
        )

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

    def _get_socket_by_property(self, property_name: str):
        """Find input socket by property_name attribute."""
        for socket in self.inputs:
            if hasattr(socket, "property_name") and socket.property_name == property_name:
                return socket
        return None

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
        for preset_name in ["OAK", "PINE", "WILLOW"]:
            op = row.operator("mtree.apply_trunk_node_preset", text=preset_name.capitalize())
            op.preset = preset_name
            op.node_tree_name = self.id_data.name
            op.node_name = self.name

        # Parameter sections
        self._draw_section(layout, "Basic", "show_basic", BASIC_PARAMS)
        self._draw_section(layout, "Shape", "show_shape", SHAPE_PARAMS)

    def apply_preset(self, preset_name: str):
        """Apply a preset's trunk parameters by setting socket property values."""
        from ...presets import _DEFAULT_TRUNK_PARAMS, TREE_PRESETS

        if preset_name == "RANDOM":
            return  # Trunk doesn't vary randomly

        preset = TREE_PRESETS.get(preset_name)
        params = {**_DEFAULT_TRUNK_PARAMS}
        if preset and preset.trunk:
            params.update(preset.trunk)

        for param_name, param_value in params.items():
            socket = self._get_socket_by_property(param_name)
            if socket:
                socket.property_value = float(param_value)


from __future__ import annotations

from random import randint
import bpy
from ..base_types.node import MtreeFunctionNode
from ...m_tree_wrapper import lazy_m_tree

# Parameter groupings for organized UI
BASIC_PARAMS = ['seed', 'start', 'end', 'length', 'branches_density', 'start_angle']
SHAPE_PARAMS = ['randomness', 'flatness', 'up_attraction', 'gravity_strength', 'stiffness']
SPLIT_PARAMS = ['split_proba', 'split_radius', 'split_angle', 'phillotaxis']
ADVANCED_PARAMS = ['break_chance', 'resolution', 'start_radius']

# Parameter descriptions for tooltips
PARAM_DESCRIPTIONS = {
    'seed': "Random seed for reproducible results",
    'start': "Position along parent where branches start (0=base, 1=tip)",
    'end': "Position along parent where branches end (0=base, 1=tip)",
    'length': "Maximum length of branches",
    'branches_density': "Number of branches per unit length",
    'start_angle': "Angle between branch and parent at the base",
    'randomness': "Amount of random variation in branch direction",
    'flatness': "Horizontal spread (0=spherical, 1=flat canopy)",
    'up_attraction': "Tendency to grow upward (negative values droop)",
    'gravity_strength': "How much branches bend under their weight",
    'stiffness': "Resistance to bending from gravity",
    'split_proba': "Probability of a branch splitting into two",
    'split_radius': "Minimum radius for splits to occur",
    'split_angle': "Angle between split branches",
    'phillotaxis': "Spiral angle between branches (137.5 is golden angle)",
    'break_chance': "Probability of a branch breaking/stopping",
    'resolution': "Number of segments per unit length",
    'start_radius': "Branch radius at base relative to parent",
}


class BranchNode(bpy.types.Node, MtreeFunctionNode):
    bl_idname = "mt_BranchNode"
    bl_label = "Branches"

    # Collapsible section states for inspector panel
    show_basic: bpy.props.BoolProperty(name="Basic", default=True)
    show_shape: bpy.props.BoolProperty(name="Shape", default=True)
    show_split: bpy.props.BoolProperty(name="Splitting", default=False)
    show_advanced: bpy.props.BoolProperty(name="Advanced", default=False)

    @property
    def tree_function(self):
        return lazy_m_tree.BranchFunction

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)

        # Basic parameters
        self.add_input("mt_IntSocket", "Seed", min_value=0, property_name="seed", property_value=randint(0, 1000))
        self.add_input("mt_FloatSocket", "Start", min_value=0, max_value=1, property_name="start", property_value=.1)
        self.add_input("mt_FloatSocket", "End", min_value=0, max_value=1, property_name="end", property_value=.95)
        self.add_input("mt_PropertySocket", "Length", min_value=0, property_name="length", property_value=9)
        self.add_input("mt_FloatSocket", "Density", min_value=0.0001, property_name="branches_density", property_value=2)
        self.add_input("mt_PropertySocket", "Start Angle", min_value=0, max_value=180, property_name="start_angle", property_value=45)

        # Shape parameters
        self.add_input("mt_PropertySocket", "Randomness", min_value=0.0001, property_name="randomness", property_value=.5)
        self.add_input("mt_FloatSocket", "Flatness", min_value=0, max_value=1, property_name="flatness", property_value=0.2)
        self.add_input("mt_FloatSocket", "Up Attraction", property_name="up_attraction", property_value=.25)
        self.add_input("mt_FloatSocket", "Gravity", property_name="gravity_strength", property_value=10)
        self.add_input("mt_FloatSocket", "Stiffness", property_name="stiffness", property_value=.1)

        # Split parameters
        self.add_input("mt_FloatSocket", "Split Chance", min_value=0, max_value=1, property_name="split_proba", property_value=.5)
        self.add_input("mt_FloatSocket", "Split Radius", min_value=0.0001, property_name="split_radius", property_value=.8)
        self.add_input("mt_FloatSocket", "Split Angle", min_value=0, max_value=180, property_name="split_angle", property_value=35.)
        self.add_input("mt_FloatSocket", "Phillotaxis", min_value=0, max_value=360, property_name="phillotaxis", property_value=137.5)

        # Advanced parameters
        self.add_input("mt_FloatSocket", "Break Chance", min_value=0, property_name="break_chance", property_value=.02)
        self.add_input("mt_FloatSocket", "Resolution", min_value=0.0001, property_name="resolution", property_value=3)
        self.add_input("mt_PropertySocket", "Start Radius", min_value=0.0001, property_name="start_radius", property_value=.4)

        self.add_output("mt_TreeSocket", "Tree", is_property=False)

    def _get_socket_by_property(self, property_name: str):
        """Find input socket by property_name attribute."""
        for socket in self.inputs:
            if hasattr(socket, 'property_name') and socket.property_name == property_name:
                return socket
        return None

    def _draw_section(self, layout, title: str, show_prop: str, params: list) -> None:
        """Draw a collapsible section with parameters."""
        box = layout.box()
        row = box.row()
        show = getattr(self, show_prop)
        row.prop(self, show_prop, icon='TRIA_DOWN' if show else 'TRIA_RIGHT',
                 icon_only=True, emboss=False)
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
        self._draw_section(layout, "Basic", "show_basic", BASIC_PARAMS)
        self._draw_section(layout, "Shape", "show_shape", SHAPE_PARAMS)
        self._draw_section(layout, "Splitting", "show_split", SPLIT_PARAMS)
        self._draw_section(layout, "Advanced", "show_advanced", ADVANCED_PARAMS)
        

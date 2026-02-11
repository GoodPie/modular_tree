"""Leaf shape generation node for the Mtree node editor."""

from __future__ import annotations

import bpy

from ...m_tree_wrapper import lazy_m_tree as m_tree
from ...mesh_utils import create_leaf_mesh_from_cpp
from ...presets.leaf_presets import LEAF_PRESETS
from ..base_types.node import MtreeFunctionNode, MtreeNode

# Socket parameter definitions for organized access
CONTOUR_PARAMS = ["m", "a", "b", "n1", "n2", "n3", "aspect_ratio"]
MARGIN_PARAMS = ["tooth_count", "tooth_depth", "tooth_sharpness"]
VENATION_PARAMS = ["vein_density", "kill_distance", "attraction_distance", "growth_step_size"]
SURFACE_PARAMS = ["midrib_curvature", "cross_curvature", "vein_displacement", "edge_curl"]

# Parameter descriptions for tooltips
PARAM_DESCRIPTIONS = {
    # Contour
    "m": "Number of lobes or points on the leaf outline. 2 = simple leaf, 3 = clover-like, 5 = star-shaped",
    "a": "Stretches the shape horizontally. Increase for a wider silhouette",
    "b": "Stretches the shape vertically. Increase for a taller silhouette",
    "n1": "Overall roundness. Low values = puffy and rounded, high values = thin and spiky",
    "n2": "Shape of each lobe. Low = bulging lobes, high = pinched angular lobes",
    "n3": "Secondary lobe shaping. Adjust relative to Lobe Shape A for asymmetric lobes",
    "aspect_ratio": "Width-to-height ratio. 0.5 = twice as long as wide, 1.0 = equal, 2.0 = wider than tall",
    # Margin
    "tooth_count": "Number of teeth or scallops along the leaf edge",
    "tooth_depth": "How deep the teeth cut into the leaf contour",
    "tooth_sharpness": "How pointed vs. rounded the teeth are",
    # Venation
    "vein_density": "Number of growth attractors scattered inside the leaf. Higher = denser vein network",
    "kill_distance": "How close a vein must grow to an attractor to consume it. Smaller = finer detail",
    "attraction_distance": "How far away an attractor can influence vein growth direction",
    "growth_step_size": "Length of each vein growth step. Smaller = smoother veins but slower generation",
    # Surface
    "midrib_curvature": "Bends the leaf along its central vein, like a taco shell",
    "cross_curvature": "Cups the leaf perpendicular to the midrib",
    "vein_displacement": "Raises the surface along vein paths. Requires venation enabled",
    "edge_curl": "Curls the leaf edges upward (positive) or downward (negative)",
}


_REVERSE_MARGIN_MAP = {0: "ENTIRE", 1: "SERRATE", 2: "DENTATE", 3: "CRENATE", 4: "LOBED"}
_REVERSE_VENATION_MAP = {0: "OPEN", 1: "CLOSED"}


class LeafShapeNode(bpy.types.Node, MtreeNode):
    bl_idname = "mt_LeafShapeNode"
    bl_label = "Leaf Shape"

    # Section toggles
    show_contour: bpy.props.BoolProperty(name="Contour", default=True)
    show_venation: bpy.props.BoolProperty(name="Venation", default=False)
    show_surface: bpy.props.BoolProperty(name="Surface", default=False)

    # Generated object reference
    leaf_object: bpy.props.StringProperty(name="Leaf Object")

    # Margin type enum
    margin_type: bpy.props.EnumProperty(
        name="Margin Type",
        items=[
            ("ENTIRE", "Entire", "Smooth edge"),
            ("SERRATE", "Serrate", "Saw-like teeth"),
            ("DENTATE", "Dentate", "Outward teeth"),
            ("CRENATE", "Crenate", "Rounded scallops"),
            ("LOBED", "Lobed", "Deep rounded lobes"),
        ],
        default="ENTIRE",
    )

    # Venation controls
    enable_venation: bpy.props.BoolProperty(name="Enable Venation", default=False)
    venation_type: bpy.props.EnumProperty(
        name="Venation Type",
        items=[
            ("OPEN", "Open", "Tree-like branching (dicot pattern)"),
            ("CLOSED", "Closed", "Looped/anastomosing network"),
        ],
        default="OPEN",
    )

    # Status feedback
    status_message: bpy.props.StringProperty(default="")
    status_is_error: bpy.props.BoolProperty(default=False)

    _MARGIN_TYPE_MAP = {
        "ENTIRE": "Entire",
        "SERRATE": "Serrate",
        "DENTATE": "Dentate",
        "CRENATE": "Crenate",
        "LOBED": "Lobed",
    }

    _VENATION_TYPE_MAP = {
        "OPEN": "Open",
        "CLOSED": "Closed",
    }

    def init(self, context):
        # Tree I/O
        self.add_input("mt_TreeSocket", "Tree", is_property=False)
        self.add_output("mt_TreeSocket", "Tree", is_property=False)

        # Contour sockets
        self.add_input(
            "mt_FloatSocket",
            "Lobes",
            property_name="m",
            property_value=2.0,
            min_value=1.0,
            max_value=20.0,
            description=PARAM_DESCRIPTIONS["m"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Horizontal Stretch",
            property_name="a",
            property_value=1.0,
            min_value=0.01,
            max_value=5.0,
            description=PARAM_DESCRIPTIONS["a"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Vertical Stretch",
            property_name="b",
            property_value=1.0,
            min_value=0.01,
            max_value=5.0,
            description=PARAM_DESCRIPTIONS["b"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Roundness",
            property_name="n1",
            property_value=3.0,
            min_value=0.1,
            max_value=50.0,
            description=PARAM_DESCRIPTIONS["n1"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lobe Shape A",
            property_name="n2",
            property_value=3.0,
            min_value=0.1,
            max_value=50.0,
            description=PARAM_DESCRIPTIONS["n2"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Lobe Shape B",
            property_name="n3",
            property_value=3.0,
            min_value=0.1,
            max_value=50.0,
            description=PARAM_DESCRIPTIONS["n3"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Aspect Ratio",
            property_name="aspect_ratio",
            property_value=0.5,
            min_value=0.01,
            max_value=2.0,
            description=PARAM_DESCRIPTIONS["aspect_ratio"],
        )
        # Margin sockets
        self.add_input(
            "mt_IntSocket",
            "Tooth Count",
            property_name="tooth_count",
            property_value=0,
            min_value=0,
            max_value=50,
            description=PARAM_DESCRIPTIONS["tooth_count"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Tooth Depth",
            property_name="tooth_depth",
            property_value=0.1,
            min_value=0.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["tooth_depth"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Tooth Sharpness",
            property_name="tooth_sharpness",
            property_value=0.5,
            min_value=0.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["tooth_sharpness"],
        )
        # Venation sockets
        self.add_input(
            "mt_FloatSocket",
            "Vein Density",
            property_name="vein_density",
            property_value=800.0,
            min_value=0.0,
            max_value=5000.0,
            description=PARAM_DESCRIPTIONS["vein_density"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Kill Distance",
            property_name="kill_distance",
            property_value=0.03,
            min_value=0.001,
            max_value=0.5,
            description=PARAM_DESCRIPTIONS["kill_distance"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Attraction Distance",
            property_name="attraction_distance",
            property_value=0.08,
            min_value=0.01,
            max_value=0.5,
            description=PARAM_DESCRIPTIONS["attraction_distance"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Growth Step Size",
            property_name="growth_step_size",
            property_value=0.01,
            min_value=0.001,
            max_value=0.1,
            description=PARAM_DESCRIPTIONS["growth_step_size"],
        )
        # Surface sockets
        self.add_input(
            "mt_FloatSocket",
            "Midrib Curvature",
            property_name="midrib_curvature",
            property_value=0.0,
            min_value=-1.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["midrib_curvature"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Cross Curvature",
            property_name="cross_curvature",
            property_value=0.0,
            min_value=-1.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["cross_curvature"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Vein Displacement",
            property_name="vein_displacement",
            property_value=0.0,
            min_value=-1.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["vein_displacement"],
        )
        self.add_input(
            "mt_FloatSocket",
            "Edge Curl",
            property_name="edge_curl",
            property_value=0.0,
            min_value=-1.0,
            max_value=1.0,
            description=PARAM_DESCRIPTIONS["edge_curl"],
        )

    def generate_leaf(self):
        """Create or update leaf mesh object from current parameters."""
        import time

        self.status_message = ""
        self.status_is_error = False

        try:
            start_time = time.time()

            gen = m_tree.LeafShapeGenerator()

            # Set superformula parameters from sockets
            for input_socket in self.inputs:
                if not hasattr(input_socket, "is_property") or not input_socket.is_property:
                    continue
                prop_name = input_socket.property_name
                if hasattr(gen, prop_name):
                    setattr(gen, prop_name, input_socket.property_value)

            # Set margin type from enum property
            margin_name = self._MARGIN_TYPE_MAP.get(self.margin_type, "Entire")
            gen.margin_type = getattr(m_tree.MarginType, margin_name)

            # Set venation parameters
            gen.enable_venation = self.enable_venation
            if self.enable_venation:
                venation_name = self._VENATION_TYPE_MAP.get(self.venation_type, "Open")
                gen.venation_type = getattr(m_tree.VenationType, venation_name)

            cpp_mesh = gen.generate()

            # Get or create Blender object
            leaf_obj = self._get_or_create_leaf_object()
            leaf_mesh = leaf_obj.data
            leaf_mesh.clear_geometry()

            create_leaf_mesh_from_cpp(leaf_mesh, cpp_mesh)
            self.leaf_object = leaf_obj.name

            elapsed = time.time() - start_time
            self.status_message = f"Generated in {elapsed:.3f}s"
            self.status_is_error = False

        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            self.status_is_error = True

    def _get_or_create_leaf_object(self):
        """Get existing leaf object or create a new one in MTree_Resources."""
        if self.leaf_object:
            obj = bpy.data.objects.get(self.leaf_object)
            if obj is not None:
                return obj

        # Create new mesh and object
        leaf_mesh = bpy.data.meshes.new("leaf")
        leaf_obj = bpy.data.objects.new("leaf", leaf_mesh)

        # Add to MTree_Resources collection (ensure visible for procedural leaves)
        collection = bpy.data.collections.get("MTree_Resources")
        if collection is None:
            collection = bpy.data.collections.new("MTree_Resources")
            bpy.context.scene.collection.children.link(collection)
        collection.hide_viewport = False
        collection.hide_render = False
        collection.objects.link(leaf_obj)

        return leaf_obj

    def apply_preset(self, preset_name: str):
        """Apply species preset to all sockets."""
        preset = LEAF_PRESETS.get(preset_name)
        if not preset:
            return

        # Set contour parameters
        for key, value in preset.contour.items():
            socket = self._get_socket_by_property(key)
            if socket:
                socket.property_value = float(value)

        # Set margin type
        margin_type_int = preset.margin.get("margin_type", 0)
        self.margin_type = _REVERSE_MARGIN_MAP.get(margin_type_int, "ENTIRE")

        # Set margin socket values
        for key in ["tooth_count", "tooth_depth", "tooth_sharpness"]:
            if key in preset.margin:
                socket = self._get_socket_by_property(key)
                if socket:
                    socket.property_value = float(preset.margin[key])

        # Set venation parameters
        if "enable_venation" in preset.venation:
            self.enable_venation = bool(preset.venation["enable_venation"])
        if "venation_type" in preset.venation:
            vtype = preset.venation["venation_type"]
            self.venation_type = _REVERSE_VENATION_MAP.get(vtype, "OPEN")
        for key in ["vein_density", "kill_distance", "attraction_distance", "growth_step_size"]:
            if key in preset.venation:
                socket = self._get_socket_by_property(key)
                if socket:
                    socket.property_value = float(preset.venation[key])

        # Set deformation parameters
        for key, value in preset.deformation.items():
            socket = self._get_socket_by_property(key)
            if socket:
                socket.property_value = float(value)

    def _get_socket_by_property(self, property_name: str):
        """Find input socket by property_name attribute."""
        for socket in self.inputs:
            if hasattr(socket, "property_name") and socket.property_name == property_name:
                return socket
        return None

    def draw(self, context, layout):
        """Compact node view."""
        if self.status_message:
            status_row = layout.row()
            status_row.alert = self.status_is_error
            icon = "ERROR" if self.status_is_error else "CHECKMARK"
            status_row.label(text=self.status_message, icon=icon)

        op = layout.operator("mtree.generate_leaf", text="Generate Leaf")
        op.node_tree_name = self.get_node_tree().name
        op.node_name = self.name

        if self.leaf_object:
            layout.label(text=f"Object: {self.leaf_object}")

        layout.prop(self, "margin_type", text="Margin")
        layout.prop(self, "enable_venation", text="Venation")

    def draw_inspector(self, context, layout):
        """Full inspector panel (N key)."""
        # Preset buttons row
        box = layout.box()
        box.label(text="Presets", icon="PRESET")
        row = box.row(align=True)
        for preset_name in ["OAK", "MAPLE", "BIRCH", "WILLOW", "PINE"]:
            op = row.operator(
                "mtree.apply_leaf_preset",
                text=preset_name.capitalize(),
            )
            op.preset = preset_name
            op.node_tree_name = self.get_node_tree().name
            op.node_name = self.name

        # Contour section
        self._draw_section(layout, "Contour", "show_contour", CONTOUR_PARAMS)

        # Margin type dropdown in its own box
        box = layout.box()
        box.prop(self, "margin_type", text="Margin Type")
        for param in MARGIN_PARAMS:
            socket = self._get_socket_by_property(param)
            if socket and socket.is_property:
                socket.draw(context, box, self, socket.name)

        # Venation section
        box = layout.box()
        row = box.row()
        show_ven = self.show_venation
        row.prop(
            self,
            "show_venation",
            icon="TRIA_DOWN" if show_ven else "TRIA_RIGHT",
            icon_only=True,
            emboss=False,
        )
        row.label(text="Venation")

        if show_ven:
            box.prop(self, "enable_venation")
            if self.enable_venation:
                box.prop(self, "venation_type")
                for param in VENATION_PARAMS:
                    socket = self._get_socket_by_property(param)
                    if socket and socket.is_property:
                        socket.draw(context, box, self, socket.name)

        # Surface deformation section
        self._draw_section(layout, "Surface", "show_surface", SURFACE_PARAMS)

    def _draw_section(self, layout, title: str, show_prop: str, params: list):
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
                    socket.draw(bpy.context, box, self, socket.name)

    def construct_function(self):
        """Pass-through: leaf shape nodes don't create tree functions."""
        # Pass through to child nodes
        for child in self.get_child_nodes():
            if isinstance(child, MtreeFunctionNode):
                return child.construct_function()
        return None

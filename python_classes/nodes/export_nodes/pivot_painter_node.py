from __future__ import annotations

import bpy

from ..base_types.node import MtreeNode


class MTreePivotPainterExport(bpy.types.Node, MtreeNode):
    """Export Pivot Painter 2.0 data for game engines (UE4, UE5, Unity)"""

    bl_idname = "mt_PivotPainterExportNode"
    bl_label = "Pivot Painter Export"

    export_format: bpy.props.EnumProperty(
        name="Format",
        items=[
            ("UE5", "Unreal Engine 5", "Export for UE5 with Nanite support"),
            ("UE4", "Unreal Engine 4", "Export for UE4 Pivot Painter 2.0"),
            ("UNITY", "Unity", "Export vertex colors for Unity"),
        ],
        default="UE5",
    )
    texture_size: bpy.props.IntProperty(name="Texture Size", default=1024, min=64, max=4096)
    export_path: bpy.props.StringProperty(
        name="Export Path",
        subtype="DIR_PATH",
        default="//pivot_painter/",
    )

    # Status feedback
    status_message: bpy.props.StringProperty(default="")
    status_is_error: bpy.props.BoolProperty(default=False)

    def init(self, context):
        self.add_input("mt_TreeSocket", "Tree", is_property=False)

    def draw(self, context, layout):
        # Show status message if present
        if self.status_message:
            status_row = layout.row()
            status_row.alert = self.status_is_error
            icon = "ERROR" if self.status_is_error else "CHECKMARK"
            status_row.label(text=self.status_message, icon=icon)

        layout.prop(self, "export_format")

        if self.export_format != "UNITY":
            layout.prop(self, "texture_size")
            layout.prop(self, "export_path")

        # Export button
        export_row = layout.row()
        export_row.enabled = self._has_valid_input()
        props = export_row.operator("mtree.node_function", text="Export")
        props.node_tree_name = self.get_node_tree().name
        props.node_name = self.name
        props.function_name = "do_export"

    def _has_valid_input(self):
        """Check if we have a valid tree input connected."""
        if len(self.inputs) == 0:
            return False
        tree_input = self.inputs[0]
        return tree_input.links

    def _get_tree_object(self):
        """Get the tree object from the connected mesher node."""
        if not self._has_valid_input():
            return None

        # Walk back to find the mesher node
        mesher = self.get_mesher()
        if mesher is None:
            return None

        if not hasattr(mesher, "tree_object") or not mesher.tree_object:
            return None

        return bpy.data.objects.get(mesher.tree_object)

    def do_export(self):
        """Execute the pivot painter export."""
        self.status_message = ""
        self.status_is_error = False

        obj = self._get_tree_object()
        if obj is None:
            self.status_message = "No tree object found. Generate tree first."
            self.status_is_error = True
            return

        # Use the export operator
        result = bpy.ops.mtree.export_pivot_painter(
            "EXEC_DEFAULT",
            object_name=obj.name,
            export_format=self.export_format,
            texture_size=self.texture_size,
            export_path=self.export_path,
        )

        if result == {"FINISHED"}:
            self.status_message = f"Exported for {self.export_format}"
            self.status_is_error = False
        else:
            self.status_message = "Export failed"
            self.status_is_error = True

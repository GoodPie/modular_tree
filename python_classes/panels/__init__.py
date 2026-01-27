from __future__ import annotations

import bpy
from bpy.utils import register_class, unregister_class


class MTREE_PT_QuickGenerate(bpy.types.Panel):
    """Quick tree generation panel in the 3D View sidebar"""

    bl_label = "MTree"
    bl_idname = "MTREE_PT_quick_generate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MTree"

    def draw(self, context):
        layout = self.layout

        # Quick generate section
        box = layout.box()
        box.label(text="Quick Generate", icon="OUTLINER_OB_MESH")
        box.operator("mtree.quick_generate", text="Generate Tree")

        # Tips section
        layout.separator()
        box = layout.box()
        box.label(text="Advanced Options", icon="NODETREE")
        row = box.row()
        row.label(text="Use the MTree Node Editor")
        row = box.row()
        row.label(text="for full control over")
        row = box.row()
        row.label(text="tree parameters.")


def register():
    register_class(MTREE_PT_QuickGenerate)


def unregister():
    unregister_class(MTREE_PT_QuickGenerate)

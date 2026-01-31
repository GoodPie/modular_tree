import bpy

from ..base_types.socket import MtreeSocket


class MtreeBoolSocket(bpy.types.NodeSocket, MtreeSocket):
    bl_idname = "mt_BoolSocket"
    bl_label = "Mtree Bool Socket"

    color = (0.8, 0.8, 0.2, 0.5)

    def update_value(self, context):
        mesher = self.node.get_mesher()
        if mesher is not None:
            mesher.build_tree()

    property_value: bpy.props.BoolProperty(default=True, update=update_value)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "property_value", text=text)

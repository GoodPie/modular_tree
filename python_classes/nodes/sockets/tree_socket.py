import bpy

from ..base_types.socket import MtreeSocket
from ..debounce import schedule_build


class TreeSocket(bpy.types.NodeSocket, MtreeSocket):
    bl_idname = "mt_TreeSocket"
    bl_label = "Tree Socket"

    color = (0.2, 0.7, 0.2, 1)

    def update_value(self, context):
        mesher = self.node.get_mesher()
        if mesher is not None:
            schedule_build(mesher)
        else:
            auto_method = getattr(self.node, "auto_build_method", None)
            if auto_method:
                schedule_build(self.node, method=auto_method)

    def draw(self, context, layout, node, text):
        layout.label(text=text)

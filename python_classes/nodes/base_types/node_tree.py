import bpy


class MtreeNodeTree(bpy.types.NodeTree):
    bl_idname = "mt_MtreeNodeTree"
    bl_label = "Mtree"
    bl_icon = "ONIONSKIN_ON"

    def update(self):
        """Called when links or topology change."""
        # Import here to avoid circular imports
        from ..debounce import schedule_build

        for node in self.nodes:
            if node.bl_idname == "mt_MesherNode":
                schedule_build(node)
                break

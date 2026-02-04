import bpy


class MtreeNodeTree(bpy.types.NodeTree):
    bl_idname = "mt_MtreeNodeTree"
    bl_label = "Mtree"
    bl_icon = "ONIONSKIN_ON"

    def update(self):
        """Called when links or topology change."""
        # Import here to avoid circular imports
        from ..tree_function_nodes.tree_mesher_node import debounced_build

        for node in self.nodes:
            if node.bl_idname == "mt_MesherNode":
                if getattr(node, "auto_update", True):
                    debounced_build(node)
                break

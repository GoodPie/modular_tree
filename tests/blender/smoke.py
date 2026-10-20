"""Smoke test that runs inside real Blender with the packaged extension installed.

    blender --command extension install-file -r user_default modular_tree-<version>-linux_x64.zip
    blender -b --factory-startup --python-exit-code 1 --python tests/blender/smoke.py

Any failed assert makes Blender exit with code 1.
"""

import os
import tempfile

import addon_utils
import bpy


def evaluated_vertex_count(ob):
    return len(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices)


assert addon_utils.enable("bl_ext.user_default.modular_tree"), "extension failed to enable"

# Quick Generate with leaves: needs the m_tree wheel and the leaves modifier inputs (#37).
assert bpy.ops.mtree.quick_generate(preset="OAK", seed=1, add_leaves=True) == {"FINISHED"}
quick_tree = bpy.context.view_layer.objects.active
assert len(quick_tree.data.vertices) > 0, "quick generate made an empty mesh"
assert evaluated_vertex_count(quick_tree) > len(quick_tree.data.vertices), "no leaves instanced"

# Node editor path: Tree Mesher -> Trunk -> Branches, then Add Leaves.
tree = bpy.data.node_groups.new("SmokeTree", "mt_MtreeNodeTree")
mesher = tree.nodes.new("mt_MesherNode")
trunk = tree.nodes.new("mt_TrunkNode")
branches = tree.nodes.new("mt_BranchNode")
tree.links.new(mesher.outputs["Tree"], trunk.inputs["Tree"])
tree.links.new(trunk.outputs["Tree"], branches.inputs["Tree"])
mesher.build_tree()  # timers never fire in background mode, so build directly
assert not mesher.status_is_error, mesher.status_message
node_tree_ob = bpy.data.objects[mesher.tree_object]
assert len(node_tree_ob.data.vertices) > 0, "node tree made an empty mesh"
assert bpy.ops.mtree.add_leaves(object_id=node_tree_ob.name) == {"FINISHED"}
assert evaluated_vertex_count(node_tree_ob) > len(node_tree_ob.data.vertices), "no leaves instanced"

# The MTree node tree must survive save + reopen (#38).
path = os.path.join(tempfile.mkdtemp(), "smoke.blend")
bpy.ops.wm.save_as_mainfile(filepath=path)
bpy.ops.wm.open_mainfile(filepath=path)
assert "SmokeTree" in bpy.data.node_groups, "MTree node tree lost after save and reopen"

print(f"Modular Tree smoke test passed on Blender {bpy.app.version_string}")

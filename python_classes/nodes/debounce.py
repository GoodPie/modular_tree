"""Debounced tree rebuild and socket-change polling.

Blender does not reliably fire `update` callbacks on NodeSocket properties,
so we poll for value changes using bpy.app.timers and funnel detected
changes through the existing debounce mechanism.
"""

import logging

import bpy

logger = logging.getLogger(__name__)

_pending_timers = {}  # {(tree_name, node_name): timer_func}
_socket_value_cache = {}  # {(tree_name, node_name, socket_name): value}
_node_prop_cache = {}  # {(tree_name, node_name, prop_name): value}

DEBOUNCE_DELAY = 0.3  # seconds of inactivity before rebuild
POLL_INTERVAL = 0.1  # seconds between socket-value polls

# Node properties that should trigger auto-update when changed.
# Maps bl_idname -> list of property names to watch.
_WATCHED_NODE_PROPS = {
    "mt_LeafShapeNode": ["margin_type", "enable_venation", "venation_type"],
    "mt_BranchNode": ["crown_shape", "angle_variation"],
}


def schedule_build(node, method="build_tree", delay=DEBOUNCE_DELAY):
    """Schedule a debounced method call on *node*. Resets on each invocation."""
    if not getattr(node, "auto_update", True):
        return

    key = (node.id_data.name, node.name)

    # Cancel existing timer for this key
    existing = _pending_timers.get(key)
    if existing is not None:
        try:
            bpy.app.timers.unregister(existing)
        except ValueError:
            logger.debug("Timer already expired for node %s", node.name)
        del _pending_timers[key]

    def _do_build():
        _pending_timers.pop(key, None)
        node_tree = bpy.data.node_groups.get(key[0])
        if node_tree:
            resolved = node_tree.nodes.get(key[1])
            if resolved:
                getattr(resolved, method)()
        return None

    _pending_timers[key] = _do_build
    bpy.app.timers.register(_do_build, first_interval=delay)


# -- Socket-change polling ---------------------------------------------------


def _on_socket_changed(node):
    """Route a detected socket change to the right build target."""
    mesher = node.get_mesher()
    if mesher is not None:
        schedule_build(mesher)
    else:
        auto_method = getattr(node, "auto_build_method", None)
        if auto_method:
            schedule_build(node, method=auto_method)


def _on_node_prop_changed(node):
    """Route a detected node-property change to the right build target."""
    auto_method = getattr(node, "auto_build_method", None)
    if auto_method:
        schedule_build(node, method=auto_method)
    else:
        mesher = node.get_mesher()
        if mesher is not None:
            schedule_build(mesher)


def _poll_socket_changes():
    """Timer callback: scan MTree node trees for socket value changes."""
    try:
        for nt in bpy.data.node_groups:
            if nt.bl_idname != "mt_MtreeNodeTree":
                continue
            for node in nt.nodes:
                if not getattr(node, "auto_update", True):
                    continue

                # Check socket values
                for socket in node.inputs:
                    if not getattr(socket, "is_property", False):
                        continue
                    cache_key = (nt.name, node.name, socket.name)
                    new_val = socket.property_value
                    old_val = _socket_value_cache.get(cache_key)
                    if old_val is None:
                        _socket_value_cache[cache_key] = new_val
                        continue
                    if old_val != new_val:
                        _socket_value_cache[cache_key] = new_val
                        _on_socket_changed(node)

                # Check watched node properties (enums, bools)
                watched = _WATCHED_NODE_PROPS.get(node.bl_idname)
                if watched:
                    for prop_name in watched:
                        cache_key = (nt.name, node.name, prop_name)
                        new_val = getattr(node, prop_name, None)
                        old_val = _node_prop_cache.get(cache_key)
                        if old_val is None:
                            _node_prop_cache[cache_key] = new_val
                            continue
                        if old_val != new_val:
                            _node_prop_cache[cache_key] = new_val
                            _on_node_prop_changed(node)

    except Exception:
        logger.exception("Error in socket polling")

    return POLL_INTERVAL


# -- Registration -------------------------------------------------------------


def register():
    bpy.app.timers.register(_poll_socket_changes, first_interval=1.0, persistent=True)


def unregister():
    _socket_value_cache.clear()
    _node_prop_cache.clear()
    try:
        bpy.app.timers.unregister(_poll_socket_changes)
    except ValueError:
        msg = "Socket polling timer already expired"
        logger.warning(msg)

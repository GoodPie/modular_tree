"""Debounced tree rebuild to avoid redundant builds while adjusting values."""

import logging

import bpy

logger = logging.getLogger(__name__)

_pending_timers = {}  # {(tree_name, node_name): timer_func}

DEBOUNCE_DELAY = 0.3  # seconds of inactivity before rebuild


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

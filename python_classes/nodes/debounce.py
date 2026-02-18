"""Debounced tree rebuild to avoid redundant builds while adjusting values."""

import logging

import bpy

logger = logging.getLogger(__name__)

_pending_timer = None
_pending_mesher_id = None

DEBOUNCE_DELAY = 0.3  # seconds of inactivity before rebuild


def schedule_build(mesher, delay=DEBOUNCE_DELAY):
    """Schedule a debounced build_tree call. Resets on each invocation."""
    global _pending_timer, _pending_mesher_id

    _pending_mesher_id = (mesher.id_data.name, mesher.name)

    if _pending_timer is not None:
        try:
            bpy.app.timers.unregister(_pending_timer)
        except ValueError:
            # Timer already fired or was removed — safe to proceed
            logger.debug("Timer already expired for mesher %s", mesher.name)
        _pending_timer = None

    def _do_build():
        global _pending_timer, _pending_mesher_id
        _pending_timer = None
        if _pending_mesher_id is None:
            return None
        tree_name, node_name = _pending_mesher_id
        _pending_mesher_id = None
        node_tree = bpy.data.node_groups.get(tree_name)
        if node_tree:
            node = node_tree.nodes.get(node_name)
            if node:
                node.build_tree()
        return None

    _pending_timer = _do_build
    bpy.app.timers.register(_do_build, first_interval=delay)

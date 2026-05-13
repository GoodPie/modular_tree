import bpy
import nodeitems_utils
from bpy.utils import register_class, unregister_class

from . import (
    base_types,
    debounce,
    export_nodes,
    node_categories,
    properties,
    sockets,
    tree_function_nodes,
)


def register():
    base_types.register()
    sockets.register()
    tree_function_nodes.register()
    export_nodes.register()
    properties.register()
    node_categories.register()
    debounce.register()


def unregister():
    debounce.unregister()
    node_categories.unregister()
    base_types.unregister()
    sockets.unregister()
    properties.unregister()
    export_nodes.unregister()
    tree_function_nodes.unregister()

import bpy
import nodeitems_utils
from bpy.utils import register_class, unregister_class

from . import base_types, node_categories, properties, sockets, tree_function_nodes


def register():
    base_types.register()
    sockets.register()
    tree_function_nodes.register()
    properties.register()
    node_categories.register()


def unregister():
    node_categories.unregister()
    base_types.unregister()
    sockets.unregister()
    properties.unregister()
    tree_function_nodes.unregister()

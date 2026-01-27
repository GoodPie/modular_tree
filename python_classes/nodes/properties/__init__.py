import bpy
import nodeitems_utils
from bpy.utils import register_class, unregister_class

from .ramp_property import RampPropertyNode
from .random_property import RandomPropertyNode

classes = [RandomPropertyNode, RampPropertyNode]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)

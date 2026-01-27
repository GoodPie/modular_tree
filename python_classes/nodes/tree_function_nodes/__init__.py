import bpy
import nodeitems_utils
from bpy.utils import register_class, unregister_class

from .branch_node import BranchNode
from .growth_node import GrowthNode
from .pipe_radius_node import PipeRadiusNode
from .tree_mesher_node import TreeMesherNode
from .trunk_node import TrunkNode

classes = [BranchNode, GrowthNode, TreeMesherNode, TrunkNode, PipeRadiusNode]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)

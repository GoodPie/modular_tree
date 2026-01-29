from bpy.utils import register_class, unregister_class

from .pivot_painter_node import MTreePivotPainterExport

classes = [MTreePivotPainterExport]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)

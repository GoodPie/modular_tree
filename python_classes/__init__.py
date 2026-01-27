from . import nodes, operators, panels


def register():
    operators.register()
    nodes.register()
    panels.register()


def unregister():
    operators.unregister()
    nodes.unregister()
    panels.unregister()

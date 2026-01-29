import bpy


class MtreeSocket:
    is_property: bpy.props.BoolProperty(default=True)
    property_name: bpy.props.StringProperty()
    property_value: None
    color: (0.5, 0.5, 0.5, 1)
    description: bpy.props.StringProperty(name="Description", default="")

    def draw_color(self, context, node):
        return self.color

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import NodeSocket, NodeTree


class MtreeNode:
    @classmethod
    def poll(cls, nodeTree: NodeTree) -> bool:
        return nodeTree.bl_idname == "mt_MtreeNodeTree"

    # utility functions ----------------------------

    def get_node_tree(self) -> NodeTree:
        return self.id_data

    def get_child_nodes(self) -> list:
        child_nodes = []
        for socket in self.outputs:
            for link in socket.links:
                child_nodes.append(link.to_node)
        return child_nodes

    def get_neighbours(self) -> list:
        neighbours = []
        for socket in self.inputs:
            for link in socket.links:
                neighbours.append(link.from_node)
        for socket in self.outputs:
            for link in socket.links:
                neighbours.append(link.to_node)
        return neighbours

    def add_input(self, socket_type: str, name: str, **kwargs) -> NodeSocket:
        socket = self.inputs.new(socket_type, name)
        for key, value in kwargs.items():
            setattr(socket, key, value)
        return socket

    def add_output(self, socket_type: str, name: str, **kwargs) -> NodeSocket:
        socket = self.outputs.new(socket_type, name)
        for key, value in kwargs.items():
            setattr(socket, key, value)
        return socket

    def get_mesher_rec(self, seen_nodes: set) -> MtreeNode | None:
        if self.bl_idname == "mt_MesherNode":
            return self

        seen_nodes.add(self.name)

        for neighbour in self.get_neighbours():
            if neighbour.name in seen_nodes:
                continue
            mesher = neighbour.get_mesher_rec(seen_nodes)
            if mesher is not None:
                return mesher
        return None

    def get_mesher(self) -> MtreeNode | None:
        seen_nodes = set()
        return self.get_mesher_rec(seen_nodes)

    # Node events, don't override ----------------

    def draw_buttons(self, context, layout) -> None:
        self.draw(context, layout)

    def draw_buttons_ext(self, context, layout) -> None:
        self.draw_inspector(context, layout)

    # Functions that can be overriden -------------

    def draw(self, context, layout) -> None:
        pass

    def draw_inspector(self, context, layout) -> None:
        pass


class MtreeFunctionNode(MtreeNode):
    exposed_parameters = []  # List defined for each sub class
    advanced_parameters = []
    tree_function = None  # tree function type, as defined in m_tree. Should be overriden

    def draw(self, context, layout):
        for parameter in self.exposed_parameters:
            layout.prop(self, parameter)

    def draw_inspector(self, context, layout):
        for parameter in self.exposed_parameters + self.advanced_parameters:
            layout.prop(self, parameter)

    def construct_function(self):
        function_instance = self.tree_function()
        for parameter in self.exposed_parameters:
            setattr(function_instance, parameter, getattr(self, parameter))

        for input_socket in self.inputs:
            if input_socket.is_property:
                if input_socket.bl_idname == "mt_PropertySocket":
                    property = input_socket.get_property()
                    setattr(function_instance, input_socket.property_name, property)
                else:
                    setattr(
                        function_instance, input_socket.property_name, input_socket.property_value
                    )

        for child in self.get_child_nodes():
            if isinstance(child, MtreeFunctionNode):
                child_function = child.construct_function()
                function_instance.add_child(child_function)

        return function_instance


class MtreePropertyNode(MtreeNode):
    property_type = None  # tree Property type, as defined in m_tree. Should be overriden

    def get_property(self):
        property = self.property_type()
        for input_socket in self.inputs:
            if input_socket.is_property:
                setattr(property, input_socket.property_name, input_socket.property_value)
        return property

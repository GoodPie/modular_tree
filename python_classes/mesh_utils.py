"""Utilities for creating Blender meshes from C++ mesh data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import bpy


# Attribute definitions for tree meshes
FLOAT_ATTRIBUTES = [
    "radius",
    "stem_id",
    "hierarchy_depth",
    "branch_extent",
]

VECTOR3_ATTRIBUTES = [
    "direction",
    "pivot_position",
]


def create_mesh_from_cpp(
    mesh: bpy.types.Mesh,
    cpp_mesh,
) -> None:
    """Populate a Blender mesh from C++ mesh data.

    Args:
        mesh: The Blender mesh to populate.
        cpp_mesh: The C++ mesh object with vertex/polygon/attribute data.
    """
    _add_geometry(mesh, cpp_mesh)
    _add_attributes(mesh, cpp_mesh)
    _add_uvs(mesh, cpp_mesh)
    mesh.update(calc_edges=True)


def _add_geometry(mesh: bpy.types.Mesh, cpp_mesh) -> None:
    """Add vertices and polygons to the mesh."""
    verts = cpp_mesh.get_vertices()
    faces = np.copy(cpp_mesh.get_polygons()[::-1])  # Reverse to flip normals

    mesh.vertices.add(len(verts) // 3)
    mesh.vertices.foreach_set("co", verts)

    mesh.loops.add(len(faces))
    mesh.loops.foreach_set("vertex_index", faces)

    loop_start = np.arange(0, len(faces), 4, dtype=np.int32)
    loop_total = np.ones(len(faces) // 4, dtype=np.int32) * 4
    mesh.polygons.add(len(faces) // 4)
    mesh.polygons.foreach_set("loop_start", loop_start)
    mesh.polygons.foreach_set("loop_total", loop_total)
    mesh.polygons.foreach_set("use_smooth", np.ones(len(faces) // 4, dtype=bool))


def _add_attributes(mesh: bpy.types.Mesh, cpp_mesh) -> None:
    """Add custom attributes to the mesh."""
    for attr_name in FLOAT_ATTRIBUTES:
        data = cpp_mesh.get_float_attribute(attr_name)
        if attr_name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[attr_name])
        mesh.attributes.new(name=attr_name, type="FLOAT", domain="POINT")
        mesh.attributes[attr_name].data.foreach_set("value", data)

    for attr_name in VECTOR3_ATTRIBUTES:
        data = cpp_mesh.get_vector3_attribute(attr_name)
        if attr_name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[attr_name])
        mesh.attributes.new(name=attr_name, type="FLOAT_VECTOR", domain="POINT")
        mesh.attributes[attr_name].data.foreach_set("vector", data)


def _add_uvs(mesh: bpy.types.Mesh, cpp_mesh) -> None:
    """Add UV coordinates to the mesh."""
    uv_data = cpp_mesh.get_uvs()
    uv_data.shape = (len(uv_data) // 2, 2)
    uv_loops = np.copy(cpp_mesh.get_uv_loops()[::-1])  # Reverse since faces are reversed
    uvs = uv_data[uv_loops].flatten()

    uv_layer = mesh.uv_layers.new() if len(mesh.uv_layers) == 0 else mesh.uv_layers[0]
    uv_layer.data.foreach_set("uv", uvs)

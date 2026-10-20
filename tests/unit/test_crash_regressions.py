"""Regression tests for native crashes and hangs (#45, #41)."""

import numpy as np
import pytest

mt = pytest.importorskip(
    "m_tree.m_tree", reason="m_tree native module not installed (build with ./build_mtree.osx)"
)


def _constant(value):
    return mt.PropertyWrapper(mt.ConstantProperty(value))


def _curve(start, end):
    prop = mt.SimpleCurveProperty()
    prop.x_min, prop.x_max, prop.y_min, prop.y_max, prop.power = 0.0, 1.0, start, end, 1.0
    return mt.PropertyWrapper(prop)


def _issue_45_tree(seed):
    """The tree from issue #45 with a second branch level at density 0.8, resolution 0.8."""
    trunk = mt.TrunkFunction()
    trunk.seed = seed
    trunk.length = 21.27
    trunk.start_radius = 0.22
    trunk.end_radius = 0.033
    trunk.shape = 1.15
    trunk.up_attraction = 0.7
    trunk.resolution = 1.5
    trunk.randomness = 0.3

    limbs = mt.BranchFunction()
    limbs.seed = seed * 31 + 1
    limbs.distribution.start = 0.334
    limbs.distribution.end = 0.99
    limbs.distribution.density = 1.4
    limbs.length = _curve(11.09, 5.97)
    limbs.start_angle = _curve(66.0, 40.0)
    limbs.randomness = _constant(0.6)
    limbs.start_radius = _curve(0.8, 0.55)
    limbs.end_radius = 0.12
    limbs.flatness = 0.25
    limbs.gravity.strength = 3.0
    limbs.gravity.stiffness = 0.3
    limbs.gravity.up_attraction = 0.25
    limbs.split.probability = 0.16
    limbs.split.radius = 0.82
    limbs.split.angle = 30.0
    limbs.break_chance = 0.0
    limbs.resolution = 1.5
    limbs.crown.shape = mt.CrownShape.Hemispherical

    secondary = mt.BranchFunction()
    secondary.seed = seed * 31 + 2
    secondary.distribution.start = 0.2
    secondary.distribution.end = 0.97
    secondary.distribution.density = 0.8
    secondary.length = _curve(3.98, 1.71)
    secondary.start_angle = _constant(58.0)
    secondary.randomness = _constant(0.55)
    secondary.start_radius = _constant(0.55)
    secondary.end_radius = 0.08
    secondary.flatness = 0.7
    secondary.gravity.strength = 6.0
    secondary.gravity.stiffness = 0.15
    secondary.gravity.up_attraction = 0.05
    secondary.split.probability = 0.12
    secondary.split.radius = 0.8
    secondary.split.angle = 30.0
    secondary.break_chance = 0.01
    secondary.resolution = 0.8

    limbs.add_child(secondary)
    trunk.add_child(limbs)
    tree = mt.Tree()
    tree.set_trunk_function(trunk)
    tree.execute_functions()
    return tree


@pytest.mark.parametrize("seed", range(1, 13))
def test_branch_resolution_below_one_meshes_without_nan(seed):
    """Short branches got a negative segment, NaN directions, then a mesher crash (#45)."""
    mesher = mt.ManifoldMesher()
    mesher.radial_n_points = 8
    mesher.smooth_iterations = 0
    vertices = np.asarray(mesher.mesh_tree(_issue_45_tree(seed)).get_vertices())

    assert len(vertices) > 0
    assert np.isfinite(vertices).all()


@pytest.mark.parametrize(
    ("function_name", "attribute", "value"),
    [
        ("TrunkFunction", "length", -1.0),
        ("TrunkFunction", "resolution", -1.0),
        ("GrowthFunction", "iterations", -1),
        ("GrowthFunction", "apical_dominance", -0.5),
        ("GrowthFunction", "lateral_density", -1.0),
        ("PipeRadiusFunction", "end_radius", -0.1),
        ("PipeRadiusFunction", "constant_growth", -1.0),
    ],
)
def test_negative_input_raises_value_error(function_name, attribute, value):
    """Negative values froze or crashed Blender (#41); they now raise instead."""
    trunk = mt.TrunkFunction()
    function = trunk if function_name == "TrunkFunction" else getattr(mt, function_name)()
    setattr(function, attribute, value)
    if function is not trunk:
        trunk.add_child(function)
    tree = mt.Tree()
    tree.set_trunk_function(trunk)

    with pytest.raises(ValueError):
        tree.execute_functions()

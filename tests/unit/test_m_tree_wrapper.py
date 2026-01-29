"""Tests for m_tree lazy loading wrapper."""

import pytest

# Import directly from module (path setup in conftest.py)
from m_tree_wrapper import _LazyModule, get_m_tree

# Check if m_tree native module is available
try:
    from m_tree import m_tree  # noqa: F401

    HAS_NATIVE_MODULE = True
except ImportError:
    HAS_NATIVE_MODULE = False

requires_native = pytest.mark.skipif(
    not HAS_NATIVE_MODULE,
    reason="m_tree native module not installed (build with ./build_mtree.osx)",
)


class TestLazyModule:
    """Tests for _LazyModule class."""

    def test_can_instantiate(self):
        """_LazyModule can be instantiated."""
        module = _LazyModule()
        assert module is not None

    def test_is_proxy_object(self):
        """_LazyModule is a proxy that delegates attribute access."""
        module = _LazyModule()
        # Check it has the __getattr__ method for proxying
        assert hasattr(module, "__getattr__")


class TestGetMTree:
    """Tests for get_m_tree function."""

    @requires_native
    def test_returns_module(self):
        """get_m_tree returns a module object."""
        m_tree = get_m_tree()
        assert m_tree is not None

    @requires_native
    def test_caches_module(self):
        """get_m_tree returns the same instance on subsequent calls."""
        first = get_m_tree()
        second = get_m_tree()
        assert first is second

    @requires_native
    def test_module_has_expected_classes(self):
        """Loaded m_tree module exposes expected C++ classes."""
        m_tree = get_m_tree()

        # Core tree classes
        assert hasattr(m_tree, "Tree")
        assert hasattr(m_tree, "TrunkFunction")
        assert hasattr(m_tree, "BranchFunction")

        # Property classes used by presets
        assert hasattr(m_tree, "ConstantProperty")
        assert hasattr(m_tree, "PropertyWrapper")


class TestLazyMTreeProxy:
    """Tests for lazy_m_tree module-level proxy."""

    @requires_native
    def test_attribute_access_works(self):
        """Attribute access on lazy_m_tree proxy returns expected types."""
        from m_tree_wrapper import lazy_m_tree

        # Access should work without explicit get_m_tree() call
        tree_class = lazy_m_tree.Tree
        assert tree_class is not None

    @requires_native
    def test_proxy_returns_same_as_direct_access(self):
        """Proxy returns same objects as direct module access."""
        from m_tree_wrapper import lazy_m_tree

        m_tree = get_m_tree()

        assert lazy_m_tree.Tree is m_tree.Tree
        assert lazy_m_tree.BranchFunction is m_tree.BranchFunction

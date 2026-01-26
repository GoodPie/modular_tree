"""Lazy loader for m_tree native library to avoid circular imports.

When Blender loads the addon as bl_ext.user_default.modular_tree, module-level
imports of m_tree fail because the parent package isn't fully initialized yet.
This wrapper defers the import until first access.
"""

_m_tree = None


def get_m_tree():
    """Lazily import and cache the m_tree native library."""
    global _m_tree
    if _m_tree is None:
        import importlib
        parent_package = __package__.rsplit('.', 1)[0]
        _m_tree = importlib.import_module('.m_tree', parent_package)
    return _m_tree


class _LazyModule:
    """Proxy that forwards attribute access to the lazily-loaded m_tree module."""

    def __getattr__(self, name):
        return getattr(get_m_tree(), name)


lazy_m_tree = _LazyModule()

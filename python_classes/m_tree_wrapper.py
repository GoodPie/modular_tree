"""Lazy loader for m_tree native library to avoid circular imports.

When Blender loads the addon, module-level imports of m_tree can fail due to
import timing issues during addon initialization. This wrapper defers the
import until first access. The m_tree module is installed as a top-level
package by Blender's extension system (from wheels), not nested under the addon.
"""

_m_tree = None


def get_m_tree():
    """Lazily import and cache the m_tree native library."""
    global _m_tree
    if _m_tree is None:
        from m_tree import m_tree

        _m_tree = m_tree
    return _m_tree


class _LazyModule:
    """Proxy that forwards attribute access to the lazily-loaded m_tree module."""

    def __getattr__(self, name):
        return getattr(get_m_tree(), name)


lazy_m_tree = _LazyModule()

"""Root pytest configuration for MTree addon tests.

This module sets up the Python path for testing modules that don't require Blender.
We avoid importing through python_classes/__init__.py which imports bpy.
"""

import sys
from pathlib import Path

# Add specific subdirectories that can be tested without Blender
PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_CLASSES = PROJECT_ROOT / "python_classes"

# Add paths for modules that don't import bpy at top level
paths_to_add = [
    str(PYTHON_CLASSES),
    str(PYTHON_CLASSES / "presets"),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

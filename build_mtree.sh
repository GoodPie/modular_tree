#!/bin/bash
set -e

# Build C++ library
python3.11 m_tree/install.py

# Copy .so for direct import (development convenience)
cp ./m_tree/binaries/m_tree.cpython-311-x86_64-linux-gnu.so ./m_tree.cpython-311-x86_64-linux-gnu.so

# Rebuild wheel with new C++ code
rm -f wheels/*.whl 2>/dev/null || true
pip3.11 wheel ./m_tree -w ./wheels/ --no-deps

# Package addon for Blender
rm -rf tmp/
python3.11 .github/scripts/setup_addon.py

echo "Addon ready: tmp/modular_tree_*.zip"

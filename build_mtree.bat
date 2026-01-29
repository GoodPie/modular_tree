@echo off
setlocal enabledelayedexpansion

REM Build C++ library
py -3.11 m_tree/install.py
if %errorlevel% neq 0 exit /b %errorlevel%

REM Copy .pyd for direct import (development convenience)
COPY ".\m_tree\binaries\Release\m_tree.cp311-win_amd64.pyd" ".\m_tree.cp311-win_amd64.pyd"

REM Rebuild wheel with new C++ code
del /q wheels\*.whl 2>nul
py -3.11 -m pip wheel .\m_tree -w .\wheels\ --no-deps
if %errorlevel% neq 0 exit /b %errorlevel%

REM Package addon for Blender
rmdir /s /q tmp 2>nul
py -3.11 .github/scripts/setup_addon.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo Addon ready: tmp\modular_tree_*.zip

PAUSE

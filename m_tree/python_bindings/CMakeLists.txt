cmake_minimum_required(VERSION 3.5...3.27)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python 3.11 COMPONENTS Interpreter Development.Module REQUIRED)

# Tell pybind11 to use modern FindPython instead of deprecated FindPythonInterp
# Required for CMake 3.27+ where FindPythonInterp was removed (CMP0148)
set(PYBIND11_FINDPYTHON ON)

add_subdirectory(../dependencies/pybind11 pybind11)

file(GLOB_RECURSE sources
    "./*.hpp"
    "./*.cpp"
)

pybind11_add_module(m_tree ${sources})
target_link_libraries(m_tree PRIVATE m_tree-lib)

# Install target for scikit-build-core wheel builds
if(DEFINED SKBUILD_PROJECT_NAME)
    install(TARGETS m_tree LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})
endif()
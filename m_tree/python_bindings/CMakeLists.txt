cmake_minimum_required(VERSION 3.5...3.27)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python 3.11 COMPONENTS Interpreter Development REQUIRED)
add_subdirectory(../dependencies/pybind11 pybind11)

file(GLOB_RECURSE sources
    "./*.hpp"
    "./*.cpp"
)

pybind11_add_module(m_tree ${sources})
target_link_libraries(m_tree PRIVATE m_tree-lib)
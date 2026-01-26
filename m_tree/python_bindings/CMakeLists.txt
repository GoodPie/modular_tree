cmake_minimum_required(VERSION 3.5...3.27)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(../dependencies/pybind11 [EXCLUDE_FROM_ALL])

file(GLOB_RECURSE sources
    "./*.hpp"
    "./*.cpp"
)

pybind11_add_module(m_tree ${sources})
target_link_libraries(m_tree PRIVATE m_tree-lib)
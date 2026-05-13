cmake_minimum_required(VERSION 3.15...3.31)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)


file(GLOB_RECURSE sources
    "./*.hpp"
    "./*.cpp"
)

add_executable(m_tree_tests ${sources})

add_test(NAME m_tree_tests COMMAND m_tree_tests)

target_link_libraries(m_tree_tests PRIVATE m_tree-lib)

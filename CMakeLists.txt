cmake_minimum_required(VERSION 3.18.2)
project(favicorn_core VERSION 1.0)
include(CMakePrintHelpers)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(GNUInstallDirs)

# Use -fPIC even if statically compiled
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED PATHS ${Python3_SITEARCH} NO_DEFAULT_PATH)
file(GLOB_RECURSE FAVICORN_CORE_HEADERS favicorn_core *.hpp *.h)
file(GLOB_RECURSE FAVICORN_CORE_SOURCES favicorn_core *.cpp *.c)
add_library(
    favicorn_core
    ${FAVICORN_CORE_HEADERS}
    ${FAVICORN_CORE_SOURCES}
)
add_library(favicorn_core::favicorn_core ALIAS favicorn_core)

set_target_properties(
    favicorn_core
    PROPERTIES
    PUBLIC_HEADER "${FAVICORN_CORE_HEADERS}"
)
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/favicorn_core/
    ${CMAKE_CURRENT_SOURCE_DIR}/favicorn_core/include/
)
cmake_print_variables(pybind11_INCLUDE_DIRS)
target_include_directories(favicorn_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/favicorn_core/>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
    PRIVATE ${Python3_INCLUDE_DIRS}
    PRIVATE ${pybind11_INCLUDE_DIRS}
)
install(
    TARGETS favicorn_core 
    EXPORT favicorn_coreTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

install(
    EXPORT favicorn_coreTargets
    FILE favicorn_coreTargets.cmake
    NAMESPACE favicorn_core::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/favicorn_core)

include(CMakePackageConfigHelpers)

set(PACKAGE_INIT_MACRO "@PACKAGE_INIT@")
set(CONFIG_CMAKE_IN "\
@PACKAGE_INIT_MACRO@\n\
include(\"\${CMAKE_CURRENT_LIST_DIR}/favicorn_coreTargets.cmake\")\n\
check_required_components(favicorn_core)\n"
)

# Create Config.cmake.in
file(CONFIGURE
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/Config.cmake.in
    CONTENT ${CONFIG_CMAKE_IN}
    @ONLY)

# Create MyMathConfig.cmake
configure_package_config_file(
    ${CMAKE_CURRENT_BINARY_DIR}/Config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/favicorn_coreConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/favicorn_core)

# Create MyMathConfigVersion.cmake
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/favicorn_coreConfigVersion.cmake"
    VERSION "${version}"
    COMPATIBILITY AnyNewerVersion
)

# Install CMake package files
install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/favicorn_coreConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/favicorn_coreConfigVersion.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/favicorn_core
)

# ===============
# Python bindings
# ===============

# Find Python3 and NumPy
set(CMAKE_FIND_DEBUG_MODE 1)
set(VERBOSE 1)
cmake_print_variables(pybind11_DIR)

pybind11_add_module(pybind11_bindings MODULE favicorn_core/core.cpp)
target_link_libraries(pybind11_bindings
    PRIVATE favicorn_core::favicorn_core)

set_target_properties(pybind11_bindings PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/favicorn_core
    OUTPUT_NAME "favicorn_core")

if(CALL_FROM_SETUP_PY)
    # The CMakeExtension will set CMAKE_INSTALL_PREFIX to the root
    # of the resulting wheel archive
    set(FAVICORN_CORE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
else()
    # The Python package is installed directly in the folder of the
    # detected interpreter (system, user, or virtualenv)
    set(FAVICORN_CORE_INSTALL_PREFIX ${Python3_SITELIB})
endif()

install(
    TARGETS pybind11_bindings
    COMPONENT favicorn_core
    LIBRARY DESTINATION ${FAVICORN_CORE_INSTALL_PREFIX}
    ARCHIVE DESTINATION ${FAVICORN_CORE_INSTALL_PREFIX}
    RUNTIME DESTINATION ${FAVICORN_CORE_INSTALL_PREFIX}
)

cmake_minimum_required(VERSION 3.18.2)
project(favicorn_core VERSION 1.0)
include(CMakePrintHelpers)
include(GNUInstallDirs)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR})
add_compile_options(-fsanitize=address)

# Use -fPIC even if statically compiled
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED PATHS ${Python3_SITEARCH} NO_DEFAULT_PATH)
find_package(Threads REQUIRED)
find_package(LIBUV REQUIRED)
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
target_include_directories(favicorn_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/favicorn_core/>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
    PRIVATE ${Python3_INCLUDE_DIRS}
    PRIVATE ${pybind11_INCLUDE_DIRS}
    PRIVATE ${LIBUV_INCLUDE_DIRS}
)
install(
    TARGETS favicorn_core 
    EXPORT favicorn_coreTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

target_link_libraries(
    favicorn_core
    PRIVATE Threads::Threads
    PRIVATE ${LIBUV_LIBRARIES}
)
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

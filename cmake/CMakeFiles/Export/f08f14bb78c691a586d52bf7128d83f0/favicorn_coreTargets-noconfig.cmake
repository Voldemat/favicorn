#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "favicorn_core::favicorn_core" for configuration ""
set_property(TARGET favicorn_core::favicorn_core APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(favicorn_core::favicorn_core PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_NOCONFIG "C;CXX"
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libfavicorn_core.a"
  )

list(APPEND _cmake_import_check_targets favicorn_core::favicorn_core )
list(APPEND _cmake_import_check_files_for_favicorn_core::favicorn_core "${_IMPORT_PREFIX}/lib/libfavicorn_core.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

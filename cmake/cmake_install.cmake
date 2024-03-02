# Install script for directory: /Users/vladimir/code/opensource/favicorn

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/Users/vladimir/code/opensource/favicorn/cmake/libfavicorn_core.a")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libfavicorn_core.a" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libfavicorn_core.a")
    execute_process(COMMAND "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/ranlib" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libfavicorn_core.a")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include" TYPE FILE FILES
    "/Users/vladimir/code/opensource/favicorn/build/lib.macosx-13.1-arm64-cpython-310/include/http_parser.hpp"
    "/Users/vladimir/code/opensource/favicorn/build/lib.macosx-13.1-arm64-cpython-310/include/llhttp.h"
    "/Users/vladimir/code/opensource/favicorn/build/lib.macosx-13.1-arm64-cpython-310/include/loop.hpp"
    "/Users/vladimir/code/opensource/favicorn/build/lib.macosx-13.1-arm64-cpython-310/include/scope.hpp"
    "/Users/vladimir/code/opensource/favicorn/build/lib.macosx-13.1-arm64-cpython-310/include/server.hpp"
    "/Users/vladimir/code/opensource/favicorn/favicorn_core/include/llhttp.h"
    "/Users/vladimir/code/opensource/favicorn/favicorn_core/src/http_parser/http_parser.hpp"
    "/Users/vladimir/code/opensource/favicorn/favicorn_core/src/loop/loop.hpp"
    "/Users/vladimir/code/opensource/favicorn/favicorn_core/src/scope.hpp"
    "/Users/vladimir/code/opensource/favicorn/favicorn_core/src/server/server.hpp"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core/favicorn_coreTargets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core/favicorn_coreTargets.cmake"
         "/Users/vladimir/code/opensource/favicorn/cmake/CMakeFiles/Export/f08f14bb78c691a586d52bf7128d83f0/favicorn_coreTargets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core/favicorn_coreTargets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core/favicorn_coreTargets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core" TYPE FILE FILES "/Users/vladimir/code/opensource/favicorn/cmake/CMakeFiles/Export/f08f14bb78c691a586d52bf7128d83f0/favicorn_coreTargets.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^()$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core" TYPE FILE FILES "/Users/vladimir/code/opensource/favicorn/cmake/CMakeFiles/Export/f08f14bb78c691a586d52bf7128d83f0/favicorn_coreTargets-noconfig.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/favicorn_core" TYPE FILE FILES
    "/Users/vladimir/code/opensource/favicorn/cmake/favicorn_coreConfig.cmake"
    "/Users/vladimir/code/opensource/favicorn/cmake/favicorn_coreConfigVersion.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "favicorn_core" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/Users/vladimir/.local/share/virtualenvs/favicorn-TLgRKIlL/lib/python3.10/site-packages/favicorn_core.cpython-310-darwin.so")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/Users/vladimir/.local/share/virtualenvs/favicorn-TLgRKIlL/lib/python3.10/site-packages" TYPE MODULE FILES "/Users/vladimir/code/opensource/favicorn/cmake/favicorn_core/favicorn_core.cpython-310-darwin.so")
  if(EXISTS "$ENV{DESTDIR}/Users/vladimir/.local/share/virtualenvs/favicorn-TLgRKIlL/lib/python3.10/site-packages/favicorn_core.cpython-310-darwin.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/Users/vladimir/.local/share/virtualenvs/favicorn-TLgRKIlL/lib/python3.10/site-packages/favicorn_core.cpython-310-darwin.so")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/strip" -x "$ENV{DESTDIR}/Users/vladimir/.local/share/virtualenvs/favicorn-TLgRKIlL/lib/python3.10/site-packages/favicorn_core.cpython-310-darwin.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/Users/vladimir/code/opensource/favicorn/cmake/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")

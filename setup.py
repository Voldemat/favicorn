import os
import sys
from pathlib import Path

from setuptools import find_packages, setup  # type: ignore [import]

import cmake_build_extension

favicorn_core = cmake_build_extension.CMakeExtension(
    name="favicorn_core",
    # Name of the resulting package name (import mymath_pybind11)
    install_prefix="",
    # Note: pybind11 is a build-system requirement specified in pyproject.toml,
    #       therefore pypa/pip or pypa/build will install it in the virtual
    #       environment created in /tmp during packaging.
    #       This cmake_depends_on option adds the pybind11 installation path
    #       to CMAKE_PREFIX_PATH so that the example finds the pybind11 targets
    #       even if it is not installed in the system.
    cmake_depends_on=["pybind11"],
    #write_top_level_init=init_py,
    source_dir=str(Path(__file__).parent.absolute()),
    cmake_configure_options=[
        # This option points CMake to the right Python interpreter, and helps
        # the logic of FindPython3.cmake to find the active version
        f"-DPython3_ROOT_DIR={Path(sys.prefix)}",
        "-DCALL_FROM_SETUP_PY:BOOL=ON",
        "-DBUILD_SHARED_LIBS:BOOL=OFF",
        # Select the bindings implementation
        "-DEXAMPLE_WITH_SWIG:BOOL=OFF",
        "-DEXAMPLE_WITH_PYBIND11:BOOL=ON",
    ]
)

setup(
    name="favicorn",
    version=os.environ["GITHUB_REF_NAME"],
    description="ASGI webserver",
    author="Vladimir Vojtenko",
    author_email="vladimirdev635@gmail.com",
    license="MIT",
    packages=find_packages(exclude=["__tests__*"]),
    include_package_data=True,
    ext_modules=[favicorn_core],
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    install_requires=['pybind11', 'cmake_build_extension'],
    cmdclass={
        'build_ext': cmake_build_extension.BuildExtension
    }
)

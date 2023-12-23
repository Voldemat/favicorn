import os
import sys
from pathlib import Path

import cmake_build_extension

from setuptools import find_packages, setup  # type: ignore [import]


favicorn_core = cmake_build_extension.CMakeExtension(
    name="favicorn_core",
    cmake_depends_on=["pybind11"],
    source_dir=str(Path(__file__).parent.absolute()),
    cmake_configure_options=[
        f"-DPython3_ROOT_DIR={Path(sys.prefix)}",
        "-DCALL_FROM_SETUP_PY:BOOL=ON",
        "-DBUILD_SHARED_LIBS:BOOL=OFF",
        "-DEXAMPLE_WITH_SWIG:BOOL=OFF",
        "-DEXAMPLE_WITH_PYBIND11:BOOL=ON",
    ],
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
    cmdclass={"build_ext": cmake_build_extension.BuildExtension},
)

import os
import glob
from pathlib import Path

from setuptools import find_packages, setup, Extension  # type: ignore [import]

sources = [
    *glob.glob("**/*.c", recursive=True),
    *glob.glob("**/*.cpp", recursive=True),
]
header_files = [
    *glob.glob("**/*.h", recursive=True),
    *glob.glob("**/*.hpp", recursive=True),
]
proxylib_module = Extension(
    "favicorn_core",
    sources=sources,
    language="c++",
    include_dirs=[
        'favicorn_core',
        'favicorn_core/include'
    ],
    depends=[*sources, *header_files],
    extra_compile_args=['-Wno-unreachable-code']
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
    ext_modules=[proxylib_module],
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
)

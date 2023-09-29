import os
from distutils.core import Extension
from pathlib import Path

from setuptools import find_packages, setup  # type: ignore [import]

proxylib_module = Extension(
    "favicorn_core",
    sources=[
        "favicorn/extension/core.cpp",
    ],
    language="c++",
    include_dirs=[
        "/Users/vladimir/code/opensource/favicorn/favicorn/extension/"
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
    ext_modules=[proxylib_module],
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
)

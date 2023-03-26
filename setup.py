import os
from pathlib import Path

from setuptools import setup  # type: ignore [import]


setup(
    name="favicorn",
    version=os.environ["GITHUB_REF_NAME"],
    description="ASGI webserver",
    author="Vladimir Vojtenko",
    author_email="vladimirdev635@gmail.com",
    license="MIT",
    packages=[
        "favicorn",
    ],
    package_data={
        "favicorn": ["py.typed"],
    },
    install_requires=["httptools", "asgiref"],
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
)

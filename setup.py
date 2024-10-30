import didact
from setuptools import setup, find_packages

version = didact.__version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="didact",
    packages=find_packages(exclude=[]),
    version=version,
    description=(
        "Didact. "
        "Hosted PaperQA connected to a cloud DB."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Didact Authors",
    author_email="limsweekiat@gmail.com",
    url="https://github.com/greentfrapp/didact",
    license="",
    keywords=[
    ],
    install_requires=[
    ],
    classifiers=[
    ],
)
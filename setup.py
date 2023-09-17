import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="fastutils_hmarcuzzo",
    version="0.1.3",  # The initial release version
    author="Henrique Marcuzzo",  # Full name of the author
    description="A personal utility library I've developed to streamline and optimize backend development with FastAPI in my projects. "
    "From generic repositories and queries to enums, error handling, and more, fastutils_hmarcuzzo encompasses essential tools "
    "that have proven invaluable in my development journey, whether as a novice or a seasoned professional.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(where="src"),  # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],  # Information to filter the project on PyPi website
    python_requires=">=3.10",  # Minimum version requirement of the package
    package_dir={"": "src"},  # Directory of the source code of the package
    install_requires=requirements,  # Install other dependencies if any
)


"""

Author: F. Thomas
Date: February 17, 2021

"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hercules",
    version="0.0.1",
    author="Florian Thomas",
    author_email="fthomas@uni-mainz.de",
    description="https://github.com/project8/hercules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/project8/hercules",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)

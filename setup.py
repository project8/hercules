"""

Author: F. Thomas
Date: February 17, 2021

"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

required = [
    "h5py",
    "numpy",
    "scipy",
    "tqdm"
]

setuptools.setup(
    name="hercules",
    version="0.4.1",
    author="Florian Thomas, Mingyu (Charles) Li",
    author_email="fthomas@uni-mainz.de, mingyuli@mit.edu",
    description="https://github.com/project8/hercules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/project8/hercules",
    packages=setuptools.find_packages(),
    package_data={'hercules': ['hexbug/**/**/*', 'hexbug/**/*', 'settings/*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=required)

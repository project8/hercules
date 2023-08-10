"""

Author: F. Thomas
Date: February 17, 2021

"""

import setuptools
import versioneer

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    required = [line.strip() for line in fh]

setuptools.setup(
    name="hercules",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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

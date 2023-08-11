"""

Author: F. Thomas
Date: February 17, 2021

"""

from distutils.cmd import Command
from setuptools import setup
import setuptools
from setuptools.command.build_py import build_py
import versioneer
import subprocess
import glob

from hercules import _versionhelper

class cmd_build_py(build_py):

    def run(self) -> None:
        _versionhelper.persist_hexbug_commit_version()

        #pickle CRESana models
        try:
            import cresana
            path = 'hercules/hexbug/Phase4/CRESana_models'
            for file in glob.glob(path+'/*.py'):
                subprocess.run(['python', file])

        except:
            print('Not installing CRESana models')

        build_py.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    required = [line.strip() for line in fh]

cmd_class = {'build_py': cmd_build_py}

setup(
    name="hercules",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(cmd_class),
    author="Florian Thomas, Mingyu (Charles) Li",
    author_email="fthomas@uni-mainz.de, mingyuli@mit.edu",
    description="https://github.com/project8/hercules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/project8/hercules",
    packages=setuptools.find_packages(),
    package_data={'hercules': ['hexbug/**/**/*', 'hexbug/**/*', 'hexbug/*', 'settings/*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=required)

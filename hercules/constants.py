
"""

Author: F. Thomas
Date: March 10, 2021

"""

__all__ = []

from pathlib import Path, PosixPath

from .configuration import Configuration

MODULE_DIR = Path(__file__).parent.absolute()
HEXBUG_DIR = MODULE_DIR / 'hexbug'
#container is running linux
#-> make sure it's PosixPath when run from windows
HEXBUG_DIR_CONTAINER = PosixPath('/') / 'tmp'
OUTPUT_DIR_CONTAINER = PosixPath('/') / 'home' 
LOCUST_CONFIG_NAME = 'LocustPhase3Template.json'
KASS_CONFIG_NAME = 'LocustKassElectrons.xml'
SIM_CONFIG_NAME = 'SimConfig.json'

CONFIG = Configuration()

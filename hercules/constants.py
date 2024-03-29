
"""

Author: F. Thomas
Date: March 10, 2021

"""

__all__ = []

from pathlib import Path, PurePosixPath

from .configuration import Configuration

MODULE_DIR = Path(__file__).parent.absolute()
HEXBUG_DIR = MODULE_DIR / 'hexbug'
#container is running linux
#-> make sure it's PosixPath when run from windows
HEXBUG_DIR_CONTAINER = PurePosixPath('/') / 'tmp'
OUTPUT_DIR_CONTAINER = PurePosixPath('/') / 'home' 
LOCUST_CONFIG_NAME_P2 = 'LocustPhase2Template.json'
KASS_CONFIG_NAME_P2 = 'Project8Phase2_electrons.xml'
LOCUST_CONFIG_NAME_P3 = 'LocustPhase3Template.json'
KASS_CONFIG_NAME_P3 = 'LocustKassElectrons.xml'
PY_DATA_NAME = 'data.npy'

LOCUST_CONFIG_NAME = 'Locust.json'
KASS_CONFIG_NAME = 'LocustKassElectrons.xml'
SIM_CONFIG_NAME = 'SimConfig.json'

CONFIG = Configuration()


"""

Author: F. Thomas
Date: August 11, 2023

"""

import sys
from pathlib import Path
import os

from .simconfig import SimpleSimConfig


class PyJob:

    def __init__(self):
        args = sys.argv
        print(args)
        path = Path(args[1]).absolute()
        os.chdir(path)
        self._config_dict = SimpleSimConfig.from_json('SimConfig.json').to_dict()

    @property
    def config_data(self):
        return self._config_dict['config-data']
    
    @property
    def meta_data(self):
        return self._config_dict['meta-data']
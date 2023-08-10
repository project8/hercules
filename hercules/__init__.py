
"""

Author: F. Thomas
Date: February 17, 2021

"""


from .simulation import KassLocustP3
from .simconfig import SimConfig, SimpleSimConfig, ConfigList
from .eggreader import LocustP3File
from .dataset import Dataset

from . import _version
from . import _versionhelper

__version__ = _version.get_versions()['version']
__hexbug_version__ = _versionhelper.get_hexbug_commit_version()
__python_script_version__ = _versionhelper.get_python_dir_commit_version()

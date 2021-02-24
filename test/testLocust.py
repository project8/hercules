
"""

Author: F. Thomas
Date: February 22, 2021

"""

from hercules.simulation import SimConfig, KassLocustP3
from pathlib import Path

moduleDir = Path(__file__).parent.absolute()

#just an example
config = SimConfig(nChannels=2, seedLocust=1, vRange=7.0,
                    eggFilename='someFileName.egg', seedKass =12534, xMin=-0.1e-5, 
                    xMax=0.1e-5, tMax=0.5e-6,
                    geometry='FreeSpaceGeometry_V00_00_10.xml')


sim = KassLocustP3(str(moduleDir) + '/workingDir')
sim(config, 'someDirName')

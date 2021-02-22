
"""

Author: F. Thomas
Date: February 22, 2021

"""

from hercules.simulation import SimConfig

config = SimConfig(nChannels=15, seedLocust=1, vRange=7.0, nSubarrays=3,
                    eggFilename='x.egg', seedKass =12534, xMin=0.05e-6, 
                    xMax=0.1e-5, outPath='/', 
                    geometry='FreeSpaceGeometry_V00_00_10.xml')

config.toJson('SimConfig.json')

config2 = SimConfig.fromJson('SimConfig.json')
config2.makeConfigFile('Locust.json', 'Kass.xml')
print(config2.toDict())

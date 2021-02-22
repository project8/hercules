
"""

Author: F. Thomas
Date: February 22, 2021

"""

from hercules.simulation import LocustConfig, KassConfig

lConfig = LocustConfig(nChannels=15, randomSeed=1, vRange=7.0, nSubarrays=3, eggFilename='x.egg')
lConfig.makeConfigFile('Locust.json')

kConfig = KassConfig(seedKass =12534, xMin=0.05e-6, xMax=0.1e-5, outPath='/', geometry='FreeSpaceGeometry_V00_00_10.xml')
kConfig.makeConfigFile('Kass.xml')

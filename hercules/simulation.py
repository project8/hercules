
"""

Author: F. Thomas
Date: February 19, 2021

"""

import time

def _getRandSeed():
    
    t = int( time.time() * 1000.0 )
    seed = ((t & 0xff000000) >> 24) +\
             ((t & 0x00ff0000) >>  8) +\
             ((t & 0x0000ff00) <<  8) +\
             ((t & 0x000000ff) << 24)
             
    return seed
    
    
class KassConfig:
    
    __configDict = {'seedKass': '$SEED',
                   'tMax': '$TMAX',
                   'xMin': '$XMIN',
                   'yMin': '$YMIN',
                   'xMax': '$XMAX',
                   'yMax': '$YMAX',
                   'zMin': '$ZMIN',
                   'zMax': '$ZMAX',
                   'pitchMin': '$PITCHMIN',
                   'pitchMax': '$PITCHMAX',
                   'geometry': '$GEOMETRY',
                   'outPath': '$OUTPATH' }
    
    def __init__(self,
                    seedKass=None,
                    tMax = None,
                    xMin = None,
                    xMax = None,
                    yMin = None,
                    yMax = None,
                    zMin = None,
                    zMax = None,
                    pitchMin = None,
                    pitchMax = None,
                    geometry = 'FreeSpaceGeometry_V00_00_04.xml',
                    locustVersion ='v2.1.6'):
        
        self.__seedKass = seedKass
        self.__tMax = tMax
        self.__xMin = xMin
        self.__xMax = xMax
        self.__yMin = yMin
        self.__yMax = yMax
        self.__zMin = zMin
        self.__zMax = zMax
        self.__pitchMin = pitchMin
        self.__pitchMax = pitchMax
        self.__geometry = '/hexbug/Phase3/Trap/'+geometry
        self.__outPath =  '/usr/local/p8/locust/'+ locustVersion +'/output'
        
        
        self.__setRandomSeed()
        
    def __setRandomSeed(self):
        
        if not self.__seedKass:
            self.seedKass = _getRandSeed()
            
    def makeConfigFile(self, inPath, outPath):
        
        with open(inPath) as conf:
            xml = conf.read()
        
        vals = self.__dict__
        for key in vals:
            xml=xml.replace(kassConfigDict[key], '"'+str(vals[key])+'"')
            
        with open(outPath, 'w') as newConf:
            newConf.write(xml)
        
    
def _getConfigFromFile(locustFile):
    with open(locustFile, 'r') as infile:
        return json.load(infile)

class LocustConfig:
    
    #private class variables to store the json keys
    #if a key changes we can change it here
    __sSim = 'simulation'
    __sArray = 'array-signal'
    __sDigit = 'digitizer'
    __sNoise = 'gaussian-noise'
    __sGen = 'generators'
    __sFft = 'lpf-fft'
    __sDec = 'decimate-signal'
    
    __sNChannels = 'n-channels'
    __sEggFilename = 'egg-filename'
    __sRecordSize = 'record-size'
    __sNRecords = 'n-records'
    __sVRange = 'v-range'
    __sVOffset = 'v-offset'
    __sLoFrequency = 'lo-frequency'
    __sNelementsPerStrip = 'nelements-per-strip'
    __sNSubarrays = 'n-subarrays'
    __sZshiftArray = 'zshift-array'
    __sArrayRadius = 'array-radius'
    __sElementSpacing = 'element-spacing'
    __sTfReceiverBinWidth = 'tf-receiver-bin-width'
    __sTfReceiverFilename = 'tf-receiver-filename'
    __sXmlFilename = 'xml-filename'
    __sRandomSeed = 'random-seed'
    __sNoiseFloorPsd = 'noise-floor-psd'
    __sNoiseTemperature = 'noise-temperature'
    
    def __init__(self,
                templateConfig,
                nChannels=None,
                eggFilename=None,
                recordSize=None,
                nRecords=None,
                vRange=None,
                loFrequency=None,
                nElementsPerStrip=None,
                nSubarrays=None,
                zshiftArray=None,
                arrayRadius=None,
                elementSpacing=None,
                tfReceiverBinWidth=None,
                tfReceiverFilename=None,
                xmlFilename=None,
                randomSeed=None,
                noiseFloorPsd=None,
                noiseTemperature=None):
        
        self.__configDict = {}
        self.__configDict[self.__sGen] = [self.__sArray, self.__sFft, self.__sDec, self.__sDigit]
        self.__set(self.__sSim, self.__sNChannels, nChannels)
        self.__set(self.__sSim, self.__sEggFilename, eggFilename)
        self.__set(self.__sSim, self.__sRecordSize, recordSize)
        self.__set(self.__sSim, self.__sNRecords, nRecords)
        
        self.__set(self.__sDigit, self.__sVRange, vRange)
        
        self.__set(self.__sArray, self.__sLoFrequency, loFrequency)
        self.__set(self.__sArray, self.__sNelementsPerStrip, nElementsPerStrip)
        self.__set(self.__sArray, self.__sNSubarrays, nSubarrays)
        self.__set(self.__sArray, self.__sZshiftArray, zshiftArray)
        self.__set(self.__sArray, self.__sArrayRadius, arrayRadius)
        self.__set(self.__sArray, self.__sElementSpacing, elementSpacing)
        self.__set(self.__sArray, self.__sTfReceiverBinWidth, tfReceiverBinWidth)
        self.__set(self.__sArray, self.__sTfReceiverFilename, tfReceiverFilename)
        self.__set(self.__sArray, self.__sXmlFilename, xmlFilename)
        
        self.__set(self.__sNoise, self.__sRandomSeed, randomSeed)
        self.__set(self.__sNoise, self.__sNoiseFloorPsd, noiseFloorPsd)
        self.__set(self.__sNoise, self.__sNoiseTemperature, noiseTemperature)
        
        self.__finalize(templateConfig)
        
    def __set(self, key0, key1, value):
        
        if value is not None:
            if not key0 in self.__configDict:
                self.__configDict[key0] = {}
            self.__configDict[key0][key1] = value
            
    def __prefix(self, key0, key1, value):
        
        self.__configDict[key0][key1] = value + self.__configDict[key0][key1]
            
    def __finalize(self, templateConfig):
        
        self.__addDefaults(templateConfig)
        self.__handleNoise()
        self.__set(self.__sDigit, self.__sVOffset, -self.__configDict[self.__sDigit][self.__sVRange]/2)
        self.__adjustPaths()
        
    def __addDefaults(self, templateConfig):
                    
        for key in templateConfig:
            #get value from config template if it was not set
            if key not in self.__configDict:
                self.__configDict[key] = templateConfig[key]
            else:
                for subKey in templateConfig[key]:
                    if subKey not in self.__configDict[key]:
                        self.__configDict[key][subKey] = templateConfig[key][subKey]
                       
    def __handleNoise(self):
        
        if self.__sNoise in self.__configDict:

            if (self.__sNoiseFloorPsd or self.__sNoiseTemp) in self.__configDict[self.__sNoise]:
                self.__configDict[self.__sGen].insert(-1, self.__sNoise)

            if (self.__sNoiseFloorPsd and self.__sNoiseTemperature) in self.__configDict[self.__sNoise]:
                #prefer noise temperature over noise psd
                self.__configDict[self.__sNoise].pop(self.__sNoiseFloorPsd)

            if self.__sRandomSeed not in self.__configDict[self.__sNoise]:
                self.__set(self.__sNoise, self.__sRandomSeed, _getRandSeed())
                
    def __adjustPaths(self):
        
        self.__prefix(self.__sArray, self.__sXmlFilename, '/tmp/output/')
        self.__prefix(self.__sSim, self.__sEggFilename, '/tmp/output/')
        self.__prefix(self.__sArray, self.__sTfReceiverFilename, '/hexbug/Phase3/TransferFunctions/')
            
    def makeConfigFile(self, outPath):
        
        with open(outPath, 'w') as outFile:
            json.dump(self.__configDict, outFile, indent=2)
        

class SimConfig:
    
    def __init__(self, 
                    locustVersion,
                    nChannels=None,
                    noiseTemp=None,
                    vRange = None,
                    vOffset = None,
                    eggPath = None,
                    locustTemplate = None,
                    kassTemplate = None,
                    recordSize = None,
                    loFrequency = None,
                    elementsPerStrip = None,
                    nSubarrays = None,
                    zShift = None,
                    elementSpacing = None,
                    seedKass = None,
                    seedLocust= None,
                    tfReceiverBinWidth = None, 
                    tfReceiverFilename = 'FiveSlotTF.txt',
                    tMax=0.5e-4,
                    xMin=0.0,
                    xMax=0.0,
                    yMin=0.0,
                    yMax=0.0,
                    zMin=0.0,
                    zMax=0.0,
                    pitchMin=90.0,
                    pitchMax=90.0,
                    geometry='FreeSpaceGeometry_V00_00_10.xml'):
       
        
        
        #files
        self.locustTemplate = locustTemplate
        self.kassTemplate = kassTemplate
        
        #noisePower = getNoisePower(snr)
        self.locustConfig = LocustConfig(nChannels,
                                        None, # noise-psd not used
                                        noiseTemp,
                                        vRange,
                                        vOffset,
                                        eggPath,
                                        recordSize,
                                        loFrequency,
                                        elementsPerStrip,
                                        nSubarrays,
                                        zShift,
                                        elementSpacing,
                                        seedLocust,
                                        tfReceiverBinWidth,
                                        tfReceiverFilename)
                                        
        self.kassConfig = KassConfig(seedKass,
                                        tMax,
                                        xMin,
                                        xMax,
                                        yMin,
                                        yMax,
                                        zMin,
                                        zMax,
                                        pitchMin,
                                        pitchMax,
                                        geometry,
                                        locustVersion)
                                        
    def setXml(self, name):
        self.locustConfig.xmlFile=name
        
    def setEgg(self, name):
        self.locustConfig.eggPath=name
    
    def toJson(self, filename):
        
        with open(filename, 'w') as outfile:
            json.dump(self.__dict__, outfile, indent=2, 
                            default=lambda x: x.__dict__)
                            
    def toDict(self):
        
        return {**self.locustConfig.__dict__, **self.kassConfig.__dict__}
            
    @classmethod
    def fromJson(cls, filename):
        
        instance = cls(locustVersion='v2.1.6')
        instance.locustConfig = LocustConfig()
        instance.kassConfig = KassConfig()
        
        with open(filename, 'r') as infile:
            config = json.load(infile)
            instance.locustTemplate = config['locustTemplate']
            instance.kassTemplate = config['kassTemplate']
            instance.locustConfig.__dict__ = config['locustConfig']
            instance.kassConfig.__dict__ = config['kassConfig']
            
        return instance
        
    def makeConfig(self, filenamelocust, filenamekass):
        self.locustConfig.makeLocustConfig(self.locustTemplate, filenamelocust)
        self.kassConfig.makeKassConfig(self.kassTemplate, filenamekass)


class KassLocustP3:
    
    def __init__(self, workingdir, hexbugdir,
                container='project8/p8compute',
                locustversion='v2.1.2', 
                p8computeversion='v0.10.1'):
                            
        self.workingdir=workingdir+'/'
        self.outputdir = self.workingdir+'output/'
        self.locustversion=locustversion
        self.p8computeversion=p8computeversion
        self.p8locustdir='/usr/local/p8/locust/'+locustversion
        self.p8computedir='/usr/local/p8/compute/'+p8computeversion
        self.container=container
        self.hexbugdir=hexbugdir
        
        self._genCommandScript()
        
    def run(self, config, filename):
        
        #try: # Locust
         #   output = call_locust(locust_config_path)
        #except subprocess.CalledProcessError as e:
        
        filenamelocust = filename+'locust.json'
        filenamekass = filename+'kass.xml'
        config.setXml('/tmp/output/'+filenamekass)
        config.setEgg(self.p8locustdir+'/output/'+filename+'.egg')
        config.makeConfig(self.outputdir+filenamelocust, 
                            self.outputdir+filenamekass)
        config.toJson(self.outputdir+filename+'config.json')
        
        cmd = self._assembleCommand('/tmp/output/'+filename)
        
        print(cmd)
        
        os.system(cmd)
        
        deleteCmd = 'rm -f ' + self.outputdir+filenamelocust
        deleteCmd += ' ' + self.outputdir+filenamekass
        deleteCmd += ' ' + self.outputdir+'Phase3Seed*Output.root'
        
        os.system(deleteCmd)

        
    def _assembleCommand(self, configFile):
        cmd = 'docker run -it --rm -v '
        cmd += self.workingdir
        cmd += ':/tmp -v '
        cmd += self.workingdir
        cmd += '/output:'
        cmd += self.p8locustdir
        cmd += '/output -v '
        cmd += self.hexbugdir
        cmd += ':/hexbug '
        cmd += self.container
        cmd += ' /bin/bash -c "/tmp/locustcommands.sh '
        cmd += configFile
        cmd += 'locust.json"'
        
        return cmd
        
    def _genCommandScript(self):
        
        commands = '#!/bin/bash\n'
        commands += 'source ' + self.p8computedir+'/setup.sh\n'
        commands += 'source ' + self.p8locustdir+'/bin/kasperenv.sh\n'
        commands += 'LocustSim config=$1'
        
        with open(self.workingdir+'locustcommands.sh', 'w') as outFile:
            outFile.write(commands)
            
        os.system('chmod +x '+self.workingdir+'locustcommands.sh')
        

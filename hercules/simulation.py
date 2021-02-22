
"""

Author: F. Thomas
Date: February 19, 2021

"""

import time
import json
import re

def _getRandSeed():
    
    t = int( time.time() * 1000.0 )
    seed = ((t & 0xff000000) >> 24) +\
             ((t & 0x00ff0000) >>  8) +\
             ((t & 0x0000ff00) <<  8) +\
             ((t & 0x000000ff) << 24)
             
    return seed
 
def _getJsonFromFile(locustFile):
    with open(locustFile, 'r') as infile:
        return json.load(infile)
        
def _getXmlFromFile(xmlFile):
    with open(xmlFile) as conf:
        return conf.read()

def _writeXmlFile(outPath, xml):
    with open(outPath, 'w') as newConf:
        newConf.write(xml)   
    
class KassConfig:
    
    #https://www.regular-expressions.info/floatingpoint.html
    __floatRegex = re.compile('"([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)"') #not used
    __intRegex = re.compile('"(\d+)"') #not used
    __matchAllRegex = re.compile('"(.+?)"')
    
    __sSeed = '<external_define name="seed" value='
    __sOutpath = '<external_define name="output_path" value='
    __sGeometry = '<geometry>\n    <include name='
    __sXVal = '<x_uniform value_min='
    __sYVal = '<y_uniform value_min='
    __sZVal = '<z_uniform value_min='
    __sThetaVal = '<theta_uniform value_min='
    __sTMax = '<ksterm_max_time name="term_max_time" time='
    
    
    __sMax = ' value_max='
    
    __expressionDictSimple = {'seedKass': __sSeed,
                               'tMax': __sTMax,
                               'geometry': __sGeometry,
                               'outPath': __sOutpath }
                       
    __expressionDictComplex = {'xMin': __sXVal,
                               'yMin': __sYVal,
                               'zMin': __sZVal,
                               'pitchMin': __sThetaVal }
    
    def __init__(self,
                filename,
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
                geometry = None,
                outPath = None):
                #geometry = 'FreeSpaceGeometry_V00_00_04.xml',
                #locustVersion ='v2.1.6'):
        
        # returns a dictionary with all defined local variables up to this point
        # dictionary does not change when more variables are declared later 
        # -> It is important that this stays at the top!
        # https://stackoverflow.com/questions/2521901/get-a-list-tuple-dict-of-the-arguments-passed-to-a-function
        self.__configDict = locals()
         # remove 'self' and 'filename' from the dictionary
        self.__configDict.pop('self', None)
        self.__configDict.pop('filename', None)
        self.__xml = _getXmlFromFile(filename)
        self.__addDefaults()
 
    def __addDefaults(self):
        
        self.__addComplexDefaults(self.__xml)
        self.__addSimpleDefaults(self.__xml)
                        
    def __getMinMaxVal(self, expression, string):
        regex = expression+self.__matchAllRegex.pattern\
            +self.__sMax+self.__matchAllRegex.pattern
        result = re.findall(regex, string)
        minVal = result[0][0]
        maxVal = result[0][1]
        
        return minVal, maxVal
        
    def __getVal(self, expression, string):
        
        regex = expression+self.__matchAllRegex.pattern
        result = re.findall(regex, string)
        val = result[0]
        
        return val
        
    def __addSimpleDefaults(self, xml):
        
        for key in self.__expressionDictSimple:
            if self.__configDict[key] is None:
                self.__configDict[key] =(
                    self.__getVal(self.__expressionDictSimple[key], xml) )
                
    def __addComplexDefaults(self, xml):
        
        for key in self.__expressionDictComplex:
            if self.__configDict[key] is None:
                minVal, maxVal =( 
                    self.__getMinMaxVal(self.__expressionDictComplex[key], xml))
                self.__configDict[key] = minVal
                self.__configDict[key[:-3]+'Max'] = maxVal
     
    def __replaceSimple(self, key, string):
        
        return re.sub(self.__expressionDictSimple[key]\
                        +self.__matchAllRegex.pattern,
                        self.__expressionDictSimple[key]\
                        +'"'+str(self.__configDict[key])+'"', string)
        
    def __replaceComplex(self, key, string):
        
        return re.sub(self.__expressionDictComplex[key]\
                        +self.__matchAllRegex.pattern\
                        +self.__sMax\
                        +self.__matchAllRegex.pattern,
                        self.__expressionDictComplex[key]\
                        +'"'+str(self.__configDict[key])+'"'\
                        +self.__sMax\
                        +'"'+str(self.__configDict[key[:-3]+'Max'])+'"', string)
                        
    def __replaceAll(self):
        
        xml = self.__xml
        for key in self.__expressionDictComplex:
            xml = self.__replaceComplex(key, xml)
            
        for key in self.__expressionDictSimple:
            xml = self.__replaceSimple(key, xml)
            
        return xml
    
    def makeConfigFile(self, outPath):
        
        xml = self.__replaceAll()
        _writeXmlFile(outPath, xml)
        

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
                filename,
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
        
        #locals() hack not possible here since we need a nested dictionary
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
        
        templateConfig = _getJsonFromFile(filename)
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
        

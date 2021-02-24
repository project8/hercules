
"""

Author: F. Thomas
Date: February 19, 2021

"""

import time
import json
import re
from pathlib import Path, PosixPath
import os
import subprocess

_moduleDir = Path(__file__).parent.absolute()
_hexbugDir = _moduleDir / 'hexbug'
#container is running linux
#-> make sure it's PosixPath when run from windows
_hexbugDirContainer = PosixPath('/') / 'tmp'
_outputDirContainer = PosixPath('/') / 'home' 
_LocustConfigName = 'LocustPhase3Template.json'
_KassConfigName = 'LocustKassElectrons.xml'
_SimConfigName = 'SimConfig.json'

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
                filename=_hexbugDir/'Phase3'/_KassConfigName,
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
                geometry = None):
        
        # returns a dictionary with all defined local variables up to this point
        # dictionary does not change when more variables are declared later 
        # -> It is important that this stays at the top!
        # https://stackoverflow.com/questions/2521901/get-a-list-tuple-dict-of-the-arguments-passed-to-a-function
        self.__configDict = locals()
        
         # remove 'self' and 'filename' from the dictionary
        self.__configDict.pop('self', None)
        self.__configDict.pop('filename', None)
        self.__xml = _getXmlFromFile(filename)
        self.__configDict['outPath'] = str(_outputDirContainer)
        self.__addDefaults()
        self.__adjustPaths()
 
    @property
    def configDict(self):
        return self.__configDict 
    
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
        
    def __prefix(self, key, value):
        
        self.__configDict[key] = value + self.__configDict[key].split('/')[-1]
                                
    def __adjustPaths(self):
        
        self.__prefix('geometry', str(_hexbugDirContainer)+'/Phase3/Trap/')
        #self.__prefix('outPath', '/output/')
        
                        
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
                filename = _hexbugDir/'Phase3'/_LocustConfigName,
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
    
    @property
    def configDict(self):
        return self.__configDict 
    
    def __set(self, key0, key1, value):
        
        if value is not None:
            if not key0 in self.__configDict:
                self.__configDict[key0] = {}
            self.__configDict[key0][key1] = value
            
    def setXml(self, path):
        
        name = path.name
        self.__set(self.__sArray, self.__sXmlFilename, 
                    str(_outputDirContainer / name))
            
    def __prefix(self, key0, key1, value):
        
        self.__configDict[key0][key1] =(
                        value + self.__configDict[key0][key1].split('/')[-1])
            
    def __finalize(self, templateConfig):
        
        self.__addDefaults(templateConfig)
        self.__handleNoise()
        self.__set(self.__sDigit, self.__sVOffset, 
                    -self.__configDict[self.__sDigit][self.__sVRange]/2)
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
        
        self.__prefix(self.__sArray, self.__sXmlFilename, 
                        str(_outputDirContainer) + '/')
        self.__prefix(self.__sSim, self.__sEggFilename, 
                        str(_outputDirContainer) + '/')
        self.__prefix(self.__sArray, self.__sTfReceiverFilename, 
                        str(_hexbugDirContainer)+'/Phase3/TransferFunctions/')
            
    def makeConfigFile(self, outPath):
        
        with open(outPath, 'w') as outFile:
            json.dump(self.__configDict, outFile, indent=2)
        

class SimConfig:
    
    def __init__(self, 
                kassTemplate=_hexbugDir/'Phase3'/_KassConfigName,
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
                locustTemplate=_hexbugDir/'Phase3'/_LocustConfigName,
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
                seedLocust=None,
                noiseFloorPsd=None,
                noiseTemperature=None):
       
        
        
        #files
        self.__locustTemplate = locustTemplate
        self.__kassTemplate = kassTemplate
        
        self.__locustConfig = LocustConfig(filename=locustTemplate,
                                            nChannels=nChannels,
                                            eggFilename=eggFilename,
                                            recordSize=recordSize,
                                            nRecords=nRecords,
                                            vRange=vRange,
                                            loFrequency=loFrequency,
                                            nElementsPerStrip=nElementsPerStrip,
                                            nSubarrays=nSubarrays,
                                            zshiftArray=zshiftArray,
                                            arrayRadius=arrayRadius,
                                            elementSpacing=elementSpacing,
                                            tfReceiverBinWidth=tfReceiverBinWidth,
                                            tfReceiverFilename=tfReceiverFilename,
                                            xmlFilename=xmlFilename,
                                            randomSeed=seedLocust,
                                            noiseFloorPsd=noiseFloorPsd,
                                            noiseTemperature=noiseTemperature)
                                        
        self.__kassConfig = KassConfig(filename = kassTemplate,
                                        seedKass = seedKass,
                                        tMax = tMax,
                                        xMin = xMin,
                                        xMax = xMax,
                                        yMin = yMin,
                                        yMax = yMax,
                                        zMin = zMin,
                                        zMax = zMax,
                                        pitchMin = pitchMin,
                                        pitchMax = pitchMax,
                                        geometry = geometry)
    
    def toJson(self, filename):
        
        with open(filename, 'w') as outfile:
            json.dump({'kassConfig': self.__kassConfig, 
                        'locustConfig': self.__locustConfig}, outfile, indent=2, 
                            default=lambda x: x.configDict)
 
                            
    def toDict(self):
        
        return {**self.__locustConfig.configDict, **self.__kassConfig.configDict}
            
    @classmethod
    def fromJson(cls, filename):
        
        instance = cls()
        
        with open(filename, 'r') as infile:
            config = json.load(infile)
            
            #accessing 'private' data members; don't do that at home! ;)
            instance.__locustConfig._LocustConfig__configDict = config['locustConfig']
            instance.__kassConfig._KassConfig__configDict = config['kassConfig']
            
        return instance
        
    def makeConfigFile(self, filenamelocust, filenamekass):
        self.__locustConfig.setXml(filenamekass)
        self.__locustConfig.makeConfigFile(filenamelocust)
        self.__kassConfig.makeConfigFile(filenamekass)

def _genShareDirString(dirOutside, dirContainer):
    
    return ('-v '
               + str(dirOutside)
               + ':'
               + str(dirContainer))
               
def _genShareDirStringSingularity(dirOutside, dirContainer):
    
    return ('--bind '
               + str(dirOutside)
               + ':'
               + str(dirContainer))
               
def _charConcatenate(char, *strings):
    
    output = ''
    for s in strings:
        output += s + char
        
    return output[:-1] #no extra char at the end

class KassLocustP3:
    
    __workingDirContainer = PosixPath('/') / 'workingdir'
    __commandScriptName = 'locustcommands.sh'
    
    def __init__(self, workingdir,
                container='project8/p8compute',
                locustversion='v2.1.2', 
                p8computeversion='v0.10.1'):
                            
        self.__workingdir=Path(workingdir)
        
        self.__workingdir.mkdir(parents=True, exist_ok=True)
        
        self.__locustversion=locustversion
        self.__p8computeversion=p8computeversion
        self.__p8locustdir=PosixPath('/usr/local/p8/locust') / locustversion
        self.__p8computedir=PosixPath('/usr/local/p8/compute') / p8computeversion
        self.__container=container
        
        
        self._genCommandScript()
        
    def __call__(self, config, name):
        
        outputdir = self.__workingdir / name
        outputdir.mkdir(parents=True, exist_ok=True)
        
        locustFile = outputdir / _LocustConfigName
        kassFile = outputdir / _KassConfigName
        configDump = outputdir / _SimConfigName

        config.makeConfigFile(locustFile, kassFile)
        config.toJson(configDump)
        
        cmd = self._assembleCommand(outputdir)
        
        print(cmd)
        
        subprocess.Popen(cmd, shell=True).wait()
        
        #deleteCmd = 'rm -f ' + outputdir+filenamelocust
        #deleteCmd += ' ' + outputdir+filenamekass
        #deleteCmd += ' ' + outputdir+'Phase3Seed*Output.root'
        
        #os.system(deleteCmd)
        
    def _assembleCommand(self, outputdir):
        
        dockerRun = 'docker run -it --rm'
        
        bashCommand = ('"'
                       + str(self.__workingDirContainer/self.__commandScriptName)
                       + ' '
                       + str(_outputDirContainer/_LocustConfigName)
                       + '"')
                       
        dockerCmd = '/bin/bash -c ' + bashCommand
        
        shareWorkingDir = _genShareDirString(self.__workingdir, 
                                            self.__workingDirContainer)
                           
        shareOutputDir = _genShareDirString(outputdir,
                                            _outputDirContainer)
                                            
        shareHexbugDir = _genShareDirString(_hexbugDir, _hexbugDirContainer)
        
        cmd = _charConcatenate(' ', dockerRun, shareWorkingDir, shareOutputDir, 
                                shareHexbugDir, self.__container, dockerCmd)
        
        return cmd
        
    def _genCommandScript(self):
        
        shebang = '#!/bin/bash'
        p8env = _charConcatenate(' ', 'source', 
                                 str(self.__p8computedir/'setup.sh'))
        kasperenv = _charConcatenate(' ', 'source',
                                 str(self.__p8locustdir/'bin'/'kasperenv.sh'))
        locust = 'LocustSim config=$1'
        
        commands = _charConcatenate('\n', shebang, p8env, kasperenv, locust)
        
        script = self.__workingdir/self.__commandScriptName
        with open(script, 'w') as outFile:
            outFile.write(commands)
            
        subprocess.Popen('chmod +x ' + str(script), shell=True).wait()
        
class KassLocustP3Cluster:
    
    __p8computeSingularity = Path('/home/ps48/project/singularity_p8compute/p8compute_latest.sif')
    __commandScriptName = 'locustcommands.sh'
    __jobScriptName = 'JOB.sh'

    def __init__(self, workingdir,
                container='project8/p8compute',
                locustversion='v2.1.2', 
                p8computeversion='v0.10.1'):
        
        self.__workingdir=Path(workingdir)
        self.__workingdir.mkdir(parents=True, exist_ok=True)
        self.__locustversion=locustversion
        self.__p8computeversion=p8computeversion
        self.__p8locustdir=PosixPath('/usr/local/p8/locust') / locustversion
        self.__p8computedir=PosixPath('/usr/local/p8/compute') / p8computeversion
        self.__container=container
        
        
    def __call__(self, config, name):
        
        outputdir = self.__workingdir / name
        outputdir.mkdir(parents=True, exist_ok=True)
        
        locustFile = outputdir / 'LocustPhase3Template.json'
        kassFile = outputdir / 'LocustKassElectrons.xml'
        configDump = outputdir / 'SimConfig.json'

        config.makeConfigFile(locustFile, kassFile)
        config.toJson(configDump)
        
        self._genLocustScript(outputdir)
        self._genJobScript(outputdir)
        
        subprocess.Popen('sbatch ' + str(outputdir/self.__jobScriptName), 
                            shell=True).wait()
        
    def _genJobScript(self, outputdir):
        
        """
        Based on https://github.com/project8/scripts/blob/master/YaleP8ComputeScripts/GeneratePhase3Sims.py
        
        """
        
        shebang = '#!/bin/bash'
        jobName = '#SBATCH -J ' + outputdir.name
        jobOutput = '#SBATCH -o ' + str(outputdir) + '/run_singularity.out'
        jobError = '#SBATCH -e ' + str(outputdir) + '/run_singularity.err'
        jobPartition = '#SBATCH -p scavenge'
        jobTimeout = '#SBATCH -t 10:00:00'
        jobCpus = '#SBATCH --cpus-per-task=2'
        jobTasks = '#SBATCH --ntasks=1'
        jobMem = '#SBATCH --mem-per-cpu=15000'
        jobRequeue = '#SBATCH --requeue'
        
        singularityExec = 'singularity exec --no-home'
        shareOutputDir = _genShareDirStringSingularity(outputdir,
                                                        _outputDirContainer)
        shareHexbugDir = _genShareDirStringSingularity(_hexbugDir, 
                                                        _hexbugDirContainer)
        container = str(self.__p8computeSingularity)
        runScript = str(_outputDirContainer/self.__commandScriptName)
        
        singularityCmd = _charConcatenate(' ', singularityExec, shareOutputDir, 
                                            shareHexbugDir, container, 
                                            runScript)
                                            
        commands = _charConcatenate('\n', shebang, jobName, jobOutput, 
                                    jobError, jobPartition, jobTimeout, 
                                    jobCpus, jobTasks, jobMem, jobRequeue,
                                    singularityCmd)
        
        script = outputdir/self.__jobScriptName 
        
        with open(script, 'w') as outFile:
            outFile.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()
    
    def _genLocustScript(self, outputdir):   
        
        shebang = '#!/bin/bash'
        p8env = _charConcatenate(' ', 'source', 
                                 str(self.__p8computedir/'setup.sh'))
        kasperenv = _charConcatenate(' ', 'source',
                                 str(self.__p8locustdir/'bin'/'kasperenv.sh'))
        locust = ('exec LocustSim config='
                  + str(_outputDirContainer/_LocustConfigName))
        
        commands = _charConcatenate('\n', shebang, p8env, kasperenv, locust)
        
        script = outputdir / self.__commandScriptName
        with open(script, 'w') as outFile:
            outFile.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()

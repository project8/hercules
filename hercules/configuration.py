
"""

Author: F. Thomas
Date: February 24, 2021

"""

import configparser
from pathlib import Path

_moduleDir = Path(__file__).parent.absolute()
_configDir = _moduleDir/'settings'/'config.ini'


class Configuration:
    
    def __init__(self):
        
        print('Config created')
        
        config = configparser.ConfigParser()
        config.read(_configDir)
        
        self.__handleEnv()
        
        self.__locustVersion = config['PACKAGE']['LOCUSTVERSION']
        self.__locustPath = config['PACKAGE']['LOCUSTPATH']
        self.__p8computeVersion = config['PACKAGE']['P8COMPUTEVERSION']
        self.__p8computePath = config['PACKAGE']['P8COMPUTEPATH']
                              
    def __handleEnv(self):
        
        self.__env = config['USER']['ENVIRONMENT']
        
        if self.__env == 'desktop':
            self.__container = config['DESKTOP']['CONTAINER']
        elif self.__env == 'grace':
            self.__container = config['GRACE']['CONTAINER']
        else:
            raise ValueError((self.__env 
                              + ' is not a valid environment setting.
                              + ' Check settings/config.ini'))
    
    @property
    def locustVersion():
        return self.__locustVersion
        
    @property
    def locustPath():
        return self.__locustPath

    @property
    def p8computeVersion():
        return self.__p8computeVersion
        
    @property
    def p8computePath():
        return self.__p8computePath
        
    @property
    def env():
        return self.__env
        
    @property
    def container():
        return self.__container

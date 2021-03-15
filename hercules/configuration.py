
"""

Author: F. Thomas
Date: February 24, 2021

"""

__all__ = []

import configparser
from pathlib import Path

_MODULEDIR = Path(__file__).parent.absolute()
_CONFIGDIR = _MODULEDIR/'settings'/'config.ini'


class Configuration:
    
    def __init__(self):
        
        config = configparser.ConfigParser()
        config.read(_CONFIGDIR)
        
        self._handle_env(config)
        
        self._locust_version = config['PACKAGE']['LOCUSTVERSION']
        self._locust_path = config['PACKAGE']['LOCUSTPATH']
        self._p8compute_version = config['PACKAGE']['P8COMPUTEVERSION']
        self._p8compute_path = config['PACKAGE']['P8COMPUTEPATH']
        self._desktop_parallel_jobs = config['USER']['DESKTOP_PARALLEL_JOBS']
        
        self._partition = config['GRACE']['JOB_PARTITION']
        self._job_timelimit = config['GRACE']['JOB_TIMELIMIT']
        self._job_memory = config['GRACE']['JOB_MEMORY']
        self._job_limit = config['GRACE']['JOB_LIMIT']
                              
    def _handle_env(self, config):
        
        self._env = config['USER']['ENVIRONMENT']
        
        if self._env == 'desktop':
            self._container = config['DESKTOP']['CONTAINER']
        elif self._env == 'grace':
            self._container = config['GRACE']['CONTAINER']
        else:
            raise ValueError((self._env 
                              + ' is not a valid environment setting.'
                              + ' Check settings/config.ini'))
    
    @property
    def locust_version(self):
        return self._locust_version
        
    @property
    def locust_path(self):
        return self._locust_path

    @property
    def p8compute_version(self):
        return self._p8compute_version
        
    @property
    def p8compute_path(self):
        return self._p8compute_path
        
    @property
    def env(self):
        return self._env
        
    @property
    def container(self):
        return self._container
        
    @property
    def desktop_parallel_jobs(self):
        return self._desktop_parallel_jobs
        
    @property
    def partition(self):
        return self._partition
        
    @property
    def job_timelimit(self):
        return self._job_timelimit
        
    @property
    def job_memory(self):
        return self._job_memory
        
    @property
    def job_limit(self):
        return self._job_limit

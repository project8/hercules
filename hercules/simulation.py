
"""

Author: F. Thomas
Date: February 19, 2021

"""

__all__ = ['KassLocustP3']

from pathlib import Path, PosixPath
import subprocess
from abc import ABC, abstractmethod
import concurrent.futures as cf
from tqdm import tqdm

from .constants import (HEXBUG_DIR, HEXBUG_DIR_CONTAINER, OUTPUT_DIR_CONTAINER,
                        LOCUST_CONFIG_NAME, KASS_CONFIG_NAME, SIM_CONFIG_NAME, 
                        CONFIG)

def _gen_shared_dir_string(dir_outside, dir_container):
    
    return ('-v '
               + str(dir_outside)
               + ':'
               + str(dir_container))
               
def _gen_shared_dir_string_singularity(dir_outside, dir_container):
    
    return ('--bind '
               + str(dir_outside)
               + ':'
               + str(dir_container))
               
def _char_concatenate(char, *strings):
    
    output = ''
    for s in strings:
        output += s + char
        
    return output[:-1] #no extra char at the end
    
class AbstractKassLocustP3(ABC):
        
    #configuration parameters
    _p8_locust_dir = PosixPath(CONFIG.locust_path) / CONFIG.locust_version
    _p8_compute_dir = PosixPath(CONFIG.p8compute_path) / CONFIG.p8compute_version
        
    def __init__(self, working_dir, direct=True):
            
        #prevents direct instantiation without using the factory
        if direct:
            raise ValueError('Direct instantiation forbidden')
            
        self._working_dir=Path(working_dir)
        self._working_dir.mkdir(parents=True, exist_ok=True)
        
    @abstractmethod
    def __call__(self, config_list):
        pass
        
    @staticmethod
    def factory(name, working_dir):
            
        if name == 'grace':
            return KassLocustP3Cluster(working_dir, direct=False)
        elif name == 'desktop':
            return KassLocustP3Desktop(working_dir, direct=False)
        else:
            raise ValueError('Bad KassLocustP3 creation : ' + name)

class KassLocustP3Desktop(AbstractKassLocustP3):
    
    _working_dir_container = PosixPath('/') / 'workingdir'
    _command_script_name = 'locustcommands.sh'
    _container = CONFIG.container
    
    def __init__(self, working_dir, direct=True):
                            
        AbstractKassLocustP3.__init__(self, working_dir, direct)
        self._gen_command_script()
    
    def __call__(self, config_list):
        
        print('Running jobs in Locust')
        max_workers = int(CONFIG.parallel_jobs)
        with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
            
            futures = [executor.submit(self._submit, config) 
                       for config in config_list]
                       
            for future in tqdm(cf.as_completed(futures), total=len(futures)):
                future.result()
    
    def _submit(self, config):
        
        output_dir = self._working_dir / config.sim_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / LOCUST_CONFIG_NAME
        kass_file = output_dir / KASS_CONFIG_NAME
        config_dump = output_dir / SIM_CONFIG_NAME

        config.make_config_file(locust_file, kass_file)
        config.to_json(config_dump)
        
        cmd = self._assemble_command(output_dir)
        
        log_dir_container = OUTPUT_DIR_CONTAINER / config.sim_name
        
        with open(output_dir/'log.out', 'w+') as log, open(output_dir/'log.err', 'w+') as err:
            p = subprocess.Popen(cmd, shell=True, stdout=log, stderr=err)
        
        p.wait()
        #fix stty; for some reason the multithreading with docker breaks the shell
        subprocess.Popen('stty sane', shell=True).wait()
        
    def _assemble_command(self, output_dir):
        
        docker_run = 'docker run -it --rm'
        
        bash_command = ('"'
                       + str(self._working_dir_container/self._command_script_name)
                       + ' '
                       + str(OUTPUT_DIR_CONTAINER/LOCUST_CONFIG_NAME)
                       + '"')
                       
        docker_command = '/bin/bash -c ' + bash_command
        
        share_working_dir = _gen_shared_dir_string(self._working_dir, 
                                            self._working_dir_container)
                           
        share_output_dir = _gen_shared_dir_string(output_dir,
                                            OUTPUT_DIR_CONTAINER)
                                            
        share_hexbug_dir = _gen_shared_dir_string(HEXBUG_DIR, HEXBUG_DIR_CONTAINER)
        
       # log = '>' + str(output_dir) + '/log.out'
        
        cmd = _char_concatenate(' ', docker_run, share_working_dir, 
                                    share_output_dir, share_hexbug_dir, 
                                    self._container, docker_command)
        
        return cmd
        
    def _gen_command_script(self):
        
        shebang = '#!/bin/bash'
        p8_env = _char_concatenate(' ', 'source', 
                                 str(self._p8_compute_dir/'setup.sh'))
        kasper_env = _char_concatenate(' ', 'source',
                                 str(self._p8_locust_dir/'bin'/'kasperenv.sh'))
        locust = 'LocustSim config=$1'
        
        commands = _char_concatenate('\n', shebang, p8_env, kasper_env, locust)
        
        script = self._working_dir/self._command_script_name
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x ' + str(script), shell=True).wait()
        
class KassLocustP3Cluster(AbstractKassLocustP3):
    
    _singularity = Path(CONFIG.container)
    _command_script_name = 'locustcommands.sh'
    _job_script_name = 'JOB.sh'

    def __init__(self, working_dir, direct=True):
            
        AbstractKassLocustP3.__init__(self, working_dir, direct)
        
    def __call__(self, config_list):
        
        for config in config_list:
            self._submit(config)
            
    
    def _submit(self, config):
        
        output_dir = self._working_dir / config.sim_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / LOCUST_CONFIG_NAME
        kass_file = output_dir / KASS_CONFIG_NAME
        config_dump = output_dir / SIM_CONFIG_NAME

        config.make_config_file(locust_file, kass_file)
        config.to_json(config_dump)
        
        self._gen_locust_script(output_dir)
        self._gen_job_script(output_dir)
        
        subprocess.Popen('sbatch ' + str(output_dir/self._job_script_name), 
                            shell=True).wait()
        
    def _gen_job_script(self, output_dir):
        
        """
        Based on https://github.com/project8/scripts/blob/master/YaleP8ComputeScripts/GeneratePhase3Sims.py
        
        """
        
        shebang = '#!/bin/bash'
        job_name = '#SBATCH -J ' + output_dir.name
        job_output = '#SBATCH -o ' + str(output_dir) + '/run_singularity.out'
        job_error = '#SBATCH -e ' + str(output_dir) + '/run_singularity.err'
        job_partition = '#SBATCH -p ' + CONFIG.partition
        job_timeout = '#SBATCH -t ' + CONFIG.job_timelimit
        job_cpus = '#SBATCH --cpus-per-task=2'
        job_tasks = '#SBATCH --ntasks=1'
        job_mem = '#SBATCH --mem-per-cpu=' + CONFIG.job_memory
        job_requeue = '#SBATCH --requeue'
        
        singularity_exec = 'singularity exec --no-home'
        share_output_dir = _gen_shared_dir_string_singularity(output_dir,
                                                        OUTPUT_DIR_CONTAINER)
        share_hexbug_dir = _gen_shared_dir_string_singularity(HEXBUG_DIR, 
                                                        HEXBUG_DIR_CONTAINER)
        container = str(self._singularity)
        run_script = str(OUTPUT_DIR_CONTAINER/self._command_script_name)
        
        singularity_cmd = _char_concatenate(' ', singularity_exec, share_output_dir, 
                                            share_hexbug_dir, container, 
                                            run_script)
                                            
        commands = _char_concatenate('\n', shebang, job_name, job_output, 
                                    job_error, job_partition, job_timeout, 
                                    job_cpus, job_tasks, job_mem, job_requeue,
                                    singularity_cmd)
        
        script = output_dir/self._job_script_name 
        
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()
    
    def _gen_locust_script(self, output_dir):   
        
        shebang = '#!/bin/bash'
        p8_env = _char_concatenate(' ', 'source', 
                                 str(self._p8_compute_dir/'setup.sh'))
        kasper_env = _char_concatenate(' ', 'source',
                                 str(self._p8_locust_dir/'bin'/'kasperenv.sh'))
        locust = ('exec LocustSim config='
                  + str(OUTPUT_DIR_CONTAINER/LOCUST_CONFIG_NAME))
        
        commands = _char_concatenate('\n', shebang, p8_env, kasper_env, locust)
        
        script = output_dir / self._command_script_name
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()

class KassLocustP3:

    def __init__(self, working_dir):
        self._kass_locust = AbstractKassLocustP3.factory(CONFIG.env, 
                                                          working_dir)

    def __call__(self, config_list):
        if type(config_list) is not list:
            config_list = [config_list]
        return self._kass_locust(config_list)
    

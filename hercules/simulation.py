
"""

Author: F. Thomas
Date: February 19, 2021

"""

__all__ = ['KassLocustP3']

from pathlib import Path, PurePosixPath
import subprocess
from abc import ABC, abstractmethod
import concurrent.futures as cf
from tqdm import tqdm
import platform
os = platform.system()

from hercules.simconfig import ConfigList, SimpleSimConfig
from .dataset import Dataset
from .constants import (HEXBUG_DIR, HEXBUG_DIR_CONTAINER, OUTPUT_DIR_CONTAINER,
                        LOCUST_CONFIG_NAME, KASS_CONFIG_NAME, SIM_CONFIG_NAME, 
                        CONFIG)


def _gen_shared_dir_string(dir_outside, dir_container):
    # Return string for the docker argument for sharing a directory.
    # 
    # Parameters
    # ----------
    # dir_outside : Path 
    #     The path of the host directory that should be shared
    # dir_container : Path
    #     The path of the container directory
    # 
    # Returns
    # -------
    # str
    #     The string for the docker argument
    
    return ('-v '
               + str(dir_outside)
               + ':'
               + str(dir_container))
               
def _gen_shared_dir_string_singularity(dir_outside, dir_container):
    # Return string for the singularity argument for sharing a directory.
    # 
    # Parameters
    # ----------
    # dir_outside : Path
    #     The path of the host directory that should be shared
    # dir_container : Path
    #     The path of the container directory
    # 
    # Returns
    # -------
    # str
    #     The string for the singularity argument
    # 
    
    return ('--bind '
               + str(dir_outside)
               + ':'
               + str(dir_container))
               
def _char_concatenate(fill, *strings):
    # Return a string concatenation of the inputs.
    # 
    # This function concatenates an arbitrary number of strings with another
    # string in between.
    # 
    # Parameters
    # ----------
    # fill : str
    #     String used to fill in between strings
    # *strings : list of str
    #     Arbitrary number of strings
    # 
    # Returns
    # -------
    # str
    #     The concatenated strings
    # 
    
    output = ''
    for s in strings:
        output += s + fill
        
    return output[:-len(fill)] #no extra char at the end
    
def _next_path(path_pattern):
    
    # Return the next free path in a sequentially named list of files.
    # 
    # This implementation was provided by
    # https://stackoverflow.com/questions/17984809/how-do-i-create-an-incrementing-filename-in-python
    # With a path pattern like 'file-%s.txt' this returns the next free path in 
    # the sequence file-1.txt, file-2.txt, file-3.txt, ...  
    # It runs in log(n) time where n is the number of existing files in sequence.
    # 
    # Parameters:
    # -----------
    # path_pattern : str
    #     The string with the pattern for the paths, e.g. 'file-%s.txt'
    # 
    # Returns
    # -------
    # Path
    #     The Path that was found
     
    i = 1

    # First do an exponential search
    while Path(path_pattern % i).is_file():
        i = i * 2

    # Result lies somewhere in the interval (i/2..i]
    # We call this interval (a..b] and narrow it down until a + 1 = b
    a, b = (i // 2, i)
    while a + 1 < b:
        c = (a + b) // 2 # interval midpoint
        a, b = (c, b) if Path(path_pattern % c).is_file() else (a, c)

    return Path(path_pattern % b)

def _create_file_race_condition_free(path_pattern):
    
    # Create the next free file in a sequentially named list without race conditions.
    # 
    # This function creates the next free file in a sequentially named list of 
    # file names as provided by a path name. When multiple threads try to do this
    # in parallel it could happen that another thread already created the next
    # file in the list.
    # 
    # Parameters
    # ----------
    # path_pattern : str
    #     The string with the pattern for the paths, e.g. 'file-%s.txt'
    # 
    # Returns
    # -------
    # Path
    #     The Path to the file that was created
    
    
    created = False
    while not created:
        try:
            path = _next_path(path_pattern)
            with open(path, 'x'):
                created = True
        except FileExistsError:
            pass
            
    return path

    
class AbstractKassLocustP3(ABC):
    """An abstract base class for all KassLocust simulations."""
        
    #configuration parameters
    _p8_locust_dir = PurePosixPath(CONFIG.locust_path) / CONFIG.locust_version
    _p8_compute_dir = PurePosixPath(CONFIG.p8compute_path) / CONFIG.p8compute_version
        
    def __init__(self, working_dir, use_locust=True, use_kass=False,
                        python_script=None, direct=True):
        
        #no docstring since no user should directly instantiate this class
            
        #prevents direct instantiation without using the factory
        if direct:
            raise ValueError('Direct instantiation forbidden')
        
        if (use_kass or use_locust) and os=='Windows':
            raise NotImplementedError('Proper support of Docker is not implemented on Windows!')
            
        self._use_locust= use_locust
        self._use_kass= use_kass
        self._python_script= python_script
        self._python_script_name = python_script
        self._python_script = None if python_script is None else Path(CONFIG.python_script_path) / python_script
        self._working_dir=Path(working_dir)
        self._working_dir.mkdir(parents=True, exist_ok=True)
        
    def __call__(self, config_list, **kwargs):
        """Run a list of simulation jobs in parallel and make the index dictionary file.
        
        Parameters
        ----------
        config_list : ConfigList
            A ConfigList object
        """
        
        self.make_index(config_list)
        self.run(config_list.get_internal_list(), **kwargs)
        
    def make_index(self, config_list):
        
        dataset = Dataset(self._working_dir, config_list)
        dataset.dump()
    
    @abstractmethod
    def run(self, config_list, **kwargs):
        """Run a list of simulation jobs in parallel.
        
        Parameters
        ----------
        config_list : list
            A list of SimConfig objects
        """
        
        pass
        
        
    @staticmethod
    def factory(name, working_dir, use_locust=True, use_kass=False,
                python_script=None):
        """Return an instance of one of the derived classes.
        
        Parameters
        ----------
        name : str
            The string used to identify the subclass, possible values are
            'grace' and 'desktop'
        working_dir: str
            The string for the path to the working directory
        
        Raises
        ------
        ValueError
            If the name is neither 'grace' nor 'desktop'
            
        Returns
        -------
        KassLocustP3Cluster or KassLocustP3Desktop
            An instance of one of the two subclasses
        """
            
        if name == 'grace':
            return KassLocustP3Cluster(working_dir, use_locust=use_locust,
                                        use_kass=use_kass,
                                        python_script=python_script, direct=False)
        elif name == 'desktop':
            return KassLocustP3Desktop(working_dir, use_locust=use_locust,
                                        use_kass=use_kass,
                                        python_script=python_script, direct=False)
        else:
            raise ValueError('Bad KassLocustP3 creation : ' + name)

class KassLocustP3Desktop(AbstractKassLocustP3):
    """A class for running KassLocust on a desktop."""
    
    _working_dir_container = PurePosixPath('/') / 'workingdir'
    _command_script_name = 'locustcommands.sh'
    _container = CONFIG.container
    _max_workers = int(CONFIG.desktop_parallel_jobs)

    def __init__(self, working_dir, use_locust=True, 
                    use_kass=False, python_script=None, direct=True):
        """
        Parameters
        ----------
        working_dir : str
            The string for the path of the working directory
        """
                            
        AbstractKassLocustP3.__init__(self, working_dir, use_locust=use_locust,
                                        use_kass=use_kass,
                                        python_script=python_script, direct=direct)
    
    def run(self, sim_config_list, **kwargs):
        """This method overrides :meth:`AbstractKassLocustP3.__call__`.
        
        Runs a list of simulation jobs in parallel.
        
        Parameters
        ----------
        sim_config_list : list
            A list of SimConfig objects
        """
        
        print('Running jobs')
        with cf.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            
            futures = [executor.submit(self._submit, sim_config) 
                       for sim_config in sim_config_list]
                       
            for future in tqdm(cf.as_completed(futures), total=len(futures)):
                future.result()
    
    def _submit(self, sim_config):
        #Submit the job with the given SimConfig
        #Creates all the necessary configuration files, directories and the
        #json output
        
        output_dir = self._working_dir / sim_config.sim_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / LOCUST_CONFIG_NAME
        kass_file = output_dir / KASS_CONFIG_NAME
        config_dump = output_dir / SIM_CONFIG_NAME

        sim_config.to_json(config_dump)

        if self._use_locust:
            sim_config.make_locust_config_file(locust_file, kass_file)

        if self._use_kass:
            sim_config.make_kass_config_file(kass_file)
        
        if self._use_locust or self._use_kass:
            self._gen_command_script(output_dir)

        cmd = self._assemble_command(output_dir)
        print("Submitting Job:", cmd)

        with open(output_dir/'log.out', 'w+') as log, open(output_dir/'log.err', 'w+') as err:
            p = subprocess.Popen(cmd, shell=True, stdout=log, stderr=err)
        
        p.wait()
        if os!='Windows':
            #fix stty; for some reason the multithreading with docker breaks the shell
            #only if OS is not Windows. on windows command does not exist and so far
            #hercules does not support docker on windows anyway
            subprocess.Popen('stty sane', shell=True).wait()
        
    def _assemble_command(self, output_dir):
        #Assemble the docker command that runs the KassLocust simulation in the
        #p8compute container
        
        cmd = ''
        
        if self._use_locust or self._use_kass:
            
            docker_run = 'docker run -it --rm'
            
            bash_command = ('"'
                           + str(OUTPUT_DIR_CONTAINER/self._command_script_name)
                           + '"')
                           
            docker_command = '/bin/bash -c ' + bash_command

            # share_working_dir = _gen_shared_dir_string(self._working_dir,
            #                                     self._working_dir_container)

            share_output_dir = _gen_shared_dir_string(output_dir,
                                                OUTPUT_DIR_CONTAINER)
                                                
            share_hexbug_dir = _gen_shared_dir_string(HEXBUG_DIR, HEXBUG_DIR_CONTAINER)


            # cmd = _char_concatenate(' ', docker_run, share_working_dir,
            #                             share_output_dir, share_hexbug_dir,
            #                             self._container, docker_command)
            cmd = _char_concatenate(' ', docker_run,
                                share_output_dir, share_hexbug_dir,
                                self._container, docker_command)
            cmd += ';'
                            
        if self._python_script is not None:
            cmd += 'python ' + str(self._python_script) + ' ' + str(output_dir)

        return cmd
        
    def _gen_command_script(self, output_dir):
        #Generate the bash script with the commands for running locust
        #This script will be called from inside the container
        
        shebang = '#!/bin/bash'
        p8_env = _char_concatenate(' ', 'source', 
                                 str(self._p8_compute_dir/'setup.sh'))
        kasper_env = _char_concatenate(' ', 'source',
                                 str(self._p8_locust_dir/'bin'/'kasperenv.sh'))
        sim_command = ''
        if self._use_locust:
            sim_command = ('LocustSim config='
                      + str(OUTPUT_DIR_CONTAINER/LOCUST_CONFIG_NAME))
        else: 
            if self._use_kass:
                sim_command = ('Kassiopeia '
                               + str(OUTPUT_DIR_CONTAINER/KASS_CONFIG_NAME))
        
        commands = _char_concatenate('\n', shebang, p8_env, kasper_env, sim_command)

        script = output_dir/self._command_script_name
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x ' + str(script), shell=True).wait()
        
class KassLocustP3Cluster(AbstractKassLocustP3):
    """A class for running KassLocust on the grace cluster."""
    
    _singularity = Path(CONFIG.container)
    _command_script_name = 'locustcommands.sh'
    _job_script_name = 'joblist%s.txt'

    def __init__(self, working_dir, use_locust=True, 
                use_kass=False, python_script=None, direct=True):
        """
        Parameters
        ----------
        working_dir : str
            The string for the path of the working directory
        """
        
        AbstractKassLocustP3.__init__(self, working_dir, use_locust=use_locust,
                                        use_kass=use_kass,
                                        python_script=python_script, direct=direct)
        
    def run(self, config_list, **kwargs):
        """This method overrides :meth:`AbstractKassLocustP3.__call__`.
        
        Runs a list of simulation jobs in parallel.
        
        Parameters
        ----------
        config_list : list
            A list of SimConfig objects
        """
        
        self._joblist = _create_file_race_condition_free(str(self._working_dir/self._job_script_name))
        
        batch_size = 1 if 'batch_size' not in kwargs else int(kwargs['batch_size'])
        
        if batch_size<1:
            raise ValueError("'batch_size' needs to be >0")
            
        batches = [config_list[i:i + batch_size] for i in range(0, len(config_list), batch_size)]
        
        for batch in batches:
            self._add_job_batch(batch)
            
        self._submit_job(**kwargs)
    
    def _submit_job(self, **kwargs):
        #submits the whole list of jobs via dSQ
        #Based on https://github.com/project8/scripts/blob/master/YaleP8ComputeScripts/GeneratePhase3Sims.py
        
        module = 'module load dSQ;'
        
        n_cpus = 2 if self._use_locust else 1
        n_cpus = n_cpus if 'n_cpus' not in kwargs else kwargs['n_cpus']
        memory = CONFIG.job_memory if 'memory' not in kwargs else kwargs['memory']
        timelimit = CONFIG.job_timelimit if 'timelimit' not in kwargs else kwargs['timelimit']
        partition = CONFIG.partition if 'partition' not in kwargs else kwargs['partition']
        
        dsq = f'dsq --requeue --cpus-per-task={n_cpus} --submit'
        job_file = '--job-file ' + str(self._joblist)
        job_partition = '-p ' + partition
        job_limit = '--max-jobs ' + CONFIG.job_limit
        job_memory = '--mem-per-cpu ' + memory +'m'
        job_timelimit = '-t ' + timelimit
        job_status = '--status-dir ' + str(self._working_dir)
        job_output = '--output /dev/null'
        
        cmd = _char_concatenate(' ', module, dsq, job_file, job_partition, 
                                job_limit, job_memory, job_timelimit, 
                                job_status, job_output)
                                
        print(cmd)
        
        subprocess.Popen(cmd, shell=True).wait()
        
    def _add_job(self, sim_config):
        
        output_dir = self._working_dir / sim_config.sim_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / LOCUST_CONFIG_NAME
        kass_file = output_dir / KASS_CONFIG_NAME
        config_dump = output_dir / SIM_CONFIG_NAME

        sim_config.to_json(config_dump)

        if self._use_locust:
            sim_config.make_locust_config_file(locust_file, kass_file)

        if self._use_kass:
            sim_config.make_kass_config_file(kass_file)
        
        if self._use_locust or self._use_kass:
            self._gen_locust_script(output_dir)
        
        self._gen_locust_script(output_dir)
        cmd = self._assemble_command(output_dir)
        
        return cmd
        
    def _add_job_batch(self, config_list):
        #adds a job to the list of jobs
        #Creates all the necessary configuration files, directories and the
        #json output
        
        cmd = ''
        for config in config_list:
            cmd += self._add_job(config)
        
        cmd +='\n'
        
        with open(self._joblist, 'a+') as out_file:
            out_file.write(cmd)
        
    def _assemble_command(self, output_dir):
        #Assemble the singularity command that runs the KassLocust simulation 
        #in the p8compute singularity container
        
        cmd = '('
        
        if self._use_locust or self._use_kass:
        
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
            
            check_failure = "if [ $? -gt 1 ];then scontrol requeue $SLURM_JOB_ID;fi"
                            
            cmd += singularity_cmd + ';' + check_failure + ';'
            
        if self._python_script is not None:
            cmd += 'module load miniconda; conda activate hercules;'
            cmd += 'python ' + str(self._python_script) + ' ' + str(output_dir)
            
        log = '>' + str(output_dir) + '/log.out'
        err = '2>' + str(output_dir) + '/log.err'
        cmd += ') ' + log + ' ' + err + ';'
        
        return cmd
    
    def _gen_locust_script(self, output_dir):   
        #Generate the bash script with the commands for running locust
        #This script will be called from inside the container
        
        shebang = '#!/bin/bash'
        p8_env = _char_concatenate(' ', 'source', 
                                 str(self._p8_compute_dir/'setup.sh'))
        kasper_env = _char_concatenate(' ', 'source',
                                 str(self._p8_locust_dir/'bin'/'kasperenv.sh'))
        
        sim_command = ''
        if self._use_locust:
            sim_command = ('exec LocustSim config='
                      + str(OUTPUT_DIR_CONTAINER/LOCUST_CONFIG_NAME))
        else: 
            if self._use_kass:
                sim_command = ('exec Kassiopeia '
                               + str(OUTPUT_DIR_CONTAINER/KASS_CONFIG_NAME))
        
        commands = _char_concatenate('\n', shebang, p8_env, kasper_env, sim_command)
        
        script = output_dir / self._command_script_name
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()

class KassLocustP3:
    """Universal class for running KassLocustP3 simulations.
    
    The class serves as a wrapper for the other platform dependent subclasses
    of AbstractKassLocustP3. Internally it wraps the subclass that is 
    determined by the config.ini in hercules/settings. Users should only use
    this class, since it makes user scripts agnostic to the computing platform.
    """
    
    def __init__(self, working_dir, use_locust=True, use_kass=False,
                python_script=None):
        """
        Parameters
        ----------
        working_dir : str
            The string for the path to the working directory
        """

        self._use_locust = use_locust
        self._use_kass = use_kass
        
        self._kass_locust = AbstractKassLocustP3.factory(CONFIG.env, 
                                                          working_dir,
                                                          use_locust=use_locust,
                                                          use_kass=use_kass,
                                                          python_script=python_script)
        
    def _add_python_script_metadata(self, config_list):
        config_list.get_meta_data()['python-script'] = self._kass_locust._python_script_name

    def __call__(self, config_list, **kwargs):
        """Run a list of simulation jobs in parallel.
        
        Parameters
        ----------
        config_list : list or SimConfig
            Either a single SimConfig object or a list
        """
        if type(config_list) is not ConfigList:
            raise TypeError('Needs an instance of ConfigList')
            
        if config_list.get_list_type() is SimpleSimConfig and (self._use_kass or self._use_locust):
            raise TypeError('SimpleSimConfig is not compatible with the use of Locust or Kassiopeia!')
        
        self._add_python_script_metadata(config_list)

        return self._kass_locust(config_list, **kwargs)
    

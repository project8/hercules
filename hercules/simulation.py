
"""

Author: F. Thomas
Date: February 19, 2021

"""

import time
import json
import re
from pathlib import Path, PosixPath
from .configuration import Configuration
import os
import subprocess
from abc import ABC, abstractmethod

_MODULE_DIR = Path(__file__).parent.absolute()
_HEXBUG_DIR = _MODULE_DIR / 'hexbug'
#container is running linux
#-> make sure it's PosixPath when run from windows
_HEXBUG_DIR_CONTAINER = PosixPath('/') / 'tmp'
_OUTPUT_DIR_CONTAINER = PosixPath('/') / 'home' 
_LOCUST_CONFIG_NAME = 'LocustPhase3Template.json'
_KASS_CONFIG_NAME = 'LocustKassElectrons.xml'
_SIM_CONFIG_NAME = 'SimConfig.json'

_CONFIG = Configuration()

def _get_rand_seed():
    
    t = int( time.time() * 1000.0 )
    seed = ((t & 0xff000000) >> 24) +\
             ((t & 0x00ff0000) >>  8) +\
             ((t & 0x0000ff00) <<  8) +\
             ((t & 0x000000ff) << 24)
             
    return seed
 
def _get_json_from_file(locust_file):
    with open(locust_file, 'r') as read_file:
        return json.load(read_file)
        
def _get_xml_from_file(xml_file):
    with open(xml_file) as conf:
        return conf.read()

def _write_xml_file(output_path, xml):
    with open(output_path, 'w') as new_conf:
        new_conf.write(xml)   
    
class KassConfig:
    
    #https://www.regular-expressions.info/floatingpoint.html
    #_float_regex = re.compile('"([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)"') #not used
    #_int_regex = re.compile('"(\d+)"') #not used
    _match_all_regex = re.compile('"(.+?)"')
    
    _seed_expression = '<external_define name="seed" value='
    _output_path_expression = '<external_define name="output_path" value='
    _geometry_expression = '<geometry>\n    <include name='
    _x_val_expression = '<x_uniform value_min='
    _y_val_expression = '<y_uniform value_min='
    _z_val_expression = '<z_uniform value_min='
    _theta_val_expression = '<theta_uniform value_min='
    _t_max_expression = '<ksterm_max_time name="term_max_time" time='
    
    
    _val_max_expression = ' value_max='
    
    _expression_dict_simple = {'seed_kass': _seed_expression,
                               't_max': _t_max_expression,
                               'geometry': _geometry_expression,
                               'output_path': _output_path_expression }
                       
    _expression_dict_complex = {'x_min': _x_val_expression,
                               'y_min': _y_val_expression,
                               'z_min': _z_val_expression,
                               'theta_min': _theta_val_expression }
    
    def __init__(self,
                file_name = _HEXBUG_DIR/'Phase3'/_KASS_CONFIG_NAME,
                seed_kass = None,
                t_max = None,
                x_min = None,
                x_max = None,
                y_min = None,
                y_max = None,
                z_min = None,
                z_max = None,
                theta_min = None,
                theta_max = None,
                geometry = None):
        
        # returns a dictionary with all defined local variables up to this point
        # dictionary does not change when more variables are declared later 
        # -> It is important that this stays at the top!
        # https://stackoverflow.com/questions/2521901/get-a-list-tuple-dict-of-the-arguments-passed-to-a-function
        self._config_dict = locals()
        self._clean_initial_config()
        
        self._handle_seed()
        self._config_dict['output_path'] = str(_OUTPUT_DIR_CONTAINER)
        
        self._xml = _get_xml_from_file(file_name)
        self._add_defaults()
        self._adjust_paths()
 
    @property
    def config_dict(self):
        return self._config_dict 
        
    def _clean_initial_config(self):
        # remove 'self' and 'file_name' from the dictionary
        self._config_dict.pop('self', None)
        self._config_dict.pop('file_name', None)
        
    def _handle_seed(self):
        if not self._config_dict['seed_kass']:
            self._config_dict['seed_kass'] = _get_rand_seed()
    
    def _add_defaults(self):
        
        self._add_complex_defaults()
        self._add_simple_defaults()
                        
    def _get_min_max_val(self, expression, string):
        regex = expression+self._match_all_regex.pattern\
            +self._val_max_expression+self._match_all_regex.pattern
        result = re.findall(regex, string)
        min_val = result[0][0]
        max_val = result[0][1]
        
        return min_val, max_val
        
    def _get_val(self, expression, string):
        
        regex = expression+self._match_all_regex.pattern
        result = re.findall(regex, string)
        val = result[0]
        
        return val
        
    def _add_simple_defaults(self):
        
        for key in self._expression_dict_simple:
            if self._config_dict[key] is None:
                self._config_dict[key] =(
                    self._get_val(self._expression_dict_simple[key], self._xml) )
                
    def _add_complex_defaults(self):
        
        for key in self._expression_dict_complex:
            if self._config_dict[key] is None:
                minVal, maxVal =( 
                    self._get_min_max_val(self._expression_dict_complex[key], self._xml))
                self._config_dict[key] = minVal
                self._config_dict[key[:-3]+'Max'] = maxVal
     
    def _replace_simple(self, key, string):
        
        return re.sub(self._expression_dict_simple[key]\
                        +self._match_all_regex.pattern,
                        self._expression_dict_simple[key]\
                        +'"'+str(self._config_dict[key])+'"', string)
        
    def _replace_complex(self, key, string):
        
        return re.sub(self._expression_dict_complex[key]\
                        +self._match_all_regex.pattern\
                        +self._val_max_expression\
                        +self._match_all_regex.pattern,
                        self._expression_dict_complex[key]\
                        +'"'+str(self._config_dict[key])+'"'\
                        +self._val_max_expression\
                        +'"'+str(self._config_dict[key[:-3]+'max'])+'"', string)
        
    def _prefix(self, key, value):
        
        self._config_dict[key] = value + self._config_dict[key].split('/')[-1]
                                
    def _adjust_paths(self):
        
        self._prefix('geometry', str(_HEXBUG_DIR_CONTAINER)+'/Phase3/Trap/')
        
                        
    def _replace_all(self):
        
        xml = self._xml
        for key in self._expression_dict_complex:
            xml = self._replace_complex(key, xml)
            
        for key in self._expression_dict_simple:
            xml = self._replace_simple(key, xml)
            
        return xml
    
    def make_config_file(self, output_path):
        
        xml = self._replace_all()
        _write_xml_file(output_path, xml)
        

class LocustConfig:
    
    #private class variables to store the json keys
    #if a key changes we can change it here
    _sim_key = 'simulation'
    _array_key = 'array-signal'
    _digit_key = 'digitizer'
    _noise_key = 'gaussian-noise'
    _generators_key = 'generators'
    _fft_key = 'lpf-fft'
    _decimate_key = 'decimate-signal'
    
    _n_channels_key = 'n-channels'
    _egg_filename_key = 'egg-filename'
    _record_size_key = 'record-size'
    _n_records_key = 'n-records'
    _v_range_key = 'v-range'
    _v_offset_key = 'v-offset'
    _lo_frequency_key = 'lo-frequency'
    _nelements_per_strip_key = 'nelements-per-strip'
    _n_subarrays_key = 'n-subarrays'
    _zshift_array_key = 'zshift-array'
    _array_radius_key = 'array-radius'
    _element_spacing_key = 'element-spacing'
    _tf_receiver_bin_width_key = 'tf-receiver-bin-width'
    _tf_receiver_filename_key = 'tf-receiver-filename'
    _xml_filename_key = 'xml-filename'
    _random_seed_key = 'random-seed'
    _noise_floor_psd_key = 'noise-floor-psd'
    _noise_temperature_key = 'noise-temperature'
    
    def __init__(self,
                file_name = _HEXBUG_DIR/'Phase3'/_LOCUST_CONFIG_NAME,
                n_channels = None,
                egg_filename = None,
                record_size = None,
                n_records = None,
                v_range = None,
                lo_frequency = None,
                n_elements_per_strip = None,
                n_subarrays = None,
                zshift_array = None,
                array_radius = None,
                element_spacing = None,
                tf_receiver_bin_width = None,
                tf_receiver_filename = None,
                xml_filename = None,
                random_seed = None,
                noise_floor_psd = None,
                noise_temperature = None):
        
        #locals() hack not possible here since we need a nested dictionary
        self._config_dict = {}
        self._config_dict[self._generators_key] = [self._array_key, self._fft_key, self._decimate_key, self._digit_key]
        self._set(self._sim_key, self._n_channels_key, n_channels)
        self._set(self._sim_key, self._egg_filename_key, egg_filename)
        self._set(self._sim_key, self._record_size_key, record_size)
        self._set(self._sim_key, self._n_records_key, n_records)
        
        self._set(self._digit_key, self._v_range_key, v_range)
        
        self._set(self._array_key, self._lo_frequency_key, lo_frequency)
        self._set(self._array_key, self._nelements_per_strip_key, n_elements_per_strip)
        self._set(self._array_key, self._n_subarrays_key, n_subarrays)
        self._set(self._array_key, self._zshift_array_key, zshift_array)
        self._set(self._array_key, self._array_radius_key, array_radius)
        self._set(self._array_key, self._element_spacing_key, element_spacing)
        self._set(self._array_key, self._tf_receiver_bin_width_key, tf_receiver_bin_width)
        self._set(self._array_key, self._tf_receiver_filename_key, tf_receiver_filename)
        self._set(self._array_key, self._xml_filename_key, xml_filename)
        
        self._set(self._noise_key, self._random_seed_key, random_seed)
        self._set(self._noise_key, self._noise_floor_psd_key, noise_floor_psd)
        self._set(self._noise_key, self._noise_temperature_key, noise_temperature)
        
        templateConfig = _get_json_from_file(file_name)
        self._finalize(templateConfig)
    
    @property
    def config_dict(self):
        return self._config_dict 
    
    def _set(self, key0, key1, value):
        
        if value is not None:
            if not key0 in self._config_dict:
                self._config_dict[key0] = {}
            self._config_dict[key0][key1] = value
            
    def set_xml(self, path):
        
        name = path.name
        self._set(self._array_key, self._xml_filename_key, 
                    str(_OUTPUT_DIR_CONTAINER / name))
            
    def _prefix(self, key0, key1, value):
        
        self._config_dict[key0][key1] =(
                        value + self._config_dict[key0][key1].split('/')[-1])
            
    def _finalize(self, template_config):
        
        self._add_defaults(template_config)
        self._handle_noise()
        self._set(self._digit_key, self._v_offset_key, 
                    -self._config_dict[self._digit_key][self._v_range_key]/2)
        self._adjust_paths()
        
    def _add_defaults(self, template_config):
                    
        for key in template_config:
            #get value from config template if it was not set
            if key not in self._config_dict:
                self._config_dict[key] = template_config[key]
            else:
                for sub_key in template_config[key]:
                    if sub_key not in self._config_dict[key]:
                        self._config_dict[key][sub_key] = template_config[key][sub_key]
                       
    def _handle_noise(self):
        
        if self._noise_key in self._config_dict:

            if (self._noise_floor_psd_key or self.__sNoiseTemp) in self._config_dict[self._noise_key]:
                self._config_dict[self._generators_key].insert(-1, self._noise_key)

            if (self._noise_floor_psd_key and self._noise_temperature_key) in self._config_dict[self._noise_key]:
                #prefer noise temperature over noise psd
                self._config_dict[self._noise_key].pop(self._noise_floor_psd_key)

            if self._random_seed_key not in self._config_dict[self._noise_key]:
                self._set(self._noise_key, self._random_seed_key, _get_rand_seed())
                
    def _adjust_paths(self):
        
        self._prefix(self._array_key, self._xml_filename_key, 
                        str(_OUTPUT_DIR_CONTAINER) + '/')
        self._prefix(self._sim_key, self._egg_filename_key, 
                        str(_OUTPUT_DIR_CONTAINER) + '/')
        self._prefix(self._array_key, self._tf_receiver_filename_key, 
                        str(_HEXBUG_DIR_CONTAINER)+'/Phase3/TransferFunctions/')
            
    def make_config_file(self, output_path):
        
        with open(output_path, 'w') as outFile:
            json.dump(self._config_dict, outFile, indent=2)
        

class SimConfig:
    
    def __init__(self, 
                kass_template = _HEXBUG_DIR/'Phase3'/_KASS_CONFIG_NAME,
                seed_kass = None,
                t_max = None,
                x_min = None,
                x_max = None,
                y_min = None,
                y_max = None,
                z_min = None,
                z_max = None,
                theta_min = None,
                theta_max = None,
                geometry = None,
                locust_template = _HEXBUG_DIR/'Phase3'/_LOCUST_CONFIG_NAME,
                n_channels = None,
                egg_filename = None,
                record_size = None,
                n_records = None,
                v_range = None,
                lo_frequency = None,
                n_elements_per_strip = None,
                n_subarrays = None,
                zshift_array = None,
                array_radius = None,
                element_spacing = None,
                tf_receiver_bin_width = None,
                tf_receiver_filename = None,
                xml_filename = None,
                seed_locust = None,
                noise_floor_psd = None,
                noise_temperature = None):
        
        self._locust_config = LocustConfig(file_name = locust_template,
                                            n_channels = n_channels,
                                            egg_filename = egg_filename,
                                            record_size = record_size,
                                            n_records = n_records,
                                            v_range = v_range,
                                            lo_frequency = lo_frequency,
                                            n_elements_per_strip = n_elements_per_strip,
                                            n_subarrays = n_subarrays,
                                            zshift_array = zshift_array,
                                            array_radius = array_radius,
                                            element_spacing = element_spacing,
                                            tf_receiver_bin_width = tf_receiver_bin_width,
                                            tf_receiver_filename = tf_receiver_filename,
                                            xml_filename = xml_filename,
                                            random_seed = seed_locust,
                                            noise_floor_psd = noise_floor_psd,
                                            noise_temperature = noise_temperature)
                                        
        self._kass_config = KassConfig(file_name = kass_template,
                                        seed_kass = seed_kass,
                                        t_max = t_max,
                                        x_min = x_min,
                                        x_max = x_max,
                                        y_min = y_min,
                                        y_max = y_max,
                                        z_min = z_min,
                                        z_max = z_max,
                                        theta_min = theta_min,
                                        theta_max = theta_max,
                                        geometry = geometry)
    
    def to_json(self, file_name):
        
        with open(file_name, 'w') as outfile:
            json.dump({'kassConfig': self._kass_config, 
                        'locustConfig': self._locust_config}, outfile, 
                        indent=2, default=lambda x: x.config_dict)
 
                            
    def to_dict(self):
        
        return {**self._locust_config.config_dict, 
                **self._kass_config.config_dict}
            
    @classmethod
    def from_json(cls, file_name):
        
        instance = cls()
        
        with open(file_name, 'r') as infile:
            config = json.load(infile)
            
            #accessing 'private' data members; don't do that at home! ;)
            instance._locust_config._config_dict = config['locustConfig']
            instance._kass_config._config_dict = config['kassConfig']
            
        return instance
        
    def make_config_file(self, filename_locust, filename_kass):
        self._locust_config.set_xml(filename_kass)
        self._locust_config.make_config_file(filename_locust)
        self._kass_config.make_config_file(filename_kass)

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
    _p8_locust_dir = PosixPath(_CONFIG.locust_path) / _CONFIG.locust_version
    _p8_compute_dir = PosixPath(_CONFIG.p8compute_path) / _CONFIG.p8compute_version
        
    def __init__(self, working_dir, direct=True):
            
        #prevents direct instantiation without using the factory
        if direct:
            raise ValueError('Direct instantiation forbidden')
            
        self._working_dir=Path(working_dir)
        self._working_dir.mkdir(parents=True, exist_ok=True)
        
    @abstractmethod
    def __call__(self, config, name):
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
    _container = _CONFIG.container
    
    def __init__(self, working_dir, direct=True):
                            
        AbstractKassLocustP3.__init__(self, working_dir, direct)
        self._gen_command_script()
        
    def __call__(self, config, name):
        
        output_dir = self._working_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / _LOCUST_CONFIG_NAME
        kass_file = output_dir / _KASS_CONFIG_NAME
        config_dump = output_dir / _SIM_CONFIG_NAME

        config.make_config_file(locust_file, kass_file)
        config.to_json(config_dump)
        
        cmd = self._assemble_command(output_dir)
        
        print(cmd)
        
        subprocess.Popen(cmd, shell=True).wait()
        
    def _assemble_command(self, output_dir):
        
        docker_run = 'docker run -it --rm'
        
        bash_command = ('"'
                       + str(self._working_dir_container/self._command_script_name)
                       + ' '
                       + str(_OUTPUT_DIR_CONTAINER/_LOCUST_CONFIG_NAME)
                       + '"')
                       
        docker_command = '/bin/bash -c ' + bash_command
        
        share_working_dir = _gen_shared_dir_string(self._working_dir, 
                                            self._working_dir_container)
                           
        share_output_dir = _gen_shared_dir_string(output_dir,
                                            _OUTPUT_DIR_CONTAINER)
                                            
        share_hexbug_dir = _gen_shared_dir_string(_HEXBUG_DIR, _HEXBUG_DIR_CONTAINER)
        
        cmd = _char_concatenate(' ', docker_run, share_working_dir, share_output_dir, 
                                share_hexbug_dir, self._container, docker_command)
        
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
    
    _singularity = Path(_CONFIG.container)
    _command_script_name = 'locustcommands.sh'
    _job_script_name = 'JOB.sh'

    def __init__(self, working_dir, direct=True):
            
        AbstractKassLocustP3.__init__(self, working_dir, direct)
        
    def __call__(self, config, name):
        
        output_dir = self._working_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        locust_file = output_dir / _LOCUST_CONFIG_NAME
        kass_file = output_dir / _KASS_CONFIG_NAME
        config_dump = output_dir / _SIM_CONFIG_NAME

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
        job_partition = '#SBATCH -p scavenge'
        job_timeout = '#SBATCH -t 10:00:00'
        job_cpus = '#SBATCH --cpus-per-task=2'
        job_tasks = '#SBATCH --ntasks=1'
        job_mem = '#SBATCH --mem-per-cpu=15000'
        job_requeue = '#SBATCH --requeue'
        
        singularity_exec = 'singularity exec --no-home'
        share_output_dir = _gen_shared_dir_string_singularity(output_dir,
                                                        _OUTPUT_DIR_CONTAINER)
        share_hexbug_dir = _gen_shared_dir_string_singularity(_HEXBUG_DIR, 
                                                        _HEXBUG_DIR_CONTAINER)
        container = str(self._singularity)
        run_script = str(_OUTPUT_DIR_CONTAINER/self._command_script_name)
        
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
                  + str(_OUTPUT_DIR_CONTAINER/_LOCUST_CONFIG_NAME))
        
        commands = _char_concatenate('\n', shebang, p8_env, kasper_env, locust)
        
        script = output_dir / self._command_script_name
        with open(script, 'w') as out_file:
            out_file.write(commands)
            
        subprocess.Popen('chmod +x '+str(script), shell=True).wait()

class KassLocustP3:

    def __init__(self, working_dir):
        self._kass_locust = AbstractKassLocustP3.factory(_CONFIG.env, 
                                                          working_dir)

    def __call__(self, config, name):
        return self._kass_locust(config, name)
    

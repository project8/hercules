
"""

Author: F. Thomas
Date: March 10, 2021

"""

__all__ = ['SimConfig']

import time
import json
import re
from pathlib import Path, PosixPath
from abc import ABC, abstractmethod

from .constants import (HEXBUG_DIR, HEXBUG_DIR_CONTAINER, OUTPUT_DIR_CONTAINER,
                        LOCUST_CONFIG_NAME_P2, KASS_CONFIG_NAME_P2,
                        LOCUST_CONFIG_NAME_P3, KASS_CONFIG_NAME_P3)

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
    
    _config_path_expression = '<external_define name="config_path" value='
    
    _seed_expression = '<external_define name="seed" value='
    _output_path_expression = '<external_define name="output_path" value='
    _geometry_expression = '<geometry>\n    <include name='
    _x_val_expression = '<x_uniform value_min='
    _y_val_expression = '<y_uniform value_min='
    _z_val_expression = '<z_uniform value_min='
    _theta_val_expression = '<theta_uniform value_min='
    _t_max_expression = '<ksterm_max_time name="term_max_time" time='
    _energy_expression = '<energy_fix value='
    
    _val_max_expression = ' value_max='
    
    _expression_dict_simple = {'seed_kass': _seed_expression,
                               't_max': _t_max_expression,
                               'geometry': _geometry_expression,
                               'output_path': _output_path_expression,
                               'config_path': _config_path_expression,
                               'energy': _energy_expression }
                       
    _expression_dict_complex = {'x_min': _x_val_expression,
                               'y_min': _y_val_expression,
                               'z_min': _z_val_expression,
                               'theta_min': _theta_val_expression }
    
    def __init__(self,
                phase = 'Phase3',
                file_name = None,
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
                energy = None):
        
        # returns a dictionary with all defined local variables up to this point
        # dictionary does not change when more variables are declared later 
        # -> It is important that this stays at the top!
        # https://stackoverflow.com/questions/2521901/get-a-list-tuple-dict-of-the-arguments-passed-to-a-function
        self._config_dict = locals()
        self._clean_initial_config()
        
        self._handle_phase(phase, file_name)
        
        self._handle_seed()
        self._config_dict['output_path'] = str(OUTPUT_DIR_CONTAINER)
        self._config_dict['config_path'] = str(self._config_path)
        
        self._xml = _get_xml_from_file(self._file_name)
        self._add_defaults()
        self._adjust_paths()
 
    # -------- private part --------
    
    def _handle_phase(self, phase, file_name):
        
        allowed = phase=='Phase2' or phase =='Phase3'
        
        if allowed:
            
            self._config_path = HEXBUG_DIR_CONTAINER/phase
            
            if file_name is None:
                file_name = (KASS_CONFIG_NAME_P3 if phase=='Phase3' else
                                KASS_CONFIG_NAME_P2)
            
            self._file_name = HEXBUG_DIR/phase/file_name
            
        else:
            raise ValueError('Only "Phase2" or "Phase3" are supported')
        
    def _clean_initial_config(self):
        # remove 'self' and 'file_name' from the dictionary
        self._config_dict.pop('self', None)
        self._config_dict.pop('file_name', None)
        self._config_dict.pop('phase', None)
        
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
                self._config_dict[key[:-3]+'max'] = maxVal
     
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
        
        self._prefix('geometry', '[config_path]/Trap/')
        
                        
    def _replace_all(self):
        
        xml = self._xml
        for key in self._expression_dict_complex:
            xml = self._replace_complex(key, xml)
            
        for key in self._expression_dict_simple:
            xml = self._replace_simple(key, xml)
            
        return xml

    # -------- public part --------
            
    @property
    def config_dict(self):
        return self._config_dict 
    
    def make_config_file(self, output_path):
        
        xml = self._replace_all()
        _write_xml_file(output_path, xml)
        

class LocustConfig(ABC):
    
    #private class variables to store the json keys
    #if a key changes we can change it here
    _sim_key = 'simulation'
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
    
    _random_seed_key = 'random-seed'
    _noise_floor_psd_key = 'noise-floor-psd'
    _noise_temperature_key = 'noise-temperature'
    
    def __init__(self,
                n_channels = None,
                egg_filename = None,
                record_size = None,
                n_records = None,
                v_range = None,
                random_seed = None,
                noise_floor_psd = None,
                noise_temperature = None):
        
        #locals() hack not possible here since we need a nested dictionary
        self._config_dict = {}
        self._config_dict[self._generators_key] = [self._fft_key, self._decimate_key, self._digit_key]
        self._set(self._sim_key, self._n_channels_key, n_channels)
        self._set(self._sim_key, self._egg_filename_key, egg_filename)
        self._set(self._sim_key, self._record_size_key, record_size)
        self._set(self._sim_key, self._n_records_key, n_records)
        
        self._set(self._digit_key, self._v_range_key, v_range)
        
        self._set(self._noise_key, self._random_seed_key, random_seed)
        self._set(self._noise_key, self._noise_floor_psd_key, noise_floor_psd)
        self._set(self._noise_key, self._noise_temperature_key, noise_temperature)

    # -------- private part --------
    
    def _set(self, key0, key1, value):
        
        if value is not None:
            if not key0 in self._config_dict:
                self._config_dict[key0] = {}
            self._config_dict[key0][key1] = value
            
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
                        str(OUTPUT_DIR_CONTAINER) + '/')
        self._prefix(self._sim_key, self._egg_filename_key, 
                        str(OUTPUT_DIR_CONTAINER) + '/')
    
    # -------- public part --------
    
    @property
    def config_dict(self):
        return self._config_dict
        
    @abstractmethod
    def set_xml(self, path):
        pass
                    
    def make_config_file(self, output_path):
        
        with open(output_path, 'w') as outFile:
            json.dump(self._config_dict, outFile, indent=2)
       
class LocustConfigArraySignal(LocustConfig):
    
    _array_key = 'array-signal'
    
    _lo_frequency_key = 'lo-frequency'
    _nelements_per_strip_key = 'nelements-per-strip'
    _n_subarrays_key = 'n-subarrays'
    _zshift_array_key = 'zshift-array'
    _array_radius_key = 'array-radius'
    _element_spacing_key = 'element-spacing'
    _tf_receiver_bin_width_key = 'tf-receiver-bin-width'
    _tf_receiver_filename_key = 'tf-receiver-filename'
    _xml_filename_key = 'xml-filename'
    
    def __init__(self,
                file_name = HEXBUG_DIR/'Phase3'/LOCUST_CONFIG_NAME_P3,
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
                    
        LocustConfig.__init__(self,
                                n_channels = n_channels,
                                egg_filename = egg_filename,
                                record_size = record_size,
                                n_records = n_records,
                                v_range = v_range,
                                random_seed = random_seed,
                                noise_floor_psd = noise_floor_psd,
                                noise_temperature = noise_temperature)
                    
        self._config_dict[self._generators_key].insert(0,self._array_key)
                    
        self._set(self._array_key, self._lo_frequency_key, lo_frequency)
        self._set(self._array_key, self._nelements_per_strip_key, n_elements_per_strip)
        self._set(self._array_key, self._n_subarrays_key, n_subarrays)
        self._set(self._array_key, self._zshift_array_key, zshift_array)
        self._set(self._array_key, self._array_radius_key, array_radius)
        self._set(self._array_key, self._element_spacing_key, element_spacing)
        self._set(self._array_key, self._tf_receiver_bin_width_key, tf_receiver_bin_width)
        self._set(self._array_key, self._tf_receiver_filename_key, tf_receiver_filename)
        self._set(self._array_key, self._xml_filename_key, xml_filename)
        
        templateConfig = _get_json_from_file(file_name)
        self._finalize(templateConfig)
        
        self._prefix(self._array_key, self._tf_receiver_filename_key, 
                str(HEXBUG_DIR_CONTAINER)+'/Phase3/TransferFunctions/')
    
    def set_xml(self, path):
        name = path.name
        self._set(self._array_key, self._xml_filename_key, 
                    str(OUTPUT_DIR_CONTAINER / name))
                    
class LocustConfigKassSignal(LocustConfig):
    
    _array_key = 'kass-signal'
    
    _lo_frequency_key = 'lo-frequency'
    _center_to_short_key = 'center-to-short'
    _center_to_antenna_key = 'center-to-antenna'
    _pitchangle_filename_key = 'pitchangle-filename'
    _xml_filename_key = 'xml-filename'
    
    _pitchangle_filename = 'pitchangles.txt'
    
    def __init__(self,
                file_name = HEXBUG_DIR/'Phase2'/LOCUST_CONFIG_NAME_P2,
                n_channels = None,
                egg_filename = None,
                record_size = None,
                n_records = None,
                v_range = None,
                lo_frequency = None,
                center_to_short = None,
                center_to_antenna = None,
                xml_filename = None,
                random_seed = None,
                noise_floor_psd = None,
                noise_temperature = None):
                    
        LocustConfig.__init__(self,
                                n_channels = n_channels,
                                egg_filename = egg_filename,
                                record_size = record_size,
                                n_records = n_records,
                                v_range = v_range,
                                random_seed = random_seed,
                                noise_floor_psd = noise_floor_psd,
                                noise_temperature = noise_temperature)
                    
        self._config_dict[self._generators_key].insert(0,self._array_key)
                    
        self._set(self._array_key, self._lo_frequency_key, lo_frequency)
        self._set(self._array_key, self._center_to_short_key, center_to_short)
        self._set(self._array_key, self._center_to_antenna_key, 
                    center_to_antenna)
                    
        self._set(self._array_key, self._pitchangle_filename_key, 
                    str(OUTPUT_DIR_CONTAINER / self._pitchangle_filename))
        self._set(self._array_key, self._xml_filename_key, xml_filename)
        
        templateConfig = _get_json_from_file(file_name)
        self._finalize(templateConfig)
    
    def set_xml(self, path):
        name = path.name
        self._set(self._array_key, self._xml_filename_key, 
                    str(OUTPUT_DIR_CONTAINER / name))

class SimConfig:
    
    def __init__(self,
                sim_name,
                phase = 'Phase3',
                kass_template = None,
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
                energy = None,
                locust_template = 'Phase3/'+LOCUST_CONFIG_NAME_P3,
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
        
        self._sim_name = sim_name
        
        locust_template = HEXBUG_DIR/locust_template
        #kass_template = HEXBUG_DIR/kass_template
        
        # ~ self._locust_config = LocustConfigArraySignal(file_name = locust_template,
                                            # ~ n_channels = n_channels,
                                            # ~ egg_filename = egg_filename,
                                            # ~ record_size = record_size,
                                            # ~ n_records = n_records,
                                            # ~ v_range = v_range,
                                            # ~ lo_frequency = lo_frequency,
                                            # ~ n_elements_per_strip = n_elements_per_strip,
                                            # ~ n_subarrays = n_subarrays,
                                            # ~ zshift_array = zshift_array,
                                            # ~ array_radius = array_radius,
                                            # ~ element_spacing = element_spacing,
                                            # ~ tf_receiver_bin_width = tf_receiver_bin_width,
                                            # ~ tf_receiver_filename = tf_receiver_filename,
                                            # ~ xml_filename = xml_filename,
                                            # ~ random_seed = seed_locust,
                                            # ~ noise_floor_psd = noise_floor_psd,
                                            # ~ noise_temperature = noise_temperature)
                                            
        self._locust_config = LocustConfigKassSignal(file_name = locust_template,
                                            n_channels = n_channels,
                                            egg_filename = egg_filename,
                                            record_size = record_size,
                                            n_records = n_records,
                                            v_range = v_range,
                                            lo_frequency = lo_frequency,
                                            xml_filename = xml_filename,
                                            random_seed = seed_locust,
                                            noise_floor_psd = noise_floor_psd,
                                            noise_temperature = noise_temperature)
                                        
        self._kass_config = KassConfig(file_name = kass_template,
                                        phase = phase,
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
                                        geometry = geometry,
                                        energy = energy)
    
    @property
    def sim_name(self):
        return self._sim_name
    
    def to_json(self, file_name):
        
        with open(file_name, 'w') as outfile:
            json.dump({ 'sim-name': self._sim_name, 
                        'kass-config': self._kass_config, 
                        'locust-config': self._locust_config}, outfile, 
                        indent=2, default=lambda x: x.config_dict)
 
                            
    def to_dict(self):
        
        return {'sim-name': self._sim_name,
                **self._locust_config.config_dict, 
                **self._kass_config.config_dict}
            
    @classmethod
    def from_json(cls, file_name):
        
        instance = cls()
        
        with open(file_name, 'r') as infile:
            config = json.load(infile)
            
            instance._sim_name = config['sim-name']
            #accessing 'private' data members; don't do that at home! ;)
            instance._locust_config._config_dict = config['locust-config']
            instance._kass_config._config_dict = config['kass-config']
            
        return instance
        
    def make_config_file(self, filename_locust, filename_kass):
        self._locust_config.set_xml(filename_kass)
        self._locust_config.make_config_file(filename_locust)
        self._kass_config.make_config_file(filename_kass)

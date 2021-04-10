
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
    
    _expression_dict_constants = { 'output_path': _output_path_expression,
                                   'config_path': _config_path_expression}
    
    # these dictionaries define the accepted parameters
    _expression_dict_simple = {'seed_kass': _seed_expression,
                               't_max': _t_max_expression,
                               'geometry': _geometry_expression,
                               'energy': _energy_expression }
                       
    _expression_dict_complex = {'x_min': _x_val_expression,
                               'y_min': _y_val_expression,
                               'z_min': _z_val_expression,
                               'theta_min': _theta_val_expression }
    
    def __init__(self,
                phase = 'Phase3',
                kass_file_name = None,
                **kwargs):
    
        self._read_config_dict(kwargs)
        
        self._handle_phase(phase, kass_file_name)
        self._handle_seed()
        
        self._xml = _get_xml_from_file(self._file_name)
        self._add_defaults()
        self._adjust_paths()
 
    # -------- private part --------
    
    def _read_config_dict(self, config_dict):
        
        accepted_keys = self.get_accepted_keys()
                
        self._config_dict = {k:config_dict[k] 
                            for k 
                            in set(config_dict).intersection(accepted_keys)}
    
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
        if 'seed_kass' not in self._config_dict:
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
            #if self._config_dict[key] is None:
            if key not in self._config_dict:
                self._config_dict[key] =(
                    self._get_val(self._expression_dict_simple[key], self._xml) )
                
    def _add_complex_defaults(self):
        
        for key in self._expression_dict_complex:
            #if self._config_dict[key] is None:
            if key not in self._config_dict:
                minVal, maxVal =( 
                    self._get_min_max_val(self._expression_dict_complex[key], self._xml))
                self._config_dict[key] = minVal
                self._config_dict[key[:-3]+'max'] = maxVal
     
    def _replace_simple_val(self, expression, value, string):
        
        return re.sub( expression + self._match_all_regex.pattern,
                       expression +'"'+str(value)+'"', string)
                       
    def _replace_complex_val(self, expression, val_min, val_max, string):
        
        return re.sub( ( expression 
                        + self._match_all_regex.pattern
                        + self._val_max_expression
                        + self._match_all_regex.pattern),
                        ( expression
                        + '"'+str(val_min)+'"'
                        + self._val_max_expression
                        + '"'+str(val_max)+'"'), string)
    
    def _replace_simple(self, key, string):
        
        expression = self._expression_dict_simple[key]
        val = self._config_dict[key]
        
        return self._replace_simple_val(expression, val, string)
        
    def _replace_complex(self, key, string):
        
        expression = self._expression_dict_complex[key]
        val_min = self._config_dict[key]
        val_max = self._config_dict[key[:-3]+'max']
        
        return self._replace_complex_val(expression, val_min, val_max, string)
        
    def _prefix(self, key, value):
        
        self._config_dict[key] = value + self._config_dict[key].split('/')[-1]
                                
    def _adjust_paths(self):
        
        self._prefix('geometry', '[config_path]/Trap/')
        
    def _replace_constants(self, string):
        
        string = self._replace_simple_val(
                                self._expression_dict_constants['output_path'], 
                                str(OUTPUT_DIR_CONTAINER), string)
        string = self._replace_simple_val(
                                self._expression_dict_constants['config_path'], 
                                str(self._config_path), string)
                                
        return string
                        
    def _replace_all(self):
        
        xml = self._xml
        
        for key in self._expression_dict_complex:
            xml = self._replace_complex(key, xml)
            
        for key in self._expression_dict_simple:
            xml = self._replace_simple(key, xml)
            
        xml = self._replace_constants(xml)
            
        return xml

    # -------- public part --------
            
    @property
    def config_dict(self):
        return self._config_dict 
        
    @classmethod
    def get_accepted_keys(cls):
        
        keys = list(cls._expression_dict_simple.keys())
        keys = keys + list(cls._expression_dict_complex.keys())
        
        for key in cls._expression_dict_complex:
            keys.append(key[:-3]+'max')
            
        return keys
    
    def make_config_file(self, output_path):
        
        xml = self._replace_all()
        _write_xml_file(output_path, xml)
   
def _set_dict_2d(key_dict, key_to_var_dict, arg_dict):
    
    output = {}
    for key in key_dict:
        output[key] = {}
        for sub_key in key_dict[key]:
            var = key_to_var_dict.get(sub_key)
            val = arg_dict.get(var)
            if val:
                output[key][sub_key] = val
                
    return output

class LocustConfig:
    
    #private class variables to store the json keys
    #if a key changes we can change it here
    
    #all phases
    
    #first level keys
    _sim_key = 'simulation'
    _digit_key = 'digitizer'
    _noise_key = 'gaussian-noise'
    _generators_key = 'generators'
    _fft_key = 'lpf-fft'
    _decimate_key = 'decimate-signal'
    
    
    # simulation sub keys
    _egg_filename_key = 'egg-filename'
    _record_size_key = 'record-size'
    _n_records_key = 'n-records'
    
    # digitizer sub keys
    _v_range_key = 'v-range'
    _v_offset_key = 'v-offset'
    
    # gaussian noise subkeys
    _random_seed_key = 'random-seed'
    _noise_floor_psd_key = 'noise-floor-psd'
    _noise_temperature_key = 'noise-temperature'
    
    # phase2 = kass-signal subkeys/ phase3 = array-signal subkeys
    _xml_filename_key = 'xml-filename'
    _lo_frequency_key = 'lo-frequency'
    
    #phase 3 specific
    _array_signal_key = 'array-signal' #first level key
    
    # array-signal subkeys
    _nelements_per_strip_key = 'nelements-per-strip'
    _n_subarrays_key = 'n-subarrays'
    _zshift_array_key = 'zshift-array'
    _array_radius_key = 'array-radius'
    _element_spacing_key = 'element-spacing'
    _tf_receiver_bin_width_key = 'tf-receiver-bin-width'
    _tf_receiver_filename_key = 'tf-receiver-filename'
    _n_channels_key = 'n-channels'
    
    #phase 2 specific
    _kass_signal_key = 'kass-signal' #first level key
    
    # kass-signal subkeys
    _center_to_short_key = 'center-to-short'
    _center_to_antenna_key = 'center-to-antenna'
    _pitchangle_filename_key = 'pitchangle-filename'
    _pitchangle_filename = 'pitchangles.txt'
    
    _key_dict = {   _generators_key: [],
                    _sim_key: [ _egg_filename_key,
                                _record_size_key,
                                _n_records_key ],
                    _digit_key: [_v_range_key, 
                                 _v_offset_key],
                    _noise_key: [_random_seed_key,
                                 _noise_floor_psd_key,
                                 _noise_temperature_key],
                    _fft_key: [],
                    _decimate_key: [],
                    _array_signal_key: [_xml_filename_key,
                                        _lo_frequency_key,
                                        _nelements_per_strip_key,
                                        _n_subarrays_key,
                                        _zshift_array_key,
                                        _array_radius_key,
                                        _element_spacing_key,
                                        _tf_receiver_bin_width_key,
                                        _tf_receiver_filename_key,
                                        _n_channels_key],
                    _kass_signal_key: [_xml_filename_key,
                                            _lo_frequency_key,
                                            _center_to_short_key,
                                            _center_to_antenna_key,
                                            _pitchangle_filename_key]
                                            }
    
    #this defines the accepted parameters
    _key_to_var_dict = {_n_channels_key : 'n_channels',
                        _egg_filename_key: 'egg_filename',
                        _record_size_key: 'record_size',
                        _n_records_key: 'n_records',
                        _v_range_key: 'v_range',
                        _lo_frequency_key: 'lo_frequency',
                        _nelements_per_strip_key: 'n_elements_per_strip',
                        _n_subarrays_key: 'n_subarrays',
                        _zshift_array_key: 'zshift_array',
                        _array_radius_key: 'array_radius',
                        _element_spacing_key: 'element_spacing',
                        _tf_receiver_bin_width_key: 'tf_receiver_bin_width',
                        _tf_receiver_filename_key: 'tf_receiver_filename',
                        _random_seed_key: 'seed_locust',
                        _noise_floor_psd_key: 'noise_floor_psd',
                        _noise_temperature_key: 'noise_temperature',
                        _center_to_short_key: 'center_to_short',
                        _center_to_antenna_key: 'center_to_antenna'}
    
    def __init__(self,                
                phase = 'Phase3',
                locust_file_name = None,
                **kwargs):

        self._config_dict = _set_dict_2d(self._key_dict, self._key_to_var_dict, 
                                            kwargs)
                                            
        self._handle_phase(phase, locust_file_name)
        templateConfig = _get_json_from_file(self._file_name)
        
        self._config_dict[self._generators_key] = [self._signal_key,
                                                    self._fft_key, 
                                                    self._decimate_key, 
                                                    self._digit_key]
        
        self._finalize(templateConfig)

    # -------- private part --------
    
    def _handle_phase(self, phase, file_name):
    
        allowed = phase=='Phase2' or phase =='Phase3'
        
        if allowed:
            
            self._config_path = HEXBUG_DIR_CONTAINER/phase
            
            if file_name is None:
                file_name = (LOCUST_CONFIG_NAME_P3 if phase=='Phase3' else
                                LOCUST_CONFIG_NAME_P2)
            
            self._file_name = HEXBUG_DIR/phase/file_name
            
            self._signal_key = (self._array_signal_key if phase=='Phase3' else 
                                    self._kass_signal_key)
            
            if phase=='Phase2':
                self._set(self._signal_key, self._pitchangle_filename_key, 
                        str(OUTPUT_DIR_CONTAINER / self._pitchangle_filename))
        else:
            raise ValueError('Only "Phase2" or "Phase3" are supported')

    
    def _set(self, key0, key1, value):
        
        if value is not None:
            if not key0 in self._config_dict:
                self._config_dict[key0] = {}
            self._config_dict[key0][key1] = value
            
    def _prefix(self, key0, key1, value):
        
        sub_dict = self._config_dict.get(key0)
        
        if sub_dict:
            orig = sub_dict.get(key1)
            
            if orig:
                self._config_dict[key0][key1] = value + orig.split('/')[-1]
        
            
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
        
        self._prefix(self._sim_key, self._egg_filename_key, 
                        str(OUTPUT_DIR_CONTAINER) + '/')
                        
        self._prefix(self._signal_key, self._tf_receiver_filename_key, 
                    str(self._config_path/'TransferFunctions')+'/')
    
    # -------- public part --------
    
    @property
    def config_dict(self):
        return self._config_dict
        
    def set_xml(self, path):
        name = path.name
        self._set(self._signal_key, self._xml_filename_key, 
                    str(OUTPUT_DIR_CONTAINER / name))
    
    @classmethod
    def get_accepted_keys(cls):
            
        return list(cls._key_to_var_dict.values())
                    
    def make_config_file(self, output_path):
        
        with open(output_path, 'w') as outFile:
            json.dump(self._config_dict, outFile, indent=2)

    
def _get_unknown_parameters(kwargs):
    
    accepted_parameters = ( KassConfig.get_accepted_keys() 
                            + LocustConfig.get_accepted_keys() )
                            
    return set(kwargs.keys()).difference(accepted_parameters)
    
def trigger_unknown_parameter_warnings(kwargs):
    
    unknown_parameters = _get_unknown_parameters(kwargs)
    
    for parameter in unknown_parameters:
        print('WARNING - unknown parameter "{}" is ignored'.format(parameter))

class SimConfig:
    
    def __init__(self, sim_name, phase = 'Phase3', kass_file_name = None, 
                    locust_file_name = None, **kwargs):
                        
        trigger_unknown_parameter_warnings(kwargs)
        
        self._sim_name = sim_name
        self._phase = phase
        
        self._locust_config = LocustConfig(phase = phase, 
                                           locust_file_name = locust_file_name, 
                                           **kwargs)
                                        
        self._kass_config = KassConfig( phase = phase, 
                                        kass_file_name = kass_file_name, 
                                        **kwargs)
    
    @property
    def sim_name(self):
        return self._sim_name
    
    def to_json(self, file_name):
        
        with open(file_name, 'w') as outfile:
            json.dump({ 'sim-name': self._sim_name,
                        'phase' : self._phase,
                        'kass-config': self._kass_config, 
                        'locust-config': self._locust_config}, outfile, 
                        indent=2, default=lambda x: x.config_dict)
 
                            
    def to_dict(self):
        
        return {'sim-name': self._sim_name,
                'phase': self._phase,
                **self._locust_config.config_dict, 
                **self._kass_config.config_dict}
            
    @classmethod
    def from_json(cls, file_name):
        
        with open(file_name, 'r') as infile:
            config = json.load(infile)
            
            sim_name = config['sim-name']
            phase = config['phase']
            
            instance = cls(sim_name, phase=phase)
            
            instance._locust_config._config_dict = config['locust-config']
            instance._kass_config._config_dict = config['kass-config']
            
        return instance
        
    def make_config_file(self, filename_locust, filename_kass):
        self._locust_config.set_xml(filename_kass)
        self._locust_config.make_config_file(filename_locust)
        self._kass_config.make_config_file(filename_kass)

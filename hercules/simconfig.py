
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
    
    # Return a seed based on the current time.
    # 
    # Returns
    # -------
    # int
    #     The random seed
    
    t = int( time.time() * 1000.0 )
    seed = ((t & 0xff000000) >> 24) +\
             ((t & 0x00ff0000) >>  8) +\
             ((t & 0x0000ff00) <<  8) +\
             ((t & 0x000000ff) << 24)
             
    return seed
 
def _get_json_from_file(locust_file):
    
    # Return the json dictionary from a path to a json file.
    # 
    # Parameters
    # ----------
    # locust_file : str 
    #     The path to the json file
    # 
    # Returns
    # -------
    # dict
    #     The dictionary with the contents of the json file
    
    with open(locust_file, 'r') as read_file:
        return json.load(read_file)
        
def _get_xml_from_file(xml_file):
    
    # Return the contents of an xml file.
    # 
    # Parameters
    # ----------
    # xml_file : str 
    #     The path to the xml file
    # 
    # Returns
    # -------
    # str
    #     The string content of the xml file
    
    with open(xml_file) as conf:
        return conf.read()

def _write_xml_file(output_path, xml):
    
    # Write an xml file.
    # 
    # Parameters
    # ----------
    # output_path : str 
    #     The path to xml file which is to be created
    # xml : str
    #     The content for the xml file
    
    with open(output_path, 'w') as new_conf:
        new_conf.write(xml) 
    
class KassConfig:
    
    """A class for creating a configuration file for Kassiopeia.
    
    Attributes
    ----------
    config_dict : dict
        A dictionary with all configuration parameters
    """
    
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
        """
        Parameters
        ----------
        phase : str
            Should be either 'Phase2' or 'Phase3' and determines if
            phase 2 or phase 3 simulation is run (default 'Phase3')
        kass_file_name : str, optional
            The name for the Kassiopeia configuration file that should
            be used. This means only the file name, not the full path!
            The file has to be placed in hercules/hexbug/PHASE/, where
            PHASE is the value of the other parameter. If no file name given
            a default file specific to the phase will be used (recommended).
        **kwargs :
            Arbitrary number of keyword arguments.
                    
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """
    
        # pass the arbitrary number of keyword arguments as a dict to the read
        # method
        self._read_config_dict(kwargs)
        
        self._handle_phase(phase, kass_file_name)
        self._handle_seed()
        
        self._xml = _get_xml_from_file(self._file_name)
        self._add_defaults()
        self._adjust_paths()
 
    # -------- private part --------
    
    def _read_config_dict(self, config_dict):
        # Read a config dict into the internal config dict
        #
        # The dictionary that is passed here will come from the **kwargs of the
        # __init__ method, i.e. it will bring in an arbitrary number of keyword
        # arguments. To prevent filling the internal dictionary with anything
        # this method adds only the accepted keys.
        
        accepted_keys = self.get_accepted_keys()
        
        #internal config dictionary
        self._config_dict = {k:config_dict[k] 
                            for k 
                            in set(config_dict).intersection(accepted_keys)}
    
    def _handle_phase(self, phase, file_name):
        # Read the phase parameter and take appropriate actions according input
        # 
        # Sets the path to the hexbug dir and the template configuration file
        # according to the chosen phase.
        # 
        # Parameters
        # see __init__
        # 
        # Raises
        # ------
        # ValueError
        #     If phase is not 'Phase2' or 'Phase3'
    
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
        # not used any more
        self._config_dict.pop('self', None)
        self._config_dict.pop('file_name', None)
        self._config_dict.pop('phase', None)
        
    def _handle_seed(self):
        # Function to add a seed to the configuration if it was not set manually
        
        if 'seed_kass' not in self._config_dict:
            self._config_dict['seed_kass'] = _get_rand_seed()
    
    def _add_defaults(self):
        # Add both types of default parameters to the internal configuration
        
        self._add_complex_defaults()
        self._add_simple_defaults()
                        
    def _get_min_max_val(self, expression, string):
        # Extract a min and a max value from a string expression
        #
        # The function is used to extract the default values 
        # for variables that describe a range in the kassiopeia config.
        # The expression in the config files looks like this 
        # <x_uniform value_min=a value_max=b>.
        #
        # Parameters
        # ----------
        # expression : str
        #       A string like "<x_uniform value_min=" used to match the whole
        #       expression above
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # min_val
        #       the minimum value it found
        # max_val
        #       the maximum value it found
        
        regex = expression+self._match_all_regex.pattern\
            +self._val_max_expression+self._match_all_regex.pattern
        result = re.findall(regex, string)
        min_val = result[0][0]
        max_val = result[0][1]
        
        return min_val, max_val
        
    def _get_val(self, expression, string):
        # Extract a value from a string expression
        #
        # The function is used to extract the default values 
        # for simple variables in the kassiopeia config.
        # The expression in the config files looks like this 
        # '<external_define name="seed" value=X>'
        #
        # Parameters
        # ----------
        # expression : str
        #       A string like "<external_define name="seed" value=" used to 
        #       match the whole expression above
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # val
        #       the value it found
        
        regex = expression+self._match_all_regex.pattern
        result = re.findall(regex, string)
        val = result[0]
        
        return val
        
    def _add_simple_defaults(self):
        # Add default values to the internal config dict
        #
        # The default values are taken from the template config file.
        # This function only takes care of the simple single value parameters.
        
        for key in self._expression_dict_simple:
            #if self._config_dict[key] is None:
            if key not in self._config_dict:
                self._config_dict[key] =(
                    self._get_val(self._expression_dict_simple[key], self._xml) )
                
    def _add_complex_defaults(self):
        # Add default values to the internal config dict
        #
        # The default values are taken from the template config file.
        # This function only takes care of the parameters given in a range.
        
        for key in self._expression_dict_complex:
            #if self._config_dict[key] is None:
            if key not in self._config_dict:
                minVal, maxVal =( 
                    self._get_min_max_val(self._expression_dict_complex[key], self._xml))
                self._config_dict[key] = minVal
                self._config_dict[key[:-3]+'max'] = maxVal
     
    def _replace_simple_val(self, expression, value, string):
        # Replace a value in a Kassiopeia config
        #
        # The function is used to replace the default values 
        # for simple variables in the Kassiopeia config.
        # The expression in the config files looks like this 
        # '<external_define name="seed" value=X>'
        #
        # Parameters
        # ----------
        # expression : str
        #       A string like "<external_define name="seed" value=" used to 
        #       match the whole expression above
        # value: 
        #       The value to insert
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # str
        #       the string with the replaced value
        
        return re.sub( expression + self._match_all_regex.pattern,
                       expression +'"'+str(value)+'"', string)
                       
    def _replace_complex_val(self, expression, val_min, val_max, string):
        # Replace a min and a max value in a Kassiopeia config
        #
        # The function is used to replace the default values 
        # for variables that describe a range in the Kassiopeia config.
        # The expression in the config files looks like this 
        # <x_uniform value_min=a value_max=b>.
        #
        # Parameters
        # ----------
        # expression : str
        #       A string like "<x_uniform value_min=" used to match the whole
        #       expression above
        # val_min: 
        #       The minimum value to insert
        # val_max:
        #       The maximum value to insert
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # str
        #       the string with the replaced values
        
        return re.sub( ( expression 
                        + self._match_all_regex.pattern
                        + self._val_max_expression
                        + self._match_all_regex.pattern),
                        ( expression
                        + '"'+str(val_min)+'"'
                        + self._val_max_expression
                        + '"'+str(val_max)+'"'), string)
    
    def _replace_simple(self, key, string):
        # Replace a value in a Kassiopeia config
        #
        # The function is used to replace the default values 
        # for simple variables in the Kassiopeia config.
        # Value and expression are taken from the internal config and 
        # expression dictionaries via the key that is passed.
        #
        # Parameters
        # ----------
        # key : str
        #       A key of the internal dictionaries
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # str
        #       the string with the replaced value
    
        expression = self._expression_dict_simple[key]
        val = self._config_dict[key]
        
        return self._replace_simple_val(expression, val, string)
        
    def _replace_complex(self, key, string):
        # Replace a min and a max value in a Kassiopeia config
        #
        # The function is used to replace the default values 
        # for variables that describe a range in the Kassiopeia config.
        # Values and expression are taken from the internal config and 
        # expression dictionaries via the key that is passed.
        #
        # Parameters
        # ----------
        # key : str
        #       A key of the internal dictionaries
        # string : str
        #       the content of the xml file as a string
        #
        # Returns
        # -------
        # str
        #       the string with the replaced value
        
        expression = self._expression_dict_complex[key]
        val_min = self._config_dict[key]
        val_max = self._config_dict[key[:-3]+'max']
        
        return self._replace_complex_val(expression, val_min, val_max, string)
        
    def _prefix(self, key, value):
        # Add a string to the value of a string entry in the internal config
        
        self._config_dict[key] = value + self._config_dict[key].split('/')[-1]
                                
    def _adjust_paths(self):
        # Correct the paths in the internal config where necessary
        
        self._prefix('geometry', '[config_path]/Trap/')
        
    def _replace_constants(self, string):
        # Replace parts of a Kassiopeia config that are not part of the 
        # internal config dictionary since they are the same for any configuration
        
        string = self._replace_simple_val(
                                self._expression_dict_constants['output_path'], 
                                str(OUTPUT_DIR_CONTAINER), string)
        string = self._replace_simple_val(
                                self._expression_dict_constants['config_path'], 
                                str(self._config_path), string)
                                
        return string
                        
    def _replace_all(self):
        # Replace all parts of a Kassiopeia config
        
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
        """Return a list of keys that are accepted by the internal config dict.
        
        Returns
        -------
        list
            list of the accepted keys
        """
        
        keys = list(cls._expression_dict_simple.keys())
        keys = keys + list(cls._expression_dict_complex.keys())
        
        for key in cls._expression_dict_complex:
            keys.append(key[:-3]+'max')
            
        return keys
    
    def make_config_file(self, output_path):
        """Create a final Kassiopeia config file from the internal config.
        
        Parameters
        ----------
        output_path : str
            the path to output config file
        """
        xml = self._replace_all()
        _write_xml_file(output_path, xml)
   
def _set_dict_2d(key_dict, key_to_var_dict, arg_dict):
    # Creates a nested dictionary for the Locust config
    #
    # The function is used to create a nested dictionary in the correct
    # structure of the Locust config files from a simple dictionary that is
    # passed in the form of arbitrary many keyword arguments.
    #
    # Parameters
    # ----------
    # key_dict : dict
    #       Dictionary with lists of keys as values. The keys of the dictionary
    #       itself are the first level Locust keys. Their values are lists
    #       with the corresponding second level keys.
    # key_to_var_dict : dict
    #       Dictionary that maps Locust keys to variable names. Necessary
    #       since Locust keys use dashes, which are not allowed in python
    #       variable names.
    # arg_dict : dict
    #       Dictionary that maps the python variables to their values. This
    #       dictionary will be taken from the **kwargs in the Locust __init__
    #       that enables arbitrary keyword arguments
    #
    # Returns
    # -------
    # dict
    #       the final nested dictionary
    
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
    """A class for creating a configuration file for Locust.
    
    Attributes
    ----------
    config_dict : dict
        A dictionary with all configuration parameters
    """
    
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
        """
        Parameters
        ----------
        phase : str
            Should be either 'Phase2' or 'Phase3' and determines if
            phase 2 or phase 3 simulation is run (default 'Phase3')
        locust_file_name : str, optional
            The name for the Locust configuration file that should
            be used. This means only the file name, not the full path!
            The file has to be placed in hercules/hexbug/PHASE/, where
            PHASE is the value of the other parameter. If no file name given
            a default file specific to the phase will be used (recommended).
        
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """

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
        # Read the phase parameter and take appropriate actions according input
        # 
        # Sets the path to the hexbug dir and the template configuration file
        # according to the chosen phase and adjusts keys that are used for the
        # config dict.
        # 
        # Parameters
        # see __init__
        # 
        # Raises
        # ------
        # ValueError
        #     If phase is not 'Phase2' or 'Phase3'
    
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
        # Set a value in the nested internal config dictionary by its two keys
        
        if value is not None:
            if not key0 in self._config_dict:
                self._config_dict[key0] = {}
            self._config_dict[key0][key1] = value
            
    def _prefix(self, key0, key1, value):
        # Add a string to the value of a string entry in the internal config
        
        sub_dict = self._config_dict.get(key0)
        
        if sub_dict:
            orig = sub_dict.get(key1)
            
            if orig:
                self._config_dict[key0][key1] = value + orig.split('/')[-1]
        
            
    def _finalize(self, template_config):
        # Finalize the configuration after everything else is done.
        # 
        # Actually the most part is done here. It add the defaults from the 
        # template file, it reacts to the inputs that are noise related etc...
        
        self._add_defaults(template_config)
        self._handle_noise()
        self._set(self._digit_key, self._v_offset_key, 
                    -self._config_dict[self._digit_key][self._v_range_key]/2)
        self._adjust_paths()
        
    def _add_defaults(self, template_config):
        # Read in all default values from the template config file
        #
        # This is done by looping through the nested dictionary structure of
        # the template file and filling in keys that are missing in the internal
        # dict.
                    
        for key in template_config:
            #get value from config template if it was not set
            if key not in self._config_dict:
                self._config_dict[key] = template_config[key]
            else:
                for sub_key in template_config[key]:
                    if sub_key not in self._config_dict[key]:
                        self._config_dict[key][sub_key] = template_config[key][sub_key]
                       
    def _handle_noise(self):
        # React to the noise related inputs
        #
        # It is possible to add optional noise to the Locust simulation. This
        # function makes sure this only happens if one of the noise keywords
        # is present in the internal configuration or the template file.
        # Furthermore it adds a seed for the noise if that is missing and it
        # makes sure that only one of the two possible noise keywords goes into
        # the final config file. 
        
        if self._noise_key in self._config_dict:

            if (self._noise_floor_psd_key or self.__sNoiseTemp) in self._config_dict[self._noise_key]:
                self._config_dict[self._generators_key].insert(-1, self._noise_key)

            if (self._noise_floor_psd_key and self._noise_temperature_key) in self._config_dict[self._noise_key]:
                #prefer noise temperature over noise psd
                self._config_dict[self._noise_key].pop(self._noise_floor_psd_key)

            if self._random_seed_key not in self._config_dict[self._noise_key]:
                self._set(self._noise_key, self._random_seed_key, _get_rand_seed())
                
    def _adjust_paths(self):
        # Correct the paths in the internal config where necessary
        
        self._prefix(self._sim_key, self._egg_filename_key, 
                        str(OUTPUT_DIR_CONTAINER) + '/')
                        
        self._prefix(self._signal_key, self._tf_receiver_filename_key, 
                    str(self._config_path/'TransferFunctions')+'/')
    
    # -------- public part --------
    
    @property
    def config_dict(self):
        return self._config_dict
        
    def set_xml(self, path):
        """Set the Kassiopeia xml config file path in the internal config.
        
        It is necessary to enable setting the path from outside the class
        since the name has to match exactly the name that is used for the 
        Kassiopeia config.
        
        Parameters
        ----------
        path : Path
            the path to the Kassiopeia config file
        """
        name = path.name
        self._set(self._signal_key, self._xml_filename_key, 
                    str(OUTPUT_DIR_CONTAINER / name))
    
    @classmethod
    def get_accepted_keys(cls):
        """Return a list of keys that are accepted for the internal config dict.
        
        Returns
        -------
        list
            list of the accepted keys
        """
            
        return list(cls._key_to_var_dict.values())
                    
    def make_config_file(self, output_path):
        """Create a final Locust config file from the internal config.
        
        Parameters
        ----------
        output_path : str
            the path to output config file
        """
        
        with open(output_path, 'w') as outFile:
            json.dump(self._config_dict, outFile, indent=2)

    
def _get_unknown_parameters(kwargs):
    # Return a set with unknown parameters
    #
    # Gets the list of accepted keys of the KassConfig and the LocustConfig.
    # The set is created from any keys in the input that is not part of any of
    # the two.
    #
    # Parameters
    # ----------
    # kwargs : dict
    #       dictionary of keyword arguments
    
    accepted_parameters = ( KassConfig.get_accepted_keys() 
                            + LocustConfig.get_accepted_keys() )
                            
    return set(kwargs.keys()).difference(accepted_parameters)
    
def trigger_unknown_parameter_warnings(kwargs):
    # Print warnings for keyword arguments that are unknown to KassConfig/LocustConfig
    #
    # Useful addition since it is possible to enter an arbitrary number of
    # keyword arguments in the SimConfig. Not strictly necessary but helps
    # to prevent frustration due to typos.
    
    unknown_parameters = _get_unknown_parameters(kwargs)
    
    for parameter in unknown_parameters:
        print('WARNING - unknown parameter "{}" is ignored'.format(parameter))

class SimConfig:
    """A class for the entire simulation configuration.
    
    This class wraps the KassConfig and the LocustConfig. It is recommended that
    end users use this class since it removes another layer of complication.
    
    Attributes
    ----------
    sim_name : str
        Name of the simulation
    """
    
    def __init__(self, sim_name, phase = 'Phase3', kass_file_name = None, 
                    locust_file_name = None, **kwargs):
        """
        Parameters
        ----------
        sim_name : str
            Name of the simulation
        phase : str
            Should be either 'Phase2' or 'Phase3' and determines if
            phase 2 or phase 3 simulation is run (default 'Phase3')
        kass_file_name : str, optional
            The name for the Kassiopeia configuration file that should
            be used. This means only the file name, not the full path!
            The file has to be placed in hercules/hexbug/PHASE/, where
            PHASE is the value of the other parameter. If no file name given
            a default file specific to the phase will be used (recommended).
        locust_file_name : str, optional
            The name for the Locust configuration file that should
            be used. This means only the file name, not the full path!
            The file has to be placed in hercules/hexbug/PHASE/, where
            PHASE is the value of the other parameter. If no file name given
            a default file specific to the phase will be used (recommended).
        **kwargs :
            Arbitrary number of keyword arguments.
        
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """
                        
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
        """Write a json file with the entire simulation configuration."""
        
        with open(file_name, 'w') as outfile:
            json.dump({ 'sim-name': self._sim_name,
                        'phase' : self._phase,
                        'kass-config': self._kass_config, 
                        'locust-config': self._locust_config}, outfile, 
                        indent=2, default=lambda x: x.config_dict)
 
                            
    def to_dict(self):
        """Return a dictionary with the entire simulation configuration.
        
        Returns
        -------
        dict
            Nested dictionary with the simulation configuration
        """
        
        return {'sim-name': self._sim_name,
                'phase': self._phase,
                **self._locust_config.config_dict, 
                **self._kass_config.config_dict}
            
    @classmethod
    def from_json(cls, file_name):
        """Return a SimConfig from a json file.
        
        Creates a new instance of a SimConfig from the contents of a json file.
        This should only be used with a json file that was created by the 
        `to_json` method. No checks applied for the validity of the json file.
        
        Returns
        -------
        SimConfig
            The new SimConfig instance
        """
        
        with open(file_name, 'r') as infile:
            config = json.load(infile)
            
            sim_name = config['sim-name']
            phase = config['phase']
            
            instance = cls(sim_name, phase=phase)
            
            instance._locust_config._config_dict = config['locust-config']
            instance._kass_config._config_dict = config['kass-config']
            
        return instance
        
    def make_config_file(self, filename_locust, filename_kass):
        """Create the final Kassiopeia and Locust config files.
        
        Parameters
        ----------
        filename_locust : str
            the path to the output Locust config file
        filename_kass : str
            the path to the output Kassiopeia config file
        """
        
        self._locust_config.set_xml(filename_kass)
        self._locust_config.make_config_file(filename_locust)
        self._kass_config.make_config_file(filename_kass)

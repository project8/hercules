
"""

Author: F. Thomas
Date: March 10, 2021

"""

__all__ = ['SimConfig']

import time
import json
import re
from copy import deepcopy
from math import sqrt, atan2
from pathlib import Path

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
    
    # these dictionaries define the accepted parameters and should also contain some documentation
    _expression_dict_simple = {'seed_kass': [_seed_expression,
                                            'int -- The seed used for Kassiopeia generators'],
                               't_max': [_t_max_expression,
                                            'float -- The maximum time length of the electron trjactory'],
                               'geometry': [_geometry_expression,
                                            'str -- The file name for the trap geometry. The file has to be placed in hercules/hexbug/PHASE/Trap'],
                               'energy': [_energy_expression,
                                            'float -- Initial electron kinetic energy']}
                       
    _expression_dict_complex = {'x_min': [_x_val_expression,
                                            'float -- Paired with x_max. Bounds for uniform generator of initial electron x position. For full control use one value for both'],
                               'y_min': [_y_val_expression,
                                            'float -- Paired with y_max. Bounds for uniform generator of initial electron y position. For full control use one value for both'],
                               'z_min': [_z_val_expression,
                                            'float -- Paired with z_max. Bounds for uniform generator of initial electron z position. For full control use one value for both'],
                               'theta_min': [_theta_val_expression,
                                            'float -- Paired with y_max. Bounds for uniform generator of initial electron y position. For full control use one value for both'] }
    
    def __init__(self,
                phase = 'Phase3',
                kass_file_name = None,
                unknown_args_translation = {},
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
        unknown_args_translation: dict, optional
            Dictionary to expand the internal translation from parameter names
            to configuration file expressions. This is used to make hercules 
            understand parameters that are internally still unknown to it. For
            example when you want to modify the magnetic field in x direction 
            you can call __init__ with a keyword 'b_x' (via **kwargs).
            In the config file this corresponds to the line 
            '<external_define name="fieldX" value="0.0"/>'.
            Therefore to tell hercules what to do with 'b_x' you use
            unknown_args_translation={'b_x': '<external_define name="fieldX" value='}. 
        **kwargs :
            Arbitrary number of keyword arguments.
                    
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """
        
        self._add_unknown_args_translation(unknown_args_translation)
            
        # pass the arbitrary number of keyword arguments as a dict to the read
        # method
        self._read_config_dict(kwargs)
        
        self._handle_phase(phase, kass_file_name)
        self._handle_seed()
        
        self._xml = _get_xml_from_file(self._file_name)
        self._add_defaults()
        self._adjust_paths()
 
    # -------- private part --------
    
    def _add_unknown_args_translation(self, unknown_args_translation):
        # Add the translation of unknown arguments to _expression_dict_simple
        self._expression_dict_simple = self._expression_dict_simple.copy()#prevent overriding the class level dict
        for key in unknown_args_translation:
            self._expression_dict_simple[key] = [unknown_args_translation[key], '']
        
        
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
        
    # def _clean_initial_config(self):
    #     # remove 'self' and 'file_name' from the dictionary
    #     # not used any more
    #     self._config_dict.pop('self', None)
    #     self._config_dict.pop('file_name', None)
    #     self._config_dict.pop('phase', None)
        
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
                val = self._get_val(self._expression_dict_simple[key][0], self._xml)
                try:
                    val_f = float(val)
                except ValueError:
                    val_f = val
                self._config_dict[key] = val_f
                
    def _add_complex_defaults(self):
        # Add default values to the internal config dict
        #
        # The default values are taken from the template config file.
        # This function only takes care of the parameters given in a range.
        
        for key in self._expression_dict_complex:
            #if self._config_dict[key] is None:
            if key not in self._config_dict:
                minVal, maxVal =( 
                    self._get_min_max_val(self._expression_dict_complex[key][0], self._xml))
                self._config_dict[key] = float(minVal)
                self._config_dict[key[:-3]+'max'] = float(maxVal)
     
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
    
        expression = self._expression_dict_simple[key][0]
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
        
        expression = self._expression_dict_complex[key][0]
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
        

    def get_accepted_keys(self):
        """Return a list of keys that are accepted by the internal config dict.
        
        Returns
        -------
        list
            list of the accepted keys
        """
        
        keys = list(self._expression_dict_simple.keys())
        keys = keys + list(self._expression_dict_complex.keys())
        
        for key in self._expression_dict_complex:
            keys.append(key[:-3]+'max')
            
        return keys
        
    
    @classmethod
    def print_keyword_documentation(cls):
        """Print the documentation of accepted keywords as provided by the expression dicts."""
        
        for key in cls._expression_dict_simple:
            entry = cls._expression_dict_simple[key]
            print(key.ljust(25) + entry[1])
            
        for key in cls._expression_dict_complex:
            entry = cls._expression_dict_complex[key]
            print(key.ljust(25) + entry[1])
            print((key[:-3]+'max').ljust(25) + 'See above')
    
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
            if var:
                val = arg_dict.get(var[0])
                if val is not None:
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
    _acq_rate_key = 'acquisition-rate'
    _n_channels_key = 'n-channels'
    
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
    _event_spacing_samples_key = 'event-spacing-samples'
    
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
                                _n_records_key,
                                _acq_rate_key,
                                _n_channels_key],
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
                                        _event_spacing_samples_key],
                    _kass_signal_key: [_xml_filename_key,
                                            _lo_frequency_key,
                                            _center_to_short_key,
                                            _center_to_antenna_key,
                                            _pitchangle_filename_key]
                                            }
    
    #this defines the accepted parameters and should also include a short documentation for each
    _key_to_var_dict = {_n_channels_key: ['n_channels',
                                            'int -- The number of simulated channels'],
                                            
                        _egg_filename_key: ['egg_filename',
                                            'str -- Name of the output egg file'],
                                            
                        _record_size_key: ['record_size',
                                            'int -- Number of simulated samples in a record'],
                                            
                        _n_records_key: ['n_records',
                                            'int -- Number of simulated records'],

                        _acq_rate_key: ['acq_rate',
                                            'float -- Acquisition rate of the digitizer in MHz'],
                                            
                        _v_range_key: ['v_range',
                                            'float -- Voltage range of the digitizer in V'],
                                            
                        _lo_frequency_key: ['lo_frequency',
                                            'float -- Frequency of the local oscillator in Hz'],
                                            
                        _nelements_per_strip_key: ['n_elements_per_strip',
                                            'int -- Number of waveguide slots'],
                                            
                        _n_subarrays_key: ['n_subarrays',
                                            'int -- Number of simulated antenna rings'],
                                            
                        _zshift_array_key: ['zshift_array',
                                            'float -- z position of the antenna array in m'],
                                            
                        _array_radius_key: ['array_radius',
                                            'float -- Radius of the antenna array in m'],
                                            
                        _event_spacing_samples_key: ['event_spacing_samples',
                                            'int -- Number of samples before first event and between events'],
                                            
                        _element_spacing_key: ['element_spacing',
                                            'float -- Spacing of the waveguide slots'],
                                            
                        _tf_receiver_bin_width_key: ['tf_receiver_bin_width',
                                            'float -- I really do not know what this is'],
                                            
                        _tf_receiver_filename_key: ['tf_receiver_filename',
                                            'str -- File name for the transfer function file. The file has to be placed in hercules/hexbug/Phase3/TransferFunctions'],
                                            
                        _random_seed_key: ['seed_locust',
                                            'int -- Seed for generating noise in Locust'], 
                                                   
                        _noise_floor_psd_key: ['noise_floor_psd',
                                            'float -- PSD value of the noise floor. When this keyword is used Locust will add noise to the simulation'],
                                            
                        _noise_temperature_key: ['noise_temperature',
                                            'float -- Temperature for generation of thermal noise. When this keyword is used Locust will add noise to the simulation. Overrides noise_floor_psd if both keywords are used.'],

                        _center_to_short_key: ['center_to_short',
                                            'float -- Distance of waveguide center to waveguide short in m. Phase 2 specific'],

                        _center_to_antenna_key: ['center_to_antenna',
                                            'float -- Distance of waveguide center to antenna in m. Phase 2 specific ']}
    
    def __init__(self,                
                phase = 'Phase3',
                locust_file_name = None,
                unknown_args_translation = {},
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
        unknown_args_translation: dict, optional
            Dictionary to expand the internal translation from parameter names
            to the configuration file dictionary. This is used to make hercules 
            understand parameters that are internally still unknown to it. For
            example when you want to modify a new parameter 'example-parameter' 
            in the 'array-signal' part of the Locust config file you can call 
            __init__ with a keyword 'example_parameter' (via **kwargs).
            To tell hercules what to do with 'example_parameter' you use
            unknown_args_translation={'example_parameter': ['array-signal', 'example-parameter']}. 
        
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """
        
        self._add_unknown_args_translation(unknown_args_translation)

        self._config_dict = _set_dict_2d(self._key_dict, self._key_to_var_dict, 
                                            kwargs)
        self._config_dict.pop(self._generators_key)
                     
        self._handle_phase(phase, locust_file_name)
        templateConfig = _get_json_from_file(self._file_name)
        
      #  self._config_dict[self._generators_key] = [self._signal_key,
      #                                              self._fft_key, 
      #                                              self._decimate_key, 
      #                                              self._digit_key]
        
        self._finalize(templateConfig)

    # -------- private part --------
    
    def _add_unknown_args_translation(self, unknown_args_translation):
        # Add the translation of unknown arguments to _expression_dict_simple 
        self._key_to_var_dict = deepcopy(self._key_to_var_dict) #prevent overriding the class level dict
        self._key_dict = deepcopy(self._key_dict)
        for key in unknown_args_translation:
            key_0 = unknown_args_translation[key][0]
            key_1 = unknown_args_translation[key][1]
            self._key_to_var_dict[key_1] = [key, '']
            self._key_dict[key_0].append(key_1)
            
    
    def _handle_phase(self, phase, file_name):
        # Read the phase parameter and take appropriate actions according to input
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

            if (self._noise_floor_psd_key or self._noise_temperature_key) in self._config_dict[self._noise_key]:
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
                    
                    
    def get_accepted_keys(self):
        """Return a list of keys that are accepted for the internal config dict.
        
        Returns
        -------
        list
            list of the accepted keys
        """
        vals = self._key_to_var_dict.values()
        return [val[0] for val in vals]
                    
                    
    def make_config_file(self, output_path):
        """Create a final Locust config file from the internal config.
        
        Parameters
        ----------
        output_path : str
            the path to output config file
        """
        
        with open(output_path, 'w') as outFile:
            json.dump(self._config_dict, outFile, indent=2)
    
    @classmethod
    def print_keyword_documentation(cls):
        """Print the documentation of accepted keywords as provided by key_to_var_dict."""
        
        for k in cls._key_to_var_dict:
            entry = cls._key_to_var_dict[k]
            print(entry[0].ljust(25) + entry[1])
    

class SimConfig:
    """A class for the entire simulation configuration.
    
    This class wraps the KassConfig and the LocustConfig. It is recommended that
    end users use this class since it removes another layer of complication.
    
    Attributes
    ----------
    sim_name : str
        Name of the simulation
    """
    
    def __init__(self, phase = 'Phase3', kass_file_name = None, 
                    kass_unknown_args_translation = {},
                    locust_file_name = None,
                    locust_unknown_args_translation = {}, **kwargs):
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
        kass_unknown_args_translation: dict, optional
            Dictionary to expand the internal translation from parameter names
            to configuration file expressions. This is used to make hercules 
            understand parameters for the Kassiopeia configuration that are 
            internally still unknown to it. For example when you want to modify 
            the magnetic field in x direction you can call __init__ with a 
            keyword 'b_x' (via **kwargs). In the config file this corresponds 
            to the line '<external_define name="fieldX" value="0.0"/>'.
            Therefore, to tell hercules what to do with 'b_x' you use
            kass_unknown_args_translation={'b_x': '<external_define name="fieldX" value='}. 
        locust_file_name : str, optional
            The name for the Locust configuration file that should
            be used. This means only the file name, not the full path!
            The file has to be placed in hercules/hexbug/PHASE/, where
            PHASE is the value of the other parameter. If no file name given
            a default file specific to the phase will be used (recommended).
        locust_unknown_args_translation: dict, optional
            Dictionary to expand the internal translation from parameter names
            to the configuration file dictionary. This is used to make hercules 
            understand parameters for the Locust configuration that are 
            internally still unknown to it. For example when you want to modify 
            a new parameter 'example-parameter' in the 'array-signal' part of 
            the Locust config file you can call __init__ with a keyword 
            'example_parameter' (via **kwargs). To tell hercules what to do 
            with 'example_parameter' you use
            locust_unknown_args_translation={'example_parameter': ['array-signal', 'example-parameter']}. 
        **kwargs :
            Arbitrary number of keyword arguments.
        
        Raises
        ------
        ValueError
            If phase is not 'Phase2' or 'Phase3'.
        """
        
        self._sim_name = None
        self._phase = phase
        self._extra_meta_data = {}
        
        self._locust_config = LocustConfig(phase = phase, 
                                           locust_file_name = locust_file_name,
                                           unknown_args_translation = locust_unknown_args_translation, 
                                           **kwargs)
                                        
        self._kass_config = KassConfig( phase = phase, 
                                        kass_file_name = kass_file_name, 
                                        unknown_args_translation = kass_unknown_args_translation,
                                        **kwargs)
                                        
        self._trigger_unknown_parameter_warnings(kwargs)
                                        
    def _get_unknown_parameters(self, kwargs):
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
        
        accepted_parameters = ( self._kass_config.get_accepted_keys() 
                                + self._locust_config.get_accepted_keys() )
                                
        return set(kwargs.keys()).difference(accepted_parameters)
        
    def _trigger_unknown_parameter_warnings(self, kwargs):
        # Print warnings for keyword arguments that are unknown to KassConfig/LocustConfig
        #
        # Useful addition since it is possible to enter an arbitrary number of
        # keyword arguments in the SimConfig. Not strictly necessary but helps
        # to prevent frustration due to typos.
        
        unknown_parameters = self._get_unknown_parameters(kwargs)
        
        for parameter in unknown_parameters:
            print('WARNING - unknown parameter "{}" is ignored'.format(parameter))
    
    @property
    def sim_name(self):
        return self._sim_name
    
    @sim_name.setter
    def sim_name(self, sim_name):
        self._sim_name = sim_name
    
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
            
            phase = config['phase']
            
            instance = cls(phase=phase)
            instance.sim_name = config['sim-name']
            
            instance._locust_config._config_dict = config['locust-config']
            instance._kass_config._config_dict = config['kass-config']
            
        return instance
    
    @classmethod
    def help(cls):
        """Print documentation about the SimConfig.
        
        Prints the docstrings of the class and the __init__ method as well as
        additional information about the accepted parameters in the keyword
        arguments. The latter is provided via the two wrapped configurations.
        
        """
        print(cls.__doc__)
        print(cls.__init__.__doc__)
        print()
        print('List of accepted keyword arguments:')
        KassConfig.print_keyword_documentation()
        LocustConfig.print_keyword_documentation()
        print()
        print('Note that all keyword arguments are optional and take default values from the config files!')
        
    def make_kass_config_file(self, filename_kass):
        """Create the final Kassiopeia file.
        
        Parameters
        ----------
        filename_kass : str
            the path to the output Kassiopeia config file
        """
        self._kass_config.make_config_file(filename_kass)

    def make_locust_config_file(self, filename_locust, filename_kass):
        """Create the final Locust config file.
        
        Parameters
        ----------
        filename_locust : str
            the path to the output Locust config file
        filename_kass : str
            the path to the output Kassiopeia config file
        """
        self._locust_config.set_xml(filename_kass)
        self._locust_config.make_config_file(filename_locust)

    def get_meta_data(self):
        
        #maybe incomplete
        #add more when you realize you need more metadata

        tf_file_name = self._locust_config._config_dict[LocustConfig._array_signal_key].get(LocustConfig._tf_receiver_filename_key)
        n_channels = self._locust_config._config_dict[LocustConfig._sim_key].get(LocustConfig._n_channels_key)
        acq_rate = self._locust_config._config_dict[LocustConfig._sim_key].get(LocustConfig._acq_rate_key)
        lo_f = self._locust_config._config_dict[LocustConfig._array_signal_key].get(LocustConfig._lo_frequency_key)

        meta_data = {}
        meta_data.update(self._extra_meta_data)

        meta_data.update({'trap': self._kass_config._config_dict['geometry']})

        if tf_file_name is not None:
            meta_data.update({'transfer-function': tf_file_name})

        if n_channels is not None:
            meta_data.update({'n-channels': n_channels})

        if acq_rate is not None:
            meta_data.update({'acquisition-rate': acq_rate})

        if lo_f is not None:
            meta_data.update({'lo-frequency': lo_f})
        
        return meta_data
    
    def add_meta_data(self, meta_data):
        self._extra_meta_data = meta_data
    
    def get_config_data(self):
        
        config_data = {}

        x_min = self._kass_config._config_dict['x_min']
        y_min = self._kass_config._config_dict['y_min']
        z_min = self._kass_config._config_dict['z_min']
        pitch_min = self._kass_config._config_dict['theta_min']

        x_max = self._kass_config._config_dict['x_max']
        y_max = self._kass_config._config_dict['y_max']
        z_max = self._kass_config._config_dict['z_max']
        pitch_max = self._kass_config._config_dict['theta_max']

        energy = self._kass_config._config_dict['energy']
        
        r_min = sqrt(x_min**2 + y_min**2)
        phi_min = atan2(y_min, x_min)

        r_max = sqrt(x_max**2 + y_max**2)
        phi_max = atan2(y_max, x_max)

        if x_min==x_max and y_min==y_max and z_min==z_max and pitch_min==pitch_max:
            config_data['r'] = r_min
            config_data['phi'] = phi_min
            config_data['z'] = z_min
            config_data['pitch'] = pitch_min
        else:
            config_data['r_min'] = r_min
            config_data['phi_min'] = phi_min
            config_data['z_min'] = z_min
            config_data['pitch_min'] = pitch_min
            config_data['r_max'] = r_max
            config_data['phi_max'] = phi_max
            config_data['z_max'] = z_max
            config_data['pitch_max'] = pitch_max

        config_data['energy'] = energy

        return config_data


class SimpleSimConfig:
    """A class for a more general simulation configuration
    
    This class is intended for the use with more general python scripts.
    It supports an arbitrary number of keyword arguments. Arguments with the prefix 'meta_'
    are treated as meta parameters. Meta parameters are expected to be the same for an entire dataset.
    All other parameters are considered regular configuration parameters that should vary over a dataset.
    
    Attributes
    ----------
    sim_name : str
        Name of the simulation
    """
    
    def __init__(self, **kwargs):
        """
        Parameters
        ----------
        sim_name : str
            Name of the simulation
        **kwargs :
            Arbitrary number of keyword arguments.
        
        """
        
        self._sim_name = None
        self._extract_kwargs(kwargs)

    def _extract_kwargs(self, kwargs):

        self._meta_data = {}
        self._config_data = {}
        #for e in kwargs:
        #    if e.startswith('meta_'):
        #        new_key = e.removeprefix('meta_')
        #        self._meta_data[new_key] = kwargs[e]
        #    else:
        #        self._config_data[e] = kwargs[e]
        self._config_data = kwargs
    
    @property
    def sim_name(self):
        return self._sim_name
    
    @sim_name.setter
    def sim_name(self, sim_name):
        self._sim_name = sim_name
    
    def to_json(self, file_name):
        """Write a json file with the entire simulation configuration."""
        
        with open(file_name, 'w') as outfile:
            json.dump({ 'sim-name': self._sim_name,
                        'meta-data': self._meta_data, 
                        'config-data': self._config_data}, outfile, 
                        indent=2)#, default=lambda x: x.config_dict)
 
                            
    def to_dict(self):
        """Return a dictionary with the entire simulation configuration.
        
        Returns
        -------
        dict
            Nested dictionary with the simulation configuration
        """
        
        return {'sim-name': self._sim_name,
                'meta-data': self._meta_data, 
                'config-data': self._config_data}
            
    @classmethod
    def from_json(cls, file_name):
        """Return a SimpleSimConfig from a json file.
        
        Creates a new instance of a SimpleSimConfig from the contents of a json file.
        This should only be used with a json file that was created by the 
        `to_json` method. No checks applied for the validity of the json file.
        
        Returns
        -------
        SimpleSimConfig
            The new SimpleSimConfig instance
        """
        
        with open(file_name, 'r') as infile:
            config = json.load(infile)
            
            instance = cls()
            instance.sim_name = config['sim-name']            
            instance._meta_data = config['meta-data']
            instance._config_data = config['config-data']
            
        return instance
    
    @classmethod
    def help(cls):
        """Print documentation about the SimConfig.
        
        Prints the docstrings of the class and the __init__ method as well as
        additional information about the accepted parameters in the keyword
        arguments. The latter is provided via the two wrapped configurations.
        
        """
        print(cls.__doc__)
        print(cls.__init__.__doc__)

    def get_meta_data(self):
        return self._meta_data
    
    def get_config_data(self):
        return self._config_data
    
    def add_meta_data(self, meta_data):
        self._meta_data = meta_data


class ConfigList:

    def __init__(self, **kwargs):
        self._config_list = []
        self._meta_data = kwargs
        self._extra_meta_data = None
        self._config_list_type = None
        self._config_data_keys = None
        self._add_version_metadata()

    def _add_version_metadata(self):
        from . import __hexbug_version__, __version__, __python_script_version__
        from .constants import CONFIG
        self._meta_data['hercules-version'] = __version__
        self._meta_data['hexbug-version'] = __hexbug_version__
        self._meta_data['python-script-version'] = __python_script_version__
        self._meta_data['python-script-dir'] = CONFIG.python_script_path
        self._not_commited_warning()

    def _not_commited_warning(self):
        version_keys = ['hercules-version', 'hexbug-version', 'python-script-version']
        uncommitted = False
        for k in version_keys:
            if self._meta_data[k].endswith('-dirty/untracked'):
                uncommitted = True
                print(f'WARNING! Uncomitted changes in {k.removesuffix("-version")}')
        
        if uncommitted:
            print('Trying to run with uncommitted changes. This is dangerous for reproducibility!')
            ok = input('Continue? (y/n): ').lower().strip() == 'y'
            if not ok:
                print('Aborting. Commit your work and try again :)')
                exit()
            print("You know what you're doing :)")

    def add_config(self, config):

        n = len(self._config_list)

        if n == 0:

            common_keys = set(self._meta_data.keys()).intersection(config.get_meta_data().keys())

            if len(common_keys)>0:
                print('Warning, adding a config with metadata that overwrites an existing metadata entry! This might not be what you want.')

            self._extra_meta_data = config.get_meta_data()
            self._meta_data.update(config.get_meta_data())
            self._config_list_type = type(config)
            self._config_data_keys = config.get_config_data().keys()

        if type(config) is not self._config_list_type:
            raise TypeError('All configurations in the configuration list have to be of the same type!')
        
        if config.get_meta_data() != self._extra_meta_data:
            raise RuntimeError('All configurations in the configuration list need the same metadata')
        
        if config.get_config_data().keys() != self._config_data_keys:
            raise RuntimeError('All configurations in the configuration list need the same configuration data keys')

        config.add_meta_data(self._meta_data)
        config.sim_name = f'run{n}'
        self._config_list.append(config)

    def get_internal_list(self):
        return self._config_list
    
    def get_list_type(self):
        return self._config_list_type

    def get_meta_data(self):
        return self._meta_data
    
    def get_config_data_keys(self):
        return self._config_data_keys


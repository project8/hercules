# hercules
Python package for scripting our simulation workflows

## Requirements

A python environment with version >= 3.7.7 (might also work with 3.5 but that is untested). Required python modules will be installed automatically.
Running on a desktop requires [docker](https://www.docker.com/get-started). Furthermore, you should make sure that your user is able to [run docker without prefixing with `sudo`](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user). Finally, you should also pull the p8compute docker image with `docker pull project8/p8compute`.

## Installation

First, clone the repository to your prefered location. Then go into the repo and initialize the submodules `git submodule update --init`. Next, make a copy of the default [configuration](./hercules/settings/config.default.ini) to `./hercules/settings/config.ini` and modify the new one to your needs. On the Yale cluster you enter 'grace', while on a desktop you enter 'desktop' (both without quotes) for the environment setting. For usage on a desktop you might also want to adjust the number of parallel jobs. In theory you can set it as high as the number of logical cores in your system. However, depending on your simulation settings Locust can consume a lot of RAM. Therefore, using as many cores as possible can potentially overload the RAM. In that case your system will become unusable. Do not touch the rest of the file.
```
[USER]
#possible values are 'desktop', 'grace'
ENVIRONMENT = grace
DESKTOP_PARALLEL_JOBS = 2
```

As last step, run `pip install .` in the directory with setup.py. 

Note: If you are using the system wide python environment instead of a virtual environment (e.g. with Anaconda) the package data will go to `/usr/local`, which causes access permission issues with Docker. As a workaround use `pip install -e .` which creates symlinks to the repo instead of copying files.

## Usage

Example script:

```python
from hercules import KassLocustP3, SimConfig, ConfigList

sim = KassLocustP3('/path/to/your/workingDir', use_kass=True, use_locust=True)
configlist = ConfigList(info='Additional meta data')
#just an example
config = SimConfig(phase='Phase3', kass_file_name='someXMLFile.xml', 
                    locust_file_name='someJSONFile.json', 
                    n_channels=2, seed_locust=1, v_range=7.0,
                    egg_filename='someFileName.egg', seed_kass =12534, x_min=0.1e-5, 
                    x_max=0.1e-5, t_max=0.5e-6,
                    geometry='FreeSpaceGeometry_V00_00_10.xml')


configlist.add_config(config)
#runs the simulations
sim(configlist)

```
The example above runs a single phase 3 Kassiopeia-Locust simulation with the given parameters. Hercules is most useful if you run `config=...` and `configlist.add_config(config)` in an arbitrary python loop. The line `sim(configlist)` will always run all the simulation configurations from the list. All parameters are optional. Omitted parameters in general take on default values with the exception being the seeds which are generated on the fly. The phase parameter can take the values 'Phase2' or 'Phase3' (default). Hercules generates the config files for Kassiopeia and Locust based on the inputs, the selected phase and the template config files which also provide the default values. All config files will be taken from the [hexbug](https://github.com/project8/hexbug/tree/459dffe30eea7d8bab9ddff78b63fda5198041ad) repository. Once hercules is installed you can run the script from anywhere specifying any working directory that you want and it will always be able to find the config files. Config files from hexbug (including Transfer functions and trap geometries) are passed by just their names as demonstrated above. Hercules will look for them in the appropriate directory of hexbug depending on the phase. In most cases you want to use the defaults for 'kass_file_name' and 'loucst_file_name'.  
If you need the full list of simulation parameters you can ask hercules for a help message. `he.SimConfig.help()` will print a full list of all available keyword arguments with a short explanation for each one.  
You can find example scripts in [examples](./examples). Hercules scripts work in a desktop environment as well as on the grace cluster without requiring any modifications.

Running hercules with the example from above will create a `hercules.Dataset` in the specified working directory. A `hercules.Dataset` is a dataformat in the form of an indexed directory structure which handles like a normal directory. For each configuration in the `configlist` hercules creates a subdirectory in the working directory that is called `run{i}` with `i` being the incremental number of configurations. In addition to that the directory contains a text file `info.txt` with some info about the dataset (meta data and parameter axes) and the very important file `index.he`. The latter is the pickled `hercules.Dataset` python object. Its core is a hashmap to map configuration parameters to the corresponding paths in the working directory. The class implements some utility for convenient recovery of any data stored in the subdirectories. In the example below a loop is used to recover all egg files but note that under each path other data than just the egg file can be found (with Locust as default you get at least log files and a json file with the configuration), which can be accessed with that path. See [dataset_example](./examples/dataset_example.py) for more details on how to utilize the `Dataset` class.

```python
from hercules import Dataset, LocustP3File

dataset = Dataset.load('/path/to/your/workingDir')

for param, path in dataset:
    data = LocustP3File(path / 'someFileName.egg')
```

Another interesting feature is the use of python scripts for post-processing. Any python script located in [hexbug/CRESana](./hercules/hexbug/CRESana/) (was implemented for the use with [CRESana](https://github.com/MCFlowMace/CRESana)) can be passed by its name and for each configuration it will be run after Kassiopeia and Locust. This represents another way of producing more data for a single configuration which can be retrieved via the path from the `Dataset`.

```python
sim = KassLocustP3('/path/to/your/workingDir', use_kass=True, use_locust=True, python_script='post_processing.py')
```

The sole command line argument of these python scripts is the path of the result. More parameters can be used in the python script by importing the `SimConfig` object of the configuration via json. Thus the top of these scripts should be like

```python
from hercules import SimConfig

path = sys.argv[1]
config = SimConfig.from_json(path + '/SimConfig.json').to_dict()
#get pitch angle
pitch = config['kass-config']['theta_min']

```

Finally it is important to mention that the use of Kassiopeia and Locust is optional and can both be turned off as seen below. It depends on the configuration if it makes sense to run like that.

```python
sim = KassLocustP3('/path/to/your/workingDir', use_kass=True, use_locust=False, python_script='run_no_locust.py')
```

Without both Locust and Kassiopeia hercules turns into a simple convenience tool for running python scripts on a parameter grid on the grace cluster with the `hercules.Dataset` as output. In this case the simpler and more flexible `SimpleSimConfig` can be used. It supports any configuration parameters as passed via keyword arguments, which can be passed to the script. Together with the metadata (`info`) which is added on creation of the `ConfigList` they will be represented in the final `Dataset`. Example:

```python
sim = KassLocustP3('/path/to/your/workingDir', use_kass=False, use_locust=False, python_script='run_no_kass_no_locust.py')
configlist = ConfigList(info='Additional meta data')
config = SimpleSimConfig(x=2., some_exotic_data_name='interesting_value')
configlist.add_config(config)
sim(configlist)
```

Corresponding script head of `run_no_kass_no_locust.py`:

```python
from hercules import SimpleSimConfig

path = sys.argv[1]
config = SimpleSimConfig.from_json(path + '/SimConfig.json').to_dict()

#get config parameters
x = config['x']
some_exotic_data_name = config['some_exotic_data_name']
```

## Running on grace cluster

For running on the grace cluster there are a couple of extra keyword arguments for the `KassLocustP3` class.

```python
sim(config_list, memory='1000', timelimit='01:00:00', n_cpus=8, batch_size=3)
```

Setting `timelimit` and `memory` only as high as required for the job is good practice and should theoretically help with job scheduling. `batch_size` determines how many entries in `config_list` are combined into a single job, you need to make sure to have a `batch_size` that gets you job run times >10 minutes since the cluster is not well suited for high job throughput. `n_cpus` defaults to 2 for the use with Locust and Kass+Locust alone does not profit from using more than that. Setting it to higher values is only useful if your postprocessing python script uses muliple processes.

## Tests

To test whether Docker is working on your device, the unittest `test_locustP2.py` can be used. Run the following in cmd line:

```sh
cd ./test
python -m unittest test_locustP2.py
```

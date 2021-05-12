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
import hercules as he

sim = he.KassLocustP3('/path/to/your/workingDir')
#just an example
config = he.SimConfig('yourSimulationName', phase='Phase3', kass_file_name='someXMLFile.xml', 
                    locust_file_name='someJSONFile.json', 
                    nChannels=2, seedLocust=1, vRange=7.0,
                    eggFilename='someFileName.egg', seedKass =12534, xMin=-0.1e-5, 
                    xMax=0.1e-5, tMax=0.5e-6,
                    geometry='FreeSpaceGeometry_V00_00_10.xml')


sim(config) #can also take a list of configs

```
The example above runs a single phase 3 Kassiopeia-Locust simulation with the given parameters. All parameters except for the simulation name are optional. Omitted parameters in general take on default values with the exception being the seeds which are generated on the fly. The phase parameter can take the values 'Phase2' or 'Phase3' (default). Hercules generates the config files for Kassiopeia and Locust based on the inputs, the selected phase and the template config files which also provide the default values. All config files will be taken from the [hexbug](https://github.com/project8/hexbug/tree/459dffe30eea7d8bab9ddff78b63fda5198041ad) repository. Once hercules is installed you can run the script from anywhere specifying any working directory that you want and it will always be able to find the config files. Config files from hexbug (including Transfer functions and trap geometries) are passed by just their names as demonstrated above. Hercules will look for them in the appropriate directory of hexbug depending on the phase. In most cases you want to use the defaults for 'kass_file_name' and 'loucst_file_name'.  
If you need the full list of simulation parameters you can ask hercules for a help message. `he.SimConfig.help()` will print a full list of all available keyword arguments with a short explanation for each one.  
You can find example scripts in [examples](./examples). Hercules scripts work in a desktop environment as well as on the grace cluster without requiring any modifications. 

## Tests

To test whether Docker is working on desktop, the `test_eggreader.py` provides a separate test. Run the following in cmd line:

```sh
cd ./test
python -m unittest test_eggreader.EggReaderTest.test_locust
```

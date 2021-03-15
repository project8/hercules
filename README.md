# hercules
Python package for scripting our simulation workflows

## Requirements

A python environment with version >= 3.7.7 (might also work with 3.5 but that is untested). Required python modules will be installed automatically.
Running on a desktop requires [docker](https://www.docker.com/get-started).

## Installation

First, adjust the environment setting in the [configuration](./hercules/settings/config.ini). On the Yale cluster you enter 'grace', while on a desktop (or laptop) you enter 'desktop' (both without quotes). For usage on a desktop you might also want to adjust the number of parallel jobs. In theory you can set it as high as the number of logical cores in your system. However, depending on your simulation settings Locust can consume a lot of RAM. Therefore, using as many cores as possible can potentially overload the RAM. In that case your system will become unusable. Do not touch the rest of the file.
```
[USER]
#possible values are 'desktop', 'grace'
ENVIRONMENT = grace
DESKTOP_PARALLEL_JOBS = 2
```

Second, run `pip install .` in the directory with setup.py. That's all.

Note: run `pip install --editable .` for an editable install (deprecated practice).

## Usage

Example script:

```python
import hercules as he

sim = he.KassLocustP3('/path/to/your/workingDir')
#just an example
config = SimConfig('yourSimulationName', nChannels=2, seedLocust=1, vRange=7.0,
                    eggFilename='someFileName.egg', seedKass =12534, xMin=-0.1e-5, 
                    xMax=0.1e-5, tMax=0.5e-6,
                    geometry='FreeSpaceGeometry_V00_00_10.xml')


sim(config) #can also take a list of configs

```
The example above runs a single Kassiopeia-Locust simulation with the given parameters. The full list of available parameters can be found at (documentation missing). If omitted, the seeds are generated based on the current time. Apart from the seeds, omitted parameters take on default values. The default configuration is determined by the files in the [hexbug](https://github.com/project8/hexbug/tree/459dffe30eea7d8bab9ddff78b63fda5198041ad) repo. Transfer functions and trap geometries from hexbug can be passed by their names only as demonstrated above. The script above is agnostic about the location of the hexbug repository, hercules will find it on its own. Once hercules is installed you can run the script from anywhere specifying any working directory that you want. Additionally, the same script works in a desktop environment as well as on the cluster without modification. 

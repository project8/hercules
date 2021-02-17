# hercules
Python package for scripting our simulation workflows

## Installation

Run `pip install -e .` in the directory with setup.py.

## Usage plan

The package should provide the user a simple interface to run simulations. A user can clone the package, install it to their python environment with pip and use it with simple scripts that run anywhere. The following is not implemented yet, but should give an idea of how this should work.

```python

from hercules import SimConfig, Locust

workingdir='/home/flthomas/Project8/simulations'

#modify the default config
conf = SimConfig(nChannels=60, xMin=0.02, xMax=0.02, tMax=0.00015, recordSize=41000)

#run Locust in container/on cluster
locustWrapper = Locust(workingdir)
locustWrapper(conf, 'r002_60_channels') #submit a job

```

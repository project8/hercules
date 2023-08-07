
"""

Author: F. Thomas
Date: August 07, 2023

"""

from hercules import Dataset, LocustP3File
from pathlib import Path

module_dir = Path(__file__).parent.absolute()
dataset_name = 'workingDirP3'

path = module_dir / dataset_name

#load the hercules dataset
dataset = Dataset.load(path)

#print the metadata which is valid for all entries in the dataset
print(dataset.meta_data)

#print the axes of the dataset grid
axes = dataset.axes
for i, ax in enumerate(axes):
    print(f'{dataset.config_data_keys[i]} -> {ax}' )

#get path to data by index of all data axes
param, path = dataset.get_path([0, 0, 0, 0, 0], method='index')
print(param, path)

#use path
data = LocustP3File(path / 'someFileName.egg')

#get path to data by exact value
param, path = dataset.get_path([0., 0., 0., 87., 18600.], method='exact')
print(param, path)

#get path to data by exact value
param, path = dataset.get_path([axes[0][3], axes[1][0], axes[2][0], axes[3][0], axes[4][0]], method='exact')
print(param, path)

#get path to data by value using nearest neighbor interpolation
param, path = dataset.get_path([0.0, 0.0, 0.0, 0.0, 0.0], method='interpolated')
print(param, path)

#iterate over all data in dataset
for param, path in dataset:
    print(param, path)
    data = LocustP3File(path / 'someFileName.egg')
# We need a couple of modules to import the data and print it
import json
from pprint import pprint

# We import numpy to process data, but we don't actually need it to import the data
import numpy as np

import pandas as pd

from matplotlib import pyplot as plt

from mpl_toolkits.mplot3d import Axes3D

data_filename = '../data/data_export_id_39.json'

# We open the file
with open(data_filename, 'r') as df:
    # And read the contents
    file_contents = ''.join(df.readlines())

# Next we decode the file contents using the json module
experiment_configuration = json.loads(file_contents)

## Now we have all the data available

# We create lists to contain the data we're interested in
frequencies = []
mean_ac_rms_amplitudes = []

mean_dc_fields = []

mean_lockin_amplitudes = []
mean_lockin_phases = []

mean_mixing_chamber_temperatures = []

# Then we run through each step
for step in experiment_configuration['steps']:
    # We create a second, temporary, list to hold the the amplitudes of this step (the ones we take the mean of)
    ac_rms_amplitudes = []

    dc_fields = []

    lockin_amplitude = []
    lockin_phases = []

    mixing_chamber_temperatures = []

    # Add the frequency to the frequencies list
    frequencies.append(step['n9310a_frequency'])

    # We iterate through the datapoints
    for datapoint in step['datapoints']:
        # And we iterate through the magnetism datapoints
        for mdp in datapoint['magnetism_datapoints']:
            # We grab the ac rms amplitude
            ac_rms_amplitudes.append(mdp['ac_rms_field'])

            # We grab the DC field
            dc_fields.append(mdp['dc_field'])

            # We add the lockin data to the list we created inside the for loop
            lockin_amplitude.append(mdp['lockin_amplitude'])
            lockin_phases.append(mdp['lockin_phase'])

        for cdp in datapoint['temperature_datapoints']:
            mixing_chamber_temperatures.append(cdp['t_mixing_chamber_1'] / 2 + cdp['t_mixing_chamber_2'] / 2)

    # Now we find a mean of that list and add it to the list of mean amplitudes
    mean_ac_rms_amplitudes.append(np.mean(ac_rms_amplitudes))

    mean_dc_fields.append(np.mean(dc_fields))

    mean_lockin_amplitudes.append(np.mean(lockin_amplitude))
    mean_lockin_phases.append(np.mean(lockin_phases))

    mean_mixing_chamber_temperatures.append(np.mean(mixing_chamber_temperatures))

df = pd.DataFrame({
    'ac_rms': mean_ac_rms_amplitudes,
    'ac_frequency': frequencies,
    'dc': mean_dc_fields,
    'amplitude': mean_lockin_amplitudes,
    'phase': mean_lockin_phases,
    'temperature': mean_mixing_chamber_temperatures
})

fig = plt.figure()
ax = Axes3D(fig)

ax.scatter(df['ac_frequency'], df['amplitude'], df['amplitude'])

plt.show()

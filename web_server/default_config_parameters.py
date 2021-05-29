# This function returns a dictionary, which contains all the parameters in the configuration
# The parameters are then saved to the database (with the value provided here) as JSON
# The parameters are loaded from the database if they already exist
def get_default_configuration_parameters():
    return {
        'picowatt_delay': 5,  # Number of seconds to wait between measurements of the picowatt
        'save_every_n_temperatures': 20,  # number of measurements
        'max_timeperiod': 120,  # hours
        'is_saving_cryo_temperatures': False  # Keep track of whether we are saving all temperatures
    }

# This function returns a dictionary, which contains all the parameters in the configuration
# The parameters are then saved to the database (with the value provided here) as JSON
# The parameters are loaded from the database if they already exist
def get_default_configuration_parameters():
    return {
        'is_saving_cryo_temperatures': False
    }

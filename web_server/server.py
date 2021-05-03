# Import webserver related packages
from aiohttp import web
import socketio
import json

# Import our own models (and a database connection
from models import ExperimentStep, ExperimentConfiguration, Session, StationStatus, DataPoint, MagnetismDataPoint, \
                   MagnetismMeasurement, CryogenicsDataPoint, PressureDataPoint, TemperatureDataPoint, \
                   ConfigurationParameter, db

# Import datetime so we can query on the date fields
import datetime

# Import packages for the plots
import io
import numpy as np
import matplotlib.pyplot as plt

# Import default configuration
import default_config_parameters

# Import namespaces for the socket connections
from server_namespaces.browser_events import BrowserNamespace
from server_namespaces.cryo_events import CryoNamespace
from server_namespaces.magnetism_events import MagnetismNamespace

# Create app and setup websockets
sio = socketio.AsyncServer(ping_timeout=300)
app = web.Application()
sio.attach(app)

# Initialize namespaces
cryo_space = CryoNamespace('/cryo')
magnetism_space = MagnetismNamespace('/magnetism')
browser_space = BrowserNamespace('/browser')

# Setup cross references between namespaces
for space in [cryo_space, magnetism_space, browser_space]:
    space.set_namespaces(cryo_space, magnetism_space, browser_space)

# Register namespaces for websockets
sio.register_namespace(cryo_space)
sio.register_namespace(magnetism_space)
sio.register_namespace(browser_space)

# Open the index template to cache it
with open('index.html') as f:
    index_page_html = f.read()


# Create an index page for the initial browser request
async def index(request):
    return web.Response(text=index_page_html, content_type='text/html')


# Endpoint used to export data
async def export_data(request):
    # Check id exists
    if 'id' not in request.query:
        return web.Response(text='Could not find the requested id', content_type='text/html')

    # Grab the id
    config_id = request.query['id']

    # Now we want to start the export
    # Open connection to database
    with db.connection_context():
        # Grab the configuration first
        ecl = ExperimentConfiguration.select().where(ExperimentConfiguration.id == config_id).dicts()

        # Check if we have a result
        if len(ecl) > 0:
            # Grab the first result (There should only be one when we query by id)
            ec = ecl[0]

            # Convert date format
            ec['created'] = ec['created'].isoformat()

            # Compute the number of points taken
            ec['n_points_taken'] = ExperimentStep.select() \
                .where(ExperimentStep.experiment_configuration == ec['id']) \
                .where(ExperimentStep.step_done == True) \
                .count()

            # Compute the number of points taken
            ec['n_points_total'] = ExperimentStep.select() \
                .where(ExperimentStep.experiment_configuration == ec['id']) \
                .count()

            # Add an empty array to contain steps
            ec['steps'] = []

            # Now we're done processing the configuration
            # Next we get all the datapoints that were saved
            # We start by iterating over all the steps in the experiment
            for step in ExperimentStep.select().where(ExperimentStep.experiment_configuration == ec['id']).dicts():
                # Convert date format
                step['created'] = step['created'].isoformat()

                # Add an empty array to contain datapoints
                step['datapoints'] = []

                # And we iterate through all the datapoints for the step
                for dp in DataPoint.select().where(DataPoint.step == step['id']):
                    # Create a dict to contain the collected information
                    datapoint_dict = {
                        'id': dp.id,
                        'created': dp.created.isoformat(),
                        'magnetism_datapoints': [],
                        'temperature_datapoints': [],
                        'pressure_datapoints': []
                    }

                    # Next we find the magnetism datapoint
                    for mdp in MagnetismDataPoint.select().where(MagnetismDataPoint.datapoint == dp):
                        # For this we find the magnetism measurements (where we actually store the data)
                        mdps = MagnetismMeasurement.select().where(MagnetismMeasurement.magnetism_data_point == mdp)

                        # Save it to the datapoint dict
                        for magnetism_datapoint in list(mdps.dicts()):
                            datapoint_dict['magnetism_datapoints'].append(magnetism_datapoint)

                    # And we find the cryodatapoint
                    for cdp in CryogenicsDataPoint.select().where(CryogenicsDataPoint.datapoint == dp):
                        # Similarly we find pressure and temperature datapoints
                        pdps = PressureDataPoint.select().where(PressureDataPoint.cryo_data_point == cdp)
                        tdps = TemperatureDataPoint.select().where(TemperatureDataPoint.cryo_data_point == cdp)

                        # Save them to the datapoint dict
                        for pressure_datapoint in list(pdps.dicts()):
                            datapoint_dict['pressure_datapoints'].append(pressure_datapoint)

                        for temperature_datapoint in list(tdps.dicts()):
                            datapoint_dict['temperature_datapoints'].append(temperature_datapoint)

                    # Save the datapoint to the step
                    step['datapoints'].append(datapoint_dict)

                # Save the step to the configuration
                ec['steps'].append(step)

            # And finally we send the response data
            return web.json_response(
                headers={'Content-Disposition': f'Attachment'},
                body=json.dumps(ec)
            )
        else:
            return web.Response(text='Attempted to export ' + str(config_id) + ' but no such config found',
                                content_type='text/html')


# Endpoint to plot the temperatures saved in the last n hours
async def plot_saved_temperatures(request):
    # Open connection to database
    with db.connection_context():
        # Create a timedelta for the query (based on the config)
        period_delta = datetime.timedelta(hours=ConfigurationParameter.read_config_value('max_timeperiod'))
        period = datetime.datetime.today() - period_delta

        # Get the temperatures
        temperatures = TemperatureDataPoint\
            .select()\
            .where(TemperatureDataPoint.created > period)\
            .order_by(TemperatureDataPoint.created)\
            .dicts()

        # Determine the shape of the arrays in our output
        if len(temperatures) > 0:
            temp_shape = (len(temperatures), 1)
        else:
            temp_shape = (1, 1)

        # Create empty arrays to hold the data
        times = np.zeros(shape=temp_shape)
        t_upper_hex = np.zeros(shape=temp_shape)
        t_lower_hex = np.zeros(shape=temp_shape)
        t_he_pot = np.zeros(shape=temp_shape)
        t_1st_stage = np.zeros(shape=temp_shape)
        t_2nd_stage = np.zeros(shape=temp_shape)
        t_inner_coil = np.zeros(shape=temp_shape)
        t_outer_coil = np.zeros(shape=temp_shape)
        t_switch = np.zeros(shape=temp_shape)
        t_he_pot_2 = np.zeros(shape=temp_shape)

        # Sort the data into the relevant arrays
        for idx, t_obj in enumerate(temperatures):
            times[idx] = t_obj['created'].timestamp() # Convert the datetime to seconds
            t_upper_hex[idx] = t_obj['t_upper_hex']
            t_lower_hex[idx] = t_obj['t_lower_hex']
            t_he_pot[idx] = t_obj['t_he_pot']
            t_1st_stage[idx] = t_obj['t_1st_stage']
            t_2nd_stage[idx] = t_obj['t_2nd_stage']
            t_inner_coil[idx] = t_obj['t_inner_coil']
            t_outer_coil[idx] = t_obj['t_outer_coil']
            t_switch[idx] = t_obj['t_switch']
            t_he_pot_2[idx] = t_obj['t_he_pot_2']

        # Create the plot
        plt.subplots(figsize=(8, 3.5))

        # Plot the data
        plt.plot(times, t_upper_hex, label='Upper HEx')
        plt.plot(times, t_lower_hex, label='Lower HEx')
        plt.plot(times, t_he_pot, label='He Pot')
        plt.plot(times, t_he_pot_2, label='He Pot CCS')
        plt.plot(times, t_1st_stage, label='1st stage')
        plt.plot(times, t_2nd_stage, label='2nd stage')
        plt.plot(times, t_inner_coil, label='Inner coil')
        plt.plot(times, t_outer_coil, label='Outer coil')
        plt.plot(times, t_switch, label='Switch')

        # Pretty up the plot
        plt.xlabel('Time [seconds]')
        plt.ylabel('Temperature [kelvin]')
        plt.grid()
        plt.legend(loc='lower left')
        plt.tight_layout()

        # Save the plot to a buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()

        # Reset the buffer placement, and send the response
        buffer.seek(0)
        return web.Response(body=buffer, headers={'Content-Type': 'image/png', 'Cache-Control': 'max-age=0,no-store'})


# Setup the http routes
app.router.add_static('/static', 'static')
app.router.add_get('/export', export_data)
app.router.add_get('/get_plot', plot_saved_temperatures)
app.router.add_get('/', index)

if __name__ == '__main__':
    # Ensure the database tables are created
    with db.connection_context():
        db.create_tables([Session, ExperimentConfiguration, ExperimentStep, StationStatus, DataPoint,
                          MagnetismDataPoint, MagnetismMeasurement, CryogenicsDataPoint, PressureDataPoint,
                          TemperatureDataPoint, ConfigurationParameter])

    # Create a default configuration object
    default_config = default_config_parameters.get_default_configuration_parameters()

    # Now we load any missing keys into the database
    for key in default_config.keys():
        ConfigurationParameter.read_config_value(key, default_config[key])

    # Run the app
    web.run_app(app, port=3000, host='0.0.0.0')

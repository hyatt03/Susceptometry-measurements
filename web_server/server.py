# Import webserver related packages
from aiohttp import web
import socketio
import json

# Import our own models (and a database connection
from models import ExperimentStep, ExperimentConfiguration, Session, StationStatus, DataPoint, MagnetismDataPoint, \
                   MagnetismMeasurement, CryogenicsDataPoint, PressureDataPoint, TemperatureDataPoint, \
                   ConfigurationParameter, db

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


# Setup the http routes
app.router.add_static('/static', 'static')
app.router.add_get('/export', export_data)
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

from peewee import *
from playhouse.pool import PooledSqliteDatabase
import numpy as np

# Connect to database using connection pool
db = PooledSqliteDatabase('dashboard.db',
                          max_connections=32,
                          stale_timeout=300,
                          pragmas={
                              'journal_mode': 'wal',
                              'cache_size': -1 * 64000,  # 64MB
                              'foreign_keys': 1,
                              'ignore_check_constraints': 0,
                              'synchronous': 0
                          })


# Simple baseclass that inherits the PooledSqliteDatabase
class DBModel(Model):
    class Meta:
        database = db


# Sessions table
class Session(DBModel):
    idn = CharField(max_length=50)
    sid = CharField(max_length=50)
    type = CharField(max_length=10)


# Configure experiments
class ExperimentConfiguration(DBModel):
    # Metadata
    created = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    created_by = ForeignKeyField(Session, backref='experiments')

    # SR830 configuration
    sr830_sensitivity = FloatField()
    sr830_frequency = FloatField()
    sr830_buffersize = IntegerField()

    # N9310A configuration
    n9310a_min_frequency = FloatField()
    n9310a_max_frequency = FloatField()
    n9310a_min_amplitude = FloatField()
    n9310a_max_amplitude = FloatField()
    n9310a_sweep_steps = IntegerField()

    # Cryonics magnet configuration
    magnet_min_field = FloatField()
    magnet_max_field = FloatField()
    magnet_sweep_steps = IntegerField()

    # Analog Discovery 2 configuration
    oscope_resistor = FloatField()

    # Data collection options
    data_wait_before_measuring = FloatField()
    data_points_per_measurement = IntegerField()

    def generate_steps(self):
        if self.n9310a_min_frequency == self.n9310a_max_frequency:
            frequencies = [self.n9310a_max_frequency]
        else:
            frequencies = np.linspace(self.n9310a_min_frequency, self.n9310a_max_frequency, self.n9310a_sweep_steps)

        if self.n9310a_min_amplitude == self.n9310a_max_amplitude:
            amplitudes = [self.n9310a_max_amplitude]
        else:
            amplitudes = np.linspace(self.n9310a_min_amplitude, self.n9310a_max_amplitude, self.n9310a_sweep_steps)

        if self.magnet_min_field == self.magnet_max_field:
            magnetic_fields = [self.magnet_max_field]
        else:
            magnetic_fields = np.linspace(self.magnet_min_field, self.magnet_max_field, self.magnet_sweep_steps)

        # Generate the steps
        steps = []
        # We sweep over frequency
        for frequency in frequencies:
            # Amplitude
            for amplitude in amplitudes:
                # And magnetic field
                for magnetic_field in magnetic_fields:
                    steps.append({
                        'experiment_configuration': self.id,
                        'sr830_sensitivity': self.sr830_sensitivity,
                        'sr830_frequency': self.sr830_frequency,
                        'sr830_buffersize': self.sr830_buffersize,
                        'n9310a_frequency': frequency,
                        'n9310a_amplitude': amplitude,
                        'magnet_field': magnetic_field,
                        'oscope_resistor': self.oscope_resistor,
                        'data_wait_before_measuring': self.data_wait_before_measuring,
                        'data_points_per_measurement': self.data_points_per_measurement
                    })

        # Save the steps (100 at a time)
        with db.atomic():
            for batch in chunked(steps, 100):
                ExperimentStep.insert_many(batch).execute()

        # Return number of steps generated
        return len(steps)


# Experiment steps (Generated from ExperimentConfiguration)
class ExperimentStep(DBModel):
    # Metadata
    created = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    step_done = BooleanField(default=False)
    experiment_configuration = ForeignKeyField(ExperimentConfiguration, backref='experiment_steps')

    # SR830 configuration
    sr830_sensitivity = FloatField()
    sr830_frequency = FloatField()
    sr830_buffersize = IntegerField()

    # N9310A configuration
    n9310a_frequency = FloatField()
    n9310a_amplitude = FloatField()

    # Cryonics magnet configuration
    magnet_field = FloatField()

    # Analog Discovery 2 configuration
    oscope_resistor = FloatField()

    # Data collection options
    data_wait_before_measuring = FloatField()
    data_points_per_measurement = IntegerField()

    def generate_datapoint(self):
        # Create datapoint and save it
        DataPoint(step=self).save()


class StationStatus(DBModel):
    # Are we currently running a measurement
    is_running = BooleanField(default=False)

    # Are the instruments connected
    cryo_connection_established = BooleanField(default=False)
    magnet_connection_established = BooleanField(default=False)


class DataPoint(DBModel):
    # Backreference to the step that triggered the measurement
    step = ForeignKeyField(ExperimentStep, backref='datapoint')
    created = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    def save_magnetism_data(self, data):
        # Create model to hold references to actual collected data
        magnetism_data_point = MagnetismDataPoint(datapoint=self)
        magnetism_data_point.save()

        # Iterate through the measurements we have collected for this step
        # and save the data
        for ac, dc, amp, phs in zip(data['ac_rms_field'], data['dc_field'], 
                                    data['lockin_amplitude'], data['lockin_phase']):
            MagnetismMeasurement(magnetism_data_point=magnetism_data_point, ac_rms_field=ac, 
                                 dc_field=dc, lockin_amplitude=amp, lockin_phase=phs).save()

    def save_cryo_data(self, data):
        # Create model to hold references to actual collected data
        cryogenics_data_point = CryogenicsDataPoint(datapoint=self)
        cryogenics_data_point.save()

        # Iterate through the measurements we have collected for this step
        # and save the data
        for i in range(len(data['temperatures']['t_still'])):
            # Save pressures
            PressureDataPoint(
                cryo_data_point=cryogenics_data_point,
                p_1=data['pressures']['p_1'][i],
                p_2=data['pressures']['p_2'][i],
                p_3=data['pressures']['p_3'][i],
                p_4=data['pressures']['p_4'][i],
                p_5=data['pressures']['p_5'][i],
                p_6=data['pressures']['p_6'][i],
                p_7=data['pressures']['p_7'][i],
                p_8=data['pressures']['p_8'][i]
            ).save()

            # Save temperatures
            TemperatureDataPoint(
                cryo_data_point=cryogenics_data_point,
                t_0=data['temperatures']['t_still'][i],
                t_1=data['temperatures']['t_1'][i],
                t_2=data['temperatures']['t_2'][i],
                t_3=data['temperatures']['t_3'][i],
                t_4=data['temperatures']['t_4'][i],
                t_5=data['temperatures']['t_5'][i],
                t_6=data['temperatures']['t_6'][i],
                t_7=data['temperatures']['t_1'][i],  # @TODO: Use the actual temperatures
                t_8=data['temperatures']['t_1'][i]
            ).save()


class MagnetismDataPoint(DBModel):
    # Backreference to the datapoint which collects the measurements from all stations
    datapoint = ForeignKeyField(DataPoint, backref='magnetism')
    created = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class MagnetismMeasurement(DBModel):
    # Create fields to store the data
    ac_rms_field = FloatField()
    dc_field = FloatField()
    lockin_amplitude = FloatField()
    lockin_phase = FloatField()

    # Backreference the magnetism datapoint model to collect many measurements per step
    magnetism_data_point = ForeignKeyField(MagnetismDataPoint, backref='measurements')


class CryogenicsDataPoint(DBModel):
    # Backreference to the datapoint which collects the measurements from all stations
    datapoint = ForeignKeyField(DataPoint, backref='cryogenics')
    created = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class PressureDataPoint(DBModel):
    # Pressure data
    p_1 = FloatField()
    p_2 = FloatField()
    p_3 = FloatField()
    p_4 = FloatField()
    p_5 = FloatField()
    p_6 = FloatField()
    p_7 = FloatField()
    p_8 = FloatField() # Flow sensor

    # Backreference to the CryogenicsDataPoint model (this way we can have many datapoints to one step)
    cryo_data_point = ForeignKeyField(CryogenicsDataPoint, backref='pressures')


class TemperatureDataPoint(DBModel):
    # Upper HEx
    t_0 = FloatField()

    # Lower HEx
    t_1 = FloatField()

    # He Pot
    t_2 = FloatField()

    # 1st stage
    t_3 = FloatField()

    # 2nd stage
    t_4 = FloatField()

    # Inner coil
    t_5 = FloatField()

    # Outer coil
    t_6 = FloatField()

    # Switch
    t_7 = FloatField()

    # He pot
    t_8  = FloatField()

    # Backreference to the CryogenicsDataPoint model
    cryo_data_point = ForeignKeyField(CryogenicsDataPoint, backref='temperatures')

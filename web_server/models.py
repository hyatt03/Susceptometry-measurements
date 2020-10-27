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


# Sessions table
class Session(Model):
    class Meta:
        database = db

    idn = CharField(max_length=50)
    sid = CharField(max_length=50)
    type = CharField(max_length=10)


# Configure experiments
class ExperimentConfiguration(Model):
    class Meta:
        database = db

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


# Experiment steps (Generated from ExperimentConfiguration)
class ExperimentStep(Model):
    class Meta:
        database = db

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

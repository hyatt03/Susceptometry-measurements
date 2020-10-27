def get_default_experiment_configuration():
    return {
        # sr830 configuration
        'sr830_sensitivity': 1e-6,
        'sr830_frequency': 1000.0,
        'sr830_buffersize': 256,

        # N9310A configuration
        'n9310a_min_frequency': 1000.0,
        'n9310a_max_frequency': 1000.0,
        'n9310a_min_amplitude': 0.5,
        'n9310a_max_amplitude': 0.5,
        'n9310a_sweep_steps': 1,

        # Cryonics magnet configuration
        'magnet_min_field': 5.0,
        'magnet_max_field': 6.0,
        'magnet_sweep_steps': 10,

        # Analog Discovery 2 configuration
        'oscope_resistor': 1.0,

        # Data collection options
        'data_wait_before_measuring': 1.0,
        'data_points_per_measurement': 10,
    }

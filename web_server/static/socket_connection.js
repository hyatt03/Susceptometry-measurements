// Create a state tree to contain page state
const state = {
    'temperature_trace_plot_data': [],
    'temperature_plot_layout': 0,
    'last_temperature_update': 1603707641.0,
    'magnet_trace_plot_data': [],
    'magnet_trace_plot_layout': 0,
    'pressure_trace_plot_data': [],
    'pressure_trace_plot_layout': 0,
    'temperatures': {
        't_1st_stage': 0.0,
        't_2nd_stage': 0.0,
        't_he_pot': 0.0,
        't_he_pot_2': 0.0,
        't_inner_coil': 0.0,
        't_lower_hex': 0.0,
        't_outer_coil': 0.0,
        't_switch': 0.0,
        't_upper_hex': 0.0,
        'timestamp': 0
    },
    'pressures': {
        'p_1': 0.0,
        'p_2': 0.0,
        'p_3': 0.0,
        'p_4': 0.0,
        'p_5': 0.0,
        'p_6': 0.0,
        'p_7': 0.0,
        'p_8': 0.0
    },
    'ac_field': 0.0,
    'dc_field': 0.0,
    'n_points_taken': 0,
    'n_points_total': 0,
    'experiment_config': {
        'sr830_sensitivity': 1e-6,
        'sr830_frequency': 256,
        'sr830_buffersize': 256,
        'n9310a_min_frequency': 1000.0,
        'n9310a_max_frequency': 1000.0,
        'n9310a_min_amplitude': 0.5,
        'n9310a_max_amplitude': 0.5,
        'n9310a_sweep_steps': 1,
        'magnet_min_field': 0.0,
        'magnet_max_field': 0.0,
        'magnet_sweep_steps': 1,
        'data_wait_before_measuring': 1.0,
        'data_points_per_measurement': 10,
    }
};

// Have a list of the temperature labels
// simplifies the functions that require this information
const t_labels = ['t_upper_hex', 't_lower_hex', 't_he_pot', 't_1st_stage', 't_2nd_stage', 
                            't_inner_coil', 't_outer_coil', 't_switch', 't_he_pot_2']

// Here is the main entrypoint to the web application
// It is here we open a connection to the server and configure all the endpoints
function main_socket_connection() {
    // Open a socket connection
    var socket = io('/browser');

    // Set it to the window, so we can access it easily during debugging
    window.my_socket = socket;

    // Set pagehandlers to window
    window.pagehandlers = {
        status_page: open_status_page,
        experiment_config: open_experiment_config_page,
        info_page: open_info_page,
        cryo_page: open_cryogenics_page,
        data_page: open_data_page
    };

    // Setup events
    // Get events
    socket.on('connect', idn_requested);
    socket.on('number_of_client', n_connected_updated);
    socket.on('b_temperatures', temperatures_updated);
    socket.on('b_pressures', pressures_updated);
    socket.on('b_dc_field', dc_field_updated);
    socket.on('b_ac_field', ac_field_updated);
    socket.on('b_n_points_taken', n_points_taken_updated);
    socket.on('b_n_points_total', n_points_total_updated);
    socket.on('b_rms', rms_updated);
    socket.on('b_magnet_trace', magnet_trace_updated);
    socket.on('b_temperature_trace', temperature_trace_updated);
    socket.on('b_pressure_trace', pressure_trace_updated);
    socket.on('b_latest_experiment_config', experiment_config_updated);
    socket.on('b_got_cryo_status', cryo_status_updated);
    socket.on('b_got_experiment_list', got_experiment_list);

    // Open status page by default
    open_status_page();

    // Request fresh data stats every 5 seconds
    setInterval(update_data_status, 5000);
}

// Entrypoint, is called on document ready event
$(function () {
    // Establish connection
    main_socket_connection();
});

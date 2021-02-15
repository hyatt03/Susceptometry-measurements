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
        't_still': 0.0,
        't_1': 0.0,
        't_2': 0.0,
        't_3': 0.0,
        't_4': 0.0,
        't_5': 0.0,
        't_6': 0.0,
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
        'sr830_frequency': 1000.0,
        'sr830_buffersize': 256,
        'n9310a_min_frequency': 1000.0,
        'n9310a_max_frequency': 1000.0,
        'n9310a_min_amplitude': 0.5,
        'n9310a_max_amplitude': 0.5,
        'n9310a_sweep_steps': 1,
        'magnet_min_field': 5.0,
        'magnet_max_field': 6.0,
        'magnet_sweep_steps': 10,
        'oscope_resistor': 1.0,
        'data_wait_before_measuring': 1.0,
        'data_points_per_measurement': 10,
    }
};

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
    };

    // Setup events
    // Get events
    socket.on('idn', idn_requested);
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

    // Open status page by default
    open_status_page();

    // Request fresh data stats every 5 seconds
    setInterval(update_data_status, 5000);
}

// Event handler for server requesting idn
function idn_requested() {
    // Grab the socket connection
    const socket = window.my_socket;

    // Grab the idn from users cookies
    let idn = Cookies.get('idn');

    // Check if it exists already, if not we create a new one
    if (typeof (idn) === 'undefined') {
        idn = `webbrowser_${socket.id}`;
        Cookies.set('idn', idn, {'SameSite': 'Strict'});
    }

    // Send the idn back to the server
    socket.emit('idn', idn);
}

function update_data_status() {
    update_n_points_taken();
    update_n_points_total();
}

function update_status_state_tree() {
    update_temperatures();
    update_ac_field();
    update_dc_field();
    update_data_status();
}

function update_temperatures() {
    // Request an update for the temperatures
    window.my_socket.emit('b_get_temperatures');
}

function update_dc_field() {
    // Request an update for the dc field
    window.my_socket.emit('b_get_dc_field');
}

function update_ac_field() {
    // Request an update for the ac field
    window.my_socket.emit('b_get_ac_field');
}

function update_n_points_taken() {
    // Request an update for the number of points taken
    window.my_socket.emit('b_get_n_points_taken');
}

function update_n_points_total() {
    // Request an update for the number of points total
    window.my_socket.emit('b_get_n_points_total');
}

function update_rms() {
    // Request an update for the rms
    window.my_socket.emit('b_get_rms');
}

function update_magnet_trace() {
    // Request an update for the magnet trace
    window.my_socket.emit('b_get_magnet_trace');
}

function update_temperature_trace() {
    // Request an update for the temperature trace
    window.my_socket.emit('b_get_temperature_trace');
}

function update_pressure_trace() {
    // Request an update for the pressure trace
    window.my_socket.emit('b_get_pressure_trace');
}

function update_experiment_config() {
    window.my_socket.emit('b_get_latest_experiment_config');
}

function temperatures_updated(temperatures) {
    if (typeof temperatures !== 'undefined') {
        state['temperatures']['t_still'] = temperatures['t_still'];
        state['temperatures']['t_1'] = temperatures['t_1'];
        state['temperatures']['t_2'] = temperatures['t_2'];
        state['temperatures']['t_3'] = temperatures['t_3'];
        state['temperatures']['t_4'] = temperatures['t_4'];
        state['temperatures']['t_5'] = temperatures['t_5'];
        state['temperatures']['t_6'] = temperatures['t_6'];
        state['temperatures']['last_update'] = temperatures['timestamp'];
    }

    // Update the temperatures if they exist
    const tc = $('.temperature--container');

    // Next we append the new temperatures to the data
    if (state['temperature_trace_plot_data'].length > 0 && state['temperature_plot_layout'] !== 0) {
        if (typeof temperatures !== 'undefined') {
            // Add new data
            state['temperature_trace_plot_data'][0].x.push(temperatures['timestamp']);
            state['temperature_trace_plot_data'][0].y.push(temperatures['t_still']);

            for (let i = 1; i < 7; i++) {
                state['temperature_trace_plot_data'][i].x.push(temperatures['timestamp']);
                state['temperature_trace_plot_data'][i].y.push(temperatures['t_' + i]);
            }

            // Ensure length is at max 20 items
            if (state['temperature_trace_plot_data'][0].x.length > 20) {
                for (let i = 0; i < 7; i++) {
                    state['temperature_trace_plot_data'][i].x.shift();
                    state['temperature_trace_plot_data'][i].y.shift();
                }
            }

            // Update data revision and range
            state['temperature_plot_layout']['datarevision'] += 1;
            state['temperature_plot_layout']['xaxis.range'] = [
                state['temperature_trace_plot_data'][0].x[0],
                state['temperature_trace_plot_data'][0].x[-1]
            ];
        }

        if (tc.length > 0) {
            tc.html(get_temperature_list(state));
            Plotly.react('temperature-plot', state['temperature_trace_plot_data'], state['temperature_plot_layout']);
        }
    }
    else if (tc.length > 0) {
        // Otherwise we just update the whole page
        state['current_page'](false);
    }
}

function pressures_updated(pressures) {
    if (typeof pressures !== 'undefined') {
        state['pressures']['p_1'] = pressures['p_1'];
        state['pressures']['p_2'] = pressures['p_2'];
        state['pressures']['p_3'] = pressures['p_3'];
        state['pressures']['p_4'] = pressures['p_4'];
        state['pressures']['p_5'] = pressures['p_5'];
        state['pressures']['p_6'] = pressures['p_6'];
        state['pressures']['p_7'] = pressures['p_7'];
        state['pressures']['p_8'] = pressures['p_8'];
        state['pressures']['last_update'] = pressures['timestamp'];
    }

    // Update the temperatures if they exist
    const tc = $('.pressure--container');

    // Next we append the new temperatures to the data
    if (state['pressure_trace_plot_data'].length > 0 && state['pressure_plot_layout'] !== 0) {
        if (typeof pressures !== 'undefined') {
            // Add new data
            for (let i = 0; i < 8; i++) {
                state['pressure_trace_plot_data'][i].x.push(pressures['timestamp']);
                state['pressure_trace_plot_data'][i].y.push(pressures['p_' + (i + 1)]);
            }

            // Ensure length is at max 20 items
            if (state['pressure_trace_plot_data'][0].x.length > 20) {
                for (let i = 0; i < 8; i++) {
                    state['pressure_trace_plot_data'][i].x.shift();
                    state['pressure_trace_plot_data'][i].y.shift();
                }
            }

            // Update data revision and range
            state['pressure_plot_layout']['datarevision'] += 1;
            state['pressure_plot_layout']['xaxis.range'] = [
                state['pressure_trace_plot_data'][0].x[0],
                state['pressure_trace_plot_data'][0].x[-1]
            ];
        }

        if (tc.length > 0) {
            tc.html(get_pressure_list(state));
            Plotly.react('pressure-plot', state['pressure_trace_plot_data'], state['pressure_plot_layout']);
        }
    }
    else if (tc.length > 0) {
        // Otherwise we just update the pressure list container
        tc.html(get_pressure_list(state));
    }
}

function update_magnet_state() {
    const rms_container = $('.magnet-field-value--container');
    if (rms_container.length > 0) {
        rms_container.html(get_magnet_field_list(state));
    }
}

function dc_field_updated(fieldstrength) {
    state['dc_field'] = fieldstrength;
    update_magnet_state();
}

function ac_field_updated(fieldstrength) {
    state['ac_field'] = fieldstrength;
    update_magnet_state();
}

function update_data_status_values() {
    const take_container = $('#data--container--take');
    const remain_container = $('#data--container--remaining');
    const total_container = $('#data--container--total');

    if (take_container.length > 0) {
        take_container.html(state['n_points_taken']);
    }

    if (remain_container.length > 0) {
        remain_container.html(state['n_points_total'] - state['n_points_taken']);
    }

    if (total_container.length > 0) {
        total_container.html(state['n_points_total']);
    }
}

function n_points_taken_updated(n_points_taken) {
    state['n_points_taken'] = n_points_taken;
    update_data_status_values();
}

function n_points_total_updated(n_points_total) {
    state['n_points_total'] = n_points_total;
    update_data_status_values();
}

function rms_updated(b_rms) {
    state['b_rms'] = b_rms;
    update_magnet_state();
}

function magnet_trace_updated(magnet_trace) {
    const trace_node = $('#magnet-plot');

    // Update the plot
    if (state['magnet_trace_plot_data'].length > 0) {
        // Set a new data revision
        state['magnet_trace_plot_layout']['datarevision'] += 1;

        // Change the data
        state['magnet_trace_plot_data'][0].x = magnet_trace['times'];
        state['magnet_trace_plot_data'][0].y = magnet_trace['magnet_trace'];

        // Update the plot
        if (trace_node.length > 0) {
            Plotly.react('magnet-plot', state['magnet_trace_plot_data'], state['magnet_trace_plot_layout']);
        }
    } else {
        // Plot for the first time
        // First create the layout
        state['magnet_trace_plot_layout'] = {
            title: 'Magnetic field strength over time (small magnet)',
            datarevision: 0,
            xaxis: {
                title: 'Time [Seconds]',
                showgrid: false,
                zeroline: true
            },
            yaxis: {
                title: 'Field strength [Tesla]',
                showline: false,
                zeroline: true
            }
        }

        // Then we setup the data
        state['magnet_trace_plot_data'] = [{
            x: magnet_trace['times'],
            y: magnet_trace['magnet_trace'],
            mode: 'lines+markers',
            name: 'Total magnetic field strength'
        }]

        // And finally we create a plot
        if (trace_node.length > 0) {
            Plotly.newPlot('magnet-plot', state['magnet_trace_plot_data'], state['magnet_trace_plot_layout']);
        }
    }
}

function temperature_trace_updated(temperature_trace) {
    if (state['temperature_trace_plot_data'].length < 1) {
        // Initialize the data model
        for (let i = 0; i < 7; i++) {
            state['temperature_trace_plot_data'].push({
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'Temperature in probe ' + i
            });
        }

        // Add the datapoints
        for (let i = 0; i < temperature_trace.length; i++) {
            state['temperature_trace_plot_data'][0].x.push(temperature_trace[i]['timestamp']);
            state['temperature_trace_plot_data'][0].y.push(temperature_trace[i]['t_still']);

            for (let j = 1; j < 7; j++) {
                state['temperature_trace_plot_data'][j].x.push(temperature_trace[i]['timestamp'])
                state['temperature_trace_plot_data'][j].y.push(temperature_trace[i]['t_' + j])
            }
        }

        state['temperature_plot_layout'] = {
            datarevision: 0,
            title: 'Temperature over time',
            xaxis: {
                title: 'Time [seconds]',
                showgrid: false,
                zeroline: true
            },
            yaxis: {
                title: 'Temperature [Kelvin]',
                showline: false,
                zeroline: true
            }
        }

        Plotly.newPlot('temperature-plot', state['temperature_trace_plot_data'], state['temperature_plot_layout']);
    }
    else {
        temperatures_updated();
    }
}

function pressure_trace_updated(pressure_trace) {
    if (state['pressure_trace_plot_data'].length < 1) {
        // Initialize the data model
        for (let i = 0; i < 8; i++) {
            state['pressure_trace_plot_data'].push({
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'pressure in probe ' + (i + 1)
            });
        }

        // Add the datapoints
        for (let i = 0; i < pressure_trace.length; i++) {
            for (let j = 0; j < 8; j++) {
                state['pressure_trace_plot_data'][j].x.push(pressure_trace[i]['timestamp'])
                state['pressure_trace_plot_data'][j].y.push(pressure_trace[i]['p_' + (j+1)])
            }
        }

        state['pressure_plot_layout'] = {
            datarevision: 0,
            title: 'Pressure over time',
            xaxis: {
                title: 'Time [seconds]',
                showgrid: false,
                zeroline: true
            },
            yaxis: {
                title: 'Pressure',
                showline: false,
                zeroline: true
            }
        }

        Plotly.newPlot('pressure-plot', state['pressure_trace_plot_data'], state['pressure_plot_layout']);
    }
    else {
        pressures_updated();
    }
}

function experiment_config_updated(config) {
    state.experiment_config = config;
}

function save_experiment_configuration() {
    // Get the experiment config from the form
    experiment_config = {};
    $('#experiment_config_form').serializeArray().forEach(element => {
        experiment_config[element['name']] = element['value'];
    })

    // Send it to the server
    window.my_socket.emit('b_set_experiment_config', experiment_config);
}

function begin_cooldown_procedure() {
    window.my_socket.emit('b_begin_cooldown');
}

function get_cryo_status() {
    window.my_socket.emit('b_get_cryo_status');
}

// Function to setup the DOM to contain the statuspage
function open_status_page(should_update) {
    state['current_page'] = open_status_page;
    $('.content-title').text('Experiment status');
    $('.content-container').html(get_status_template(state));

    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
        update_magnet_trace();
        update_temperature_trace();
    }
}

// Function to setup the DOM to contain the experiment config page
function open_experiment_config_page(should_update) {
    state['current_page'] = open_experiment_config_page;
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
    }

    $('.content-title').text('Experiment configuration');
    $('.content-container').html(get_config_page_template(state));
}

// Function to setup the DOM to contain the info page
function open_info_page() {
    state['current_page'] = open_info_page;

    $('.content-title').text('About this page');
    $('.content-container').html(get_info_page_html());
}

function open_cryogenics_page(should_update) {
    state['current_page'] = open_cryogenics_page;

    $('.content-title').text('Cryogenics configuration');
    $('.content-container').html(get_cryogenics_page_html());

    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
        update_temperature_trace();
        update_pressure_trace();
    }
}

// Entrypoint, is called on document ready event
$(function () {
    // Establish connection
    main_socket_connection();
});

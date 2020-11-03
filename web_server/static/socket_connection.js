// Create a state tree to contain page state
const state = {
    'temperature_trace_plot_data': [],
    'temperature_plot_layout': 0,
    'last_temperature_update': 1603707641.0,
    'magnet_trace_plot_data': [],
    'magnet_trace_plot_layout': 0,
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
        info_page: open_info_page
    };

    // Setup events
    // Get events
    socket.on('idn', idn_requested);
    socket.on('b_temperatures', temperatures_updated);
    socket.on('b_dc_field', dc_field_updated);
    socket.on('b_ac_field', ac_field_updated);
    socket.on('b_n_points_taken', n_points_taken_updated);
    socket.on('b_n_points_total', n_points_total_updated);
    socket.on('b_rms', rms_updated);
    socket.on('b_magnet_trace', magnet_trace_updated);
    socket.on('b_temperature_trace', temperature_trace_updated);
    socket.on('b_latest_experiment_config', experiment_config_updated);

    // Open status page by default
    open_status_page();
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

function update_status_state_tree() {
    update_temperatures();
    update_ac_field();
    update_dc_field();
    update_n_points_taken();
    update_n_points_total();
    update_experiment_config();
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

function dc_field_updated(fieldstrength) {
    state['dc_field'] = fieldstrength;
    state['current_page'](false);
}

function ac_field_updated(fieldstrength) {
    state['ac_field'] = fieldstrength;
    state['current_page'](false);
}

function n_points_taken_updated(n_points_taken) {
    state['n_points_taken'] = n_points_taken;
    state['current_page'](false);
}

function n_points_total_updated(n_points_total) {
    state['n_points_total'] = n_points_total;
    state['current_page'](false);
}

function rms_updated(b_rms) {
    state['b_rms'] = b_rms;
    state['current_page'](false);
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

// Entrypoint, is called on document ready event
$(function () {
    // Establish connection
    main_socket_connection();
});

// Create a state tree to contain page state
const state = {
    'last_update': 1603707641.0,
    't_still': 0.0,
    't_1': 0.0,
    't_2': 0.0,
    't_3': 0.0,
    't_4': 0.0,
    't_5': 0.0,
    't_6': 0.0,
    'ac_field': 0.0,
    'dc_field': 0.0,
    'n_points_taken': 0,
    'n_points_total': 0
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

function temperatures_updated(temperatures) {
    state['t_still'] = temperatures['t_still'];
    state['t_1'] = temperatures['t_1'];
    state['t_2'] = temperatures['t_2'];
    state['t_3'] = temperatures['t_3'];
    state['t_4'] = temperatures['t_4'];
    state['t_5'] = temperatures['t_5'];
    state['t_6'] = temperatures['t_6'];
    state['last_update'] = temperatures['timestamp'];
    state['current_page'](false);
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
    Plotly.newPlot('magnet-plot', [{
        x: magnet_trace['times'],
        y: magnet_trace['magnet_trace'],
        mode: 'lines+markers',
        name: 'Total magnetic field strength'
    }], {
        title: 'Magnetic field strength over time',
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
    });
}

function temperature_trace_updated(temperature_trace) {
    var data = [{
        x: temperature_trace['times'],
        y: temperature_trace['t_still'],
        mode: 'lines+markers',
        name: 'Temperature in still'
    }];

    for (i=1; i<7; i++) {
        data.push({
            x: temperature_trace['times'],
            y: temperature_trace['t_' + i],
            mode: 'lines+markers',
            name: 'Temperature in probe ' + i
        })
    }

    Plotly.newPlot('temperature-plot', data, {
        title: 'Temperature over time',
        xaxis: {
            title: 'Time [Hours]',
            showgrid: false,
            zeroline: true
        },
        yaxis: {
            title: 'Temperature [Kelvin]',
            showline: false,
            zeroline: true
        }
    });
}

// Function to setup the DOM to contain the statuspage
function open_status_page(should_update) {
    state['current_page'] = open_status_page;
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
        update_magnet_trace();
        update_temperature_trace();
    }

    $('.content-title').text('Experiment status');
    $('.content-container').html(get_status_template(state));
}

// Function to setup the DOM to contain the experiment config page
function open_experiment_config_page(should_update) {
    state['current_page'] = open_experiment_config_page;
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
    }

    $('.content-title').text('Experiment configuration');
    $('.content-container').html(get_config_page_template());
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

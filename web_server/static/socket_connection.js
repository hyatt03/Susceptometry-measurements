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
    var socket = io();

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

function update_state_tree() {
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

// Function to setup the DOM to contain the statuspage
function open_status_page(should_update) {
    state['current_page'] = open_status_page;
    if (typeof(should_update) === 'undefined') {
        update_state_tree();
    }

    $('.content-title').text('Experiment status').attr('id', 'status');
    $('.content-container').html(`
<div class="cryogenics_status status_container">
    <h1 class="h4">Cryogenics status</h1>
    <div>t_still = ${state['t_still']}K</div>
    <div>t_1 = ${state['t_1']}K</div>
    <div>t_2 = ${state['t_2']}K</div>
    <div>t_3 = ${state['t_3']}K</div>
    <div>t_4 = ${state['t_4']}K</div>
    <div>t_5 = ${state['t_5']}K</div>
    <div>t_6 = ${state['t_6']}K</div>
</div>

<div class="magnets_status status_container">
    <h1 class="h4">Magnet status</h1>
    <div>B_large = ${state['dc_field']}T</div>
    <div>B_small = ${state['ac_field']}T</div>
</div>

<div class="datapoints_status status_container">
    <h1 class="h4">Data status</h1>
    <div>Number of datapoints taken = ${state['n_points_taken']}</div>
    <div>Number of datapoints remaining = ${state['n_points_total'] - state['n_points_taken']}</div>
    <div>Number of datapoints total = ${state['n_points_total']}</div>
</div>
    `);
}

// Function to setup the DOM to contain the experiment config page
function open_experiment_config_page(should_update) {
    state['current_page'] = open_experiment_config_page;
    if (typeof(should_update) === 'undefined') {
        update_state_tree();
    }

    $('.content-title').text('Experiment configuration').attr('id', 'config');
    $('.content-container').html(`
    Configure the experiment here!
    `);
}

// Function to setup the DOM to contain the info page
function open_info_page(should_update) {
    state['current_page'] = open_info_page;
    if (typeof(should_update) === 'undefined') {
        update_state_tree();
    }

    $('.content-title').text('About this page').attr('id', 'about');
    $('.content-container').html(`
    This page was made for a thesis
    `);
}

// Entrypoint, is called on document ready event
$(function () {
    // Establish connection
    main_socket_connection();
});

/**
 * Here we have socket emitters
 * They are our primary way of communicating with the backend
 * They are typically called through button presses
 */

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

function update_n_connections() {
    window.my_socket.emit('get_number_of_clients');
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

function get_experiments_list(page) {
    window.my_socket.emit('b_get_experiment_list', {page: page});
}

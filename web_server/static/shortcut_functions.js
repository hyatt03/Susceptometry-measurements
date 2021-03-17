/**
 * Here we have shortcut functions
 * They just call a common collection of functions
 */

// We want to grab both the number of points collected
// And the total number of points we're going for right now
function update_data_status() {
    update_n_connections();
    update_n_points_taken();
    update_n_points_total();
}

// Update the remaining data stuff
function update_status_state_tree() {
    update_temperatures();
    update_ac_field();
    update_dc_field();
    update_data_status();
}

// Shortcut function to change the html of the magnet field list
function update_magnet_state() {
    const rms_container = $('.magnet-field-value--container');
    if (rms_container.length > 0) {
        rms_container.html(get_magnet_field_list(state));
    }
}

// Shortcut function to update the data status values
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

/***
 * Here we begin the page handlers (views essentially)
 * They link the templates to the actual page
 */

// Function to setup the DOM to contain the statuspage
function open_status_page(should_update) {
    // Update the state
    state['current_page'] = open_status_page;

    // Set the title and the html content
    $('.content-title').text('Experiment status');
    $('.content-container').html(get_status_template(state));

    // Grab the status state, the magnet trace, and a temperature trace
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
        update_magnet_trace();
        update_temperature_trace();
    }
}

// Function to setup the DOM to contain the experiment config page
function open_experiment_config_page(should_update) {
    // Update the state
    state['current_page'] = open_experiment_config_page;

    // Update the status state
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
    }

    // Set the title and the html content
    $('.content-title').text('Experiment configuration');
    $('.content-container').html(get_config_page_template(state));
}

// Function to setup the DOM to contain the info page
function open_info_page() {
    // Update the state
    state['current_page'] = open_info_page;

    // Set the title and the html content
    $('.content-title').text('About this page');
    $('.content-container').html(get_info_page_html());
}

function open_cryogenics_page(should_update) {
    // Update the state
    state['current_page'] = open_cryogenics_page;

    // Set the title and the html content
    $('.content-title').text('Cryogenics configuration');
    $('.content-container').html(get_cryogenics_page_html());

    // Grab the status, the temperature trace, and the pressure trace
    if (typeof (should_update) === 'undefined') {
        update_status_state_tree();
        update_temperature_trace();
        update_pressure_trace();
    }
}

// Function to setup the DOM to contain the info page
function open_data_page(should_update) {
    // Update the state
    state['current_page'] = open_data_page;

    // Set the title and the html content
    $('.content-title').text('Data management');
    $('.content-container').html(get_data_page_html());

    // Grab the first page of experiments
    if (typeof (should_update) === 'undefined') {
        get_experiments_list(1);
    }
}

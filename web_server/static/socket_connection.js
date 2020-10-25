function main_socket_connection() {
    // Open a socket connection
    var socket = io();

    // Set it to the window, so we can access it easily during debugging
    window.my_socket = socket;

    // Setup events

    // Open status page by default
    window.pagehandlers['status_page']();
}

function open_status_page() {
    $('.content-title').text('Experiment status');
    $('.content-container').html(`
    View the progress here
    `);
}

function open_experiment_config_page() {
    $('.content-title').text('Experiment configuration');
    $('.content-container').html(`
    Configure the experiment here!
    `);
}

function open_info_page() {
    $('.content-title').text('About this page');
    $('.content-container').html(`
    This page was made for a thesis
    `);
}

$(function() {
    // Set pagehandlers to window
    window.pagehandlers = {
        status_page: open_status_page,
        experiment_config: open_experiment_config_page,
        info_page: open_info_page
    };

    // Establish connection
    main_socket_connection();
});

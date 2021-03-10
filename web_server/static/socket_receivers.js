/**
 * Here we have event handlers, they respond to events sent from the server to the website
 * They are the main way of getting data onto the website
 */

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

// Received as a response when we want to know the status of the GHS
function cryo_status_updated(status) {
    $('#cryo_ack').html('Latest ack: ' + status['ack']);
    $('#cryo_status').html('Status: ' + status['status']);
}

// When the cryo client is running we get an update on all the temperatures every 5 seconds
// This endpoint plots the temperatures and updates the list of the current temperatures
function temperatures_updated(temperatures) {
    if (typeof temperatures !== 'undefined') {
        for (var i = 0; i < t_labels.length; i++) {
            state['temperatures'][t_labels[i]] = temperatures[t_labels[i]];
        }
    }

    // Update the temperatures if they exist
    const tc = $('.temperature--container');

    // Next we append the new temperatures to the data
    if (state['temperature_trace_plot_data'].length > 0 && state['temperature_plot_layout'] !== 0) {
        if (typeof temperatures !== 'undefined') {
            // Add new data to the state
            for (let i = 0; i < 9; i++) {
                state['temperature_trace_plot_data'][i].x.push(temperatures['timestamp']);
                state['temperature_trace_plot_data'][i].y.push(temperatures[t_labels[i]]);
            }

            // Ensure length is at max 20 items
            if (state['temperature_trace_plot_data'][0].x.length > 20) {
                for (let i = 0; i < 9; i++) {
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

// Creates a pressure plot similar to the temperature plot
// The pressure data comes from the GHS
function pressures_updated(pressures) {
    if (typeof pressures !== 'undefined') {
        for (var i=0; i<9; i++) {
            state['pressures']['p_' + i] = pressures['p_' + i];
        }

        state['pressures']['last_update'] = pressures['timestamp'];
    }

    // Update the pressures if they exist
    const tc = $('.pressure--container');

    // Next we append the new pressures to the data
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

// Gets the DC field from the server and displays it on the screen
function dc_field_updated(fieldstrength) {
    state['dc_field'] = fieldstrength;
    update_magnet_state();
}

// Gets the AC rms field from the server and displays it on the screen
function ac_field_updated(fieldstrength) {
    state['ac_field'] = fieldstrength;
    update_magnet_state();
}

// Server sends number of datapoints collected in the current experiment
// We display it on screen
function n_points_taken_updated(n_points_taken) {
    state['n_points_taken'] = n_points_taken;
    update_data_status_values();
}

// Server sends the total number of datapoints we want in this experiment run
// We display it
function n_points_total_updated(n_points_total) {
    state['n_points_total'] = n_points_total;
    update_data_status_values();
}

// Server sends the AC rms field, we save it and display it
function rms_updated(b_rms) {
    state['b_rms'] = b_rms;
    update_magnet_state();
}

// Server sends a magnet trace, we plot the trace
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

// Server sends a temperature trace, we plot the trace
// This is usually only called when we go to a page with a temperature plot, and only once
function temperature_trace_updated(temperature_trace) {
    if (state['temperature_trace_plot_data'].length < 1) {
        // Initialize the data model
        for (let i = 0; i < 9; i++) {
            state['temperature_trace_plot_data'].push({
                x: [],
                y: [],
                mode: 'lines+markers',
                name: t_labels[i]
            });
        }

        // Add the datapoints
        for (let i = 0; i < temperature_trace.length; i++) {
            for (let j = 0; j < 9; j++) {
                state['temperature_trace_plot_data'][j].x.push(temperature_trace[i]['timestamp']);
                state['temperature_trace_plot_data'][j].y.push(temperature_trace[i][t_labels[j]]);
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

// Server sends a pressure trace, we plot the trace
// This is usually only called when we go to a page with a pressure plot, and only once
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

// Server sends the latest experiment config
// We use it as a starting point for our next experiment config
function experiment_config_updated(config) {
    state.experiment_config = config;
}

// Server sends a list of experiments
// We use it to populate a table of data on the data management page
function got_experiment_list(data) {
    // If there's data, we want to show it, otherwise we show an error message
    if (data.count < 1) {
        $('#datatable_wrapper').html('No experiments have been configured.');
    } else {
        $('#datatable_wrapper').html(get_data_table_html(data));
    }
}

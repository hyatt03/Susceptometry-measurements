function get_temperature_list(state) {
    return `
        <div>Current temperatures: </div>
        <div class="temperature--label">t_upper_hex = ${state['temperatures']['t_upper_hex']}K</div>
        <div class="temperature--label">t_lower_hex = ${state['temperatures']['t_lower_hex']}K</div>
        <div class="temperature--label">t_he_pot = ${state['temperatures']['t_he_pot']}K</div>
        <div class="temperature--label">t_1st_stage = ${state['temperatures']['t_1st_stage']}K</div>
        <div class="temperature--label">t_2nd_stage = ${state['temperatures']['t_2nd_stage']}K</div>
        <div class="temperature--label">t_inner_coil = ${state['temperatures']['t_inner_coil']}K</div>
        <div class="temperature--label">t_outer_coil = ${state['temperatures']['t_outer_coil']}K</div>
        <div class="temperature--label">t_switch = ${state['temperatures']['t_switch']}K</div>
        <div class="temperature--label">t_he_pot_2 = ${state['temperatures']['t_he_pot_2']}K</div>`;
}

function get_magnet_field_list(state) {
    return `
        <div>Current field</div>
        <div class="magnet-field-value--label">B_large = ${state['dc_field']}T</div>
        <div class="magnet-field-value--label">B_small = ${state['ac_field']}T</div>`;
}

function get_pressure_list(state) {
    return `
    <div>Current Pressures</div>
    <div class="pressure--label">p_1 = ${state['pressures']['p_1']}</div>
    <div class="pressure--label">p_2 = ${state['pressures']['p_2']}</div>
    <div class="pressure--label">p_3 = ${state['pressures']['p_3']}</div>
    <div class="pressure--label">p_4 = ${state['pressures']['p_4']}</div>
    <div class="pressure--label">p_5 = ${state['pressures']['p_5']}</div>
    <div class="pressure--label">p_6 = ${state['pressures']['p_6']}</div>
    <div class="pressure--label">p_7 = ${state['pressures']['p_7']}</div>
    <div class="pressure--label">p_8 = ${state['pressures']['p_8']}</div>
    `;
}

function get_temperature_plot(state) {
    return `
<div class="cryogenics_status status_container">
    <h1 class="h4">Cryogenics status</h1>
    <div class="status_contents plot_container row">
        <div class="temperature-plot--container col-9" id="temperature-plot"></div>
        <div class="temperature--container col-3">
            ${get_temperature_list(state)}
        </div>
    </div>
</div>
`
}

// Simple function to return status page html given the state
function get_status_template(state) {
    return `
${get_temperature_plot(state)}

<div class="magnets_status status_container">
    <h1 class="h4">Magnet status</h1>
    <div class="status_contents plot_container row">
        <div class="magnet-plot--container col-9" id="magnet-plot"></div>
        <div class="magnet-field-value--container col-3">
            ${get_magnet_field_list(state)}
        </div>
    </div>
</div>

<div class="datapoints_status status_container">
    <h1 class="h4">Data status</h1>
    <div class="status_contents">
        <div class="datapoints-status--container">
            <div>Number of datapoints taken = <span id="data--container--take">${state['n_points_taken']}</span></div>
            <div>Number of datapoints remaining = <span id="data--container--remaining">${state['n_points_total'] - state['n_points_taken']}</span></div>
            <div>Number of datapoints total = <span id="data--container--total">${state['n_points_total']}</span></div>        
        </div>
    </div>
</div>
    `
}

// Get the configuration page
const sr830_frequencies = [0.0625, 0.125, 0.25, 0.5, 1., 2., 4., 8., 16., 32., 64., 128., 256., 512.]
const sr830_sensitivities = [2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6,
    20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1]

function get_config_page_template(state) {
    const experiment_config = state['experiment_config'];
    const sr830_sensitivity_options = sr830_sensitivities.map(sens => {
        let is_default = '';
        if (sens === experiment_config['sr830_sensitivity']) {
            is_default = 'selected="selected"'
        }

        return `<option value="${sens}" ${is_default}>${sens}V</option>`
    });

    return `
<form id="experiment_config_form">
    <div class="instrument--container">
        <h1 class="h4">Data collection options</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="data_wait_before_measure">Select wait time before measuring [s]: </label>
                <input type="number" name="data_wait_before_measuring" id="data_wait_before_measure" 
                       placeholder="Wait time" value="${experiment_config['data_wait_before_measuring']}" />
            </div>
            
            <div class="config--parameter">
                <label for="data_points_per_measure">Select number of points per measurement: </label>
                <input type="number" name="data_points_per_measurement" id="data_points_per_measure" 
                       placeholder="Datapoints per measurement" 
                       value="${experiment_config['data_points_per_measurement']}" />
            </div>
        </div>
    </div>

    <div class="instrument--container">
        <h1 class="h4">Lock-in amplifier (SR830) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="sr830_sensitivity">Select sensitivity [V]: </label>
                <select name="sr830_sensitivity" id="sr830_sensitivity">${sr830_sensitivity_options}</select>
            </div>
            
            <div class="config--parameter">
                <label for="sr830_freq">Frequency [Hz]: </label>
                <input type="number" placeholder="Frequency" name="sr830_frequency" 
                       id="sr830_freq" value="${experiment_config['sr830_frequency']}" />
            </div>
            
            <div class="config--parameter">
                <label for="sr830_buffersize">Buffer size: </label>
                <input type="number" placeholder="size" name="sr830_buffersize" 
                       id="sr830_buffersize" value="${experiment_config['sr830_buffersize']}" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Signal generator (N9310A) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="n9310a_freq_min">Select minimum frequency [Hz]: </label>
                <input type="number" placeholder="Minimum frequency" name="n9310a_min_frequency" 
                       id="n9310a_freq_min" value="${experiment_config['n9310a_min_frequency']}" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_freq_max">Select maximum frequency [Hz]: </label>
                <input type="number" placeholder="Maximum frequency" name="n9310a_max_frequency" 
                       id="n9310a_freq_max" value="${experiment_config['n9310a_max_frequency']}" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_min_amplitude">Select minimum Amplitude [V]: </label>
                <input type="number" placeholder="Amplitude" name="n9310a_min_amplitude" 
                       id="n9310a_min_amplitude" value="${experiment_config['n9310a_min_amplitude']}" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_max_amplitude">Select maximum Amplitude [V]: </label>
                <input type="number" placeholder="Amplitude" name="n9310a_max_amplitude" 
                       id="n9310a_max_amplitude" value="${experiment_config['n9310a_max_amplitude']}" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_n_sweep_points">Select number of sweep points: </label>
                <input type="number" placeholder="Sweep points" name="n9310a_sweep_steps" 
                       id="n9310a_n_sweep_points" value="${experiment_config['n9310a_sweep_steps']}" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Cryonics magnet configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="dc_field_strength_min">Select minimum fieldstrength [T]: </label>
                <input type="number" name="magnet_min_field" id="dc_field_strength_min" 
                       placeholder="B-Field" value="${experiment_config['magnet_min_field']}" />
            </div>
            
            <div class="config--parameter">
                <label for="dc_field_strength_max">Select maximum fieldstrength [T]: </label>
                <input type="number" name="magnet_max_field" id="dc_field_strength_max" 
                       placeholder="B-Field" value="${experiment_config['magnet_max_field']}" />
            </div>
            
            <div class="config--parameter">
                <label for="dc_field_n_sweep_points">Select number of sweep points: </label>
                <input type="number" placeholder="Sweep points" name="magnet_sweep_steps" 
                       id="dc_field_n_sweep_points" value="${experiment_config['magnet_sweep_steps']}" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Oscilloscope (Analog discovery 2) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="oscope_resistor">Select resistor value [Ω]: </label>
                <input type="number" name="oscope_resistor" id="oscope_resistor" 
                       placeholder="Resistor" value="${experiment_config['oscope_resistor']}" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Save experiment configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                Warning: Pressing this buttion will stop any current run, 
                overwrite the experiment configuration, and start a new run.
            </div>
            <div class="config--parameter">
                <input type="button" value="Save experiment configuration" class="save_config_button"
                       name="save_experiment" onclick="save_experiment_configuration()">
            </div>
        </div>
    </div>
</form>
    `
}

function get_cryogenics_page_html() {
    return `
    <div class="cryogenics_status status_container">
        <h1 class="h4">Instrument status and latest ack</h1>
        <div class="status_contents row">
            <div class="status-ack--container col-3">
                <div>stat</div>
                <div>ack</div>
            </div>
        </div>
    </div>
    
    <form id="cryo_config_form" class="cooldown_form">
        <div class="instrument--container">
            <div class="instrument--config">
                <div class="config--parameter">
                    <input type="button" value="Get status" 
                           name="df_auto_cool" onclick="get_cryo_status()">
                    <input type="button" value="Begin automatic cooldown" 
                           name="df_auto_cool" onclick="begin_cooldown_procedure()">
                </div>
            </div>
        </div>
    </form>
    
    ${get_temperature_plot(state)}
    
    <div class="cryogenics_status status_container">
        <h1 class="h4">Pressures</h1>
        <div class="status_contents plot_container row">
            <div class="pressure-plot--container col-9" id="pressure-plot"></div>
            <div class="pressure--container col-3">
                ${get_pressure_list(state)}
            </div>
        </div>
    </div>
    `
}

function get_info_page_html() {
    return `
    This page was made for a thesis
    `
}

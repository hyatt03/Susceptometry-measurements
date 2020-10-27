// Simple function to return status page html given the state
function get_status_template(state) {
    return `
<div class="cryogenics_status status_container">
    <h1 class="h4">Cryogenics status</h1>
    <div class="status_contents row">
        <div class="temperature-plot--container col-9" id="temperature-plot"></div>
        <div class="temperature--container col-3">
            <div>Current temperatures: </div>
            <div class="temperature--label">t_still = ${state['t_still']}K</div>
            <div class="temperature--label">t_1 = ${state['t_1']}K</div>
            <div class="temperature--label">t_2 = ${state['t_2']}K</div>
            <div class="temperature--label">t_3 = ${state['t_3']}K</div>
            <div class="temperature--label">t_4 = ${state['t_4']}K</div>
            <div class="temperature--label">t_5 = ${state['t_5']}K</div>
            <div class="temperature--label">t_6 = ${state['t_6']}K</div>
        </div>
    </div>
</div>

<div class="magnets_status status_container">
    <h1 class="h4">Magnet status</h1>
    <div class="status_contents row">
        <div class="magnet-plot--container col-9" id="magnet-plot"></div>
        <div class="magnet-field-value--container col-3">
            <div>Current field</div>
            <div class="magnet-field-value--label">B_large = ${state['dc_field']}T</div>
            <div class="magnet-field-value--label">B_small = ${state['ac_field']}T</div>
        </div>
    </div>
</div>

<div class="datapoints_status status_container">
    <h1 class="h4">Data status</h1>
    <div class="status_contents">
        <div class="datapoints-status--container">
            <div>Number of datapoints taken = ${state['n_points_taken']}</div>
            <div>Number of datapoints remaining = ${state['n_points_total'] - state['n_points_taken']}</div>
            <div>Number of datapoints total = ${state['n_points_total']}</div>        
        </div>
    </div>
</div>
    `
}

// Get the configuration page
const sr830_sensitivities = [2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6,
    20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1]
function get_config_page_template() {
    const sr830_sensitivity_options = sr830_sensitivities.map(sens => {
       return `<option value="${sens}">${sens}V</option>`
    });

    return `
    <div class="instrument--container">
        <h1 class="h4">Lock-in amplifier (SR830) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="sr830_sensitivity">Select sensitivity [V]: </label>
                <select name="sr830_sensitivity" id="sr830_sensitivity">${sr830_sensitivity_options}</select>
            </div>
            
            <div class="config--parameter">
                <label for="sr830_freq">Frequency [Hz]: </label>
                <input type="number" placeholder="Frequency" name="sr830_freq" id="sr830_freq" />
            </div>
            
            <div class="config--parameter">
                <label for="sr830_buffersize">Buffer size: </label>
                <input type="number" placeholder="size" name="sr830_buffersize" id="sr830_buffersize" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Signal generator (N9310A) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="n9310a_freq_min">Select minimum frequency [Hz]: </label>
                <input type="number" placeholder="Minimum frequency" name="n9310a_freq_min" id="n9310a_freq_min" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_freq_max">Select maximum frequency [Hz]: </label>
                <input type="number" placeholder="Maximum frequency" name="n9310a_freq_max" id="n9310a_freq_max" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_min_amplitude">Select minimum Amplitude [V]: </label>
                <input type="number" placeholder="Amplitude" name="n9310a_min_amplitude" id="n9310a_min_amplitude" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_max_amplitude">Select maximum Amplitude [V]: </label>
                <input type="number" placeholder="Amplitude" name="n9310a_max_amplitude" id="n9310a_max_amplitude" />
            </div>
            
            <div class="config--parameter">
                <label for="n9310a_n_sweep_points">Select number of sweep points: </label>
                <input type="number" placeholder="Sweep points" name="n9310a_n_sweep_points" id="n9310a_n_sweep_points" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Cryonics magnet configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="dc_field_strength_min">Select minimum fieldstrength [T]: </label>
                <input type="number" name="dc_field_strength_min" id="dc_field_strength_min" placeholder="B-Field" />
            </div>
            
            <div class="config--parameter">
                <label for="dc_field_strength_max">Select maximum fieldstrength [T]: </label>
                <input type="number" name="dc_field_strength_max" id="dc_field_strength_max" placeholder="B-Field" />
            </div>
            
            <div class="config--parameter">
                <label for="dc_field_n_sweep_points">Select number of sweep points: </label>
                <input type="number" placeholder="Sweep points" name="dc_field_n_sweep_points" id="dc_field_n_sweep_points" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Oscilloscope (Analog discovery 2) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <label for="oscope_resistor">Select resistor value [Ohm]: </label>
                <input type="number" name="oscope_resistor" id="oscope_resistor" placeholder="Resistor" />
            </div>
        </div>
    </div>
    
    <div class="instrument--container">
        <h1 class="h4">Dilution fridge (MCK50-100) configuration</h1>
        <div class="instrument--config">
            <div class="config--parameter">
                <input type="button" value="Begin automatic cooldown" name="df_auto_cool">
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

function to_fixed(num, dec) {
    return Math.round(num * (10^dec)) / (10^dec);
}

function get_temperature_list(state) {
    return `
        <div>Current temperatures: </div>
        <div class="temperature--label">t_upper_hex = ${to_fixed(state['temperatures']['t_upper_hex'], 2)}K</div>
        <div class="temperature--label">t_lower_hex = ${to_fixed(state['temperatures']['t_lower_hex'], 2)}K</div>
        <div class="temperature--label">t_he_pot = ${to_fixed(state['temperatures']['t_he_pot'], 2)}K</div>
        <div class="temperature--label">t_1st_stage = ${to_fixed(state['temperatures']['t_1st_stage'], 2)}K</div>
        <div class="temperature--label">t_2nd_stage = ${to_fixed(state['temperatures']['t_2nd_stage'], 2)}K</div>
        <div class="temperature--label">t_inner_coil = ${to_fixed(state['temperatures']['t_inner_coil'], 2)}K</div>
        <div class="temperature--label">t_outer_coil = ${to_fixed(state['temperatures']['t_outer_coil'], 2)}K</div>
        <div class="temperature--label">t_switch = ${to_fixed(state['temperatures']['t_switch'], 2)}K</div>
        <div class="temperature--label">t_he_pot_2 = ${to_fixed(state['temperatures']['t_he_pot_2'], 2)}K</div>
        <div class="temperature--label">t_still = ${to_fixed(state['temperatures']['t_still'], 2)}K</div>
        <div class="temperature--label">t_mixing_chamber_1 = ${to_fixed(state['temperatures']['t_mixing_chamber_1'], 2)}K</div>
        <div class="temperature--label">t_mixing_chamber_2 = ${to_fixed(state['temperatures']['t_mixing_chamber_2'], 2)}K</div>`;
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
        <div class="pressure--label">p_1 = ${to_fixed(state['pressures']['p_1'], 2)}</div>
        <div class="pressure--label">p_2 = ${to_fixed(state['pressures']['p_2'], 2)}</div>
        <div class="pressure--label">p_3 = ${to_fixed(state['pressures']['p_3'], 2)}</div>
        <div class="pressure--label">p_4 = ${to_fixed(state['pressures']['p_4'], 2)}</div>
        <div class="pressure--label">p_5 = ${to_fixed(state['pressures']['p_5'], 2)}</div>
        <div class="pressure--label">p_6 = ${to_fixed(state['pressures']['p_6'], 2)}</div>
        <div class="pressure--label">p_7 = ${to_fixed(state['pressures']['p_7'], 2)}</div>
        <div class="pressure--label">p_8 = ${to_fixed(state['pressures']['p_8'], 2)}</div>`;
}

function get_temperature_plot(state) {
    return `
        <div class="cryogenics_status status_container">
            <h1 class="h4">Temperature status</h1>
            <div class="status_contents plot_container row">
                <div class="temperature-plot--container col-9" id="temperature-plot"></div>
                <div class="temperature--container col-3">
                    ${get_temperature_list(state)}
                </div>
            </div>
        </div>`;
}

function get_long_temperature_plot() {
    return `
    <div class="cryogenics_status status_container">
        <h1 class="h4">Temperature status (long timescale)</h1>
        ${get_long_temperature_buttons()}
        <div class="status_contents plot-2_container row">
            <img class="temperature-plot-2--container col-9" id="temperature-plot-2" src="/get_plot" />
        </div>
    </div>
    `;
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
</div>`;
}

// Get the configuration page
const sr830_frequencies = [0.0625, 0.125, 0.25, 0.5, 1., 2., 4., 8., 16., 32., 64., 128., 256., 512.]
const sr830_sensitivities = [2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6, 10e-6,
    20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1]

function get_config_page_template(state) {
    // Grab the existing experiment configuration
    const experiment_config = state['experiment_config'];

    // Create options for the SR830 sensitivity dropdown
    const sr830_sensitivity_options = sr830_sensitivities.map(sens => {
        let is_default = '';
        if (sens === experiment_config['sr830_sensitivity']) {
            is_default = 'selected="selected"'
        }

        return `<option value="${sens}" ${is_default}>${sens}V</option>`;
    });

    // Create the options for the SR830 frequency options
    const sr830_frequency_options = sr830_frequencies.map(freq => {
        let is_default = '';
        if (freq === experiment_config['sr830_frequency']) {
            is_default = 'selected="selected"';
        }

        return `<option ${is_default} value="${freq}">${freq} Hz</option>`;
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
                <label for="sr830_sensitivity">Select sensitivity: </label>
                <select name="sr830_sensitivity" id="sr830_sensitivity">${sr830_sensitivity_options}</select>
            </div>
            
            <div class="config--parameter">
                <label for="sr830_freq">Frequency: </label>
                <select name="sr830_frequency" id="sr830_freq">${sr830_frequency_options}</select>
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
</form>`;
}

function get_cryo_page_buttons() {
    return `
        <input type="button" value="Get status" name="df_get_status" onclick="get_cryo_status()" />
    `
}

function get_long_temperature_buttons() {
    save_temperatures_button = `<input type="button" value="Save temperatures continually" 
    name="df_save_temps" onclick="begin_save_temperatures()" />`;

    if (state['is_saving_temperatures']) {
    save_temperatures_button = `<input type="button" value="Stop saving temperatures" 
            name="df_save_temps" onclick="end_save_temperatures()" />`;
    }

    return `
    ${save_temperatures_button}
    <input type="button" value="Reload plot" name="df_reload_plot" onclick="pagehandlers['cryo_page']()" />
    `
}

function get_cryogenics_page_html() {
    return `
    <div class="cryogenics_status status_container">
        <h1 class="h4">Instrument status and latest ack</h1>
        <div class="status_contents row">
            <div class="status-ack--container col-12">
                <div id="cryo_status">Status: Unknown</div>
                <div id="cryo_ack">Latest ack: Unknown</div>
            </div>
        </div>
    </div>
    
    <form id="cryo_config_form" class="cooldown_form">
        <div class="instrument--container">
            <div class="instrument--config">
                <div class="config--parameter" id="cryo_page_buttons_container">
                    ${get_cryo_page_buttons()}
                </div>
            </div>
        </div>
    </form>
    
    <form id="cryo_picowatt_config_form" class="picowatt_form">
        <h1>Picowatt configuration</h1>
        <div class="instrument--container">
            <div class="instrument--config">
                <div class="config--parameter" id="cryo_page_picowatt_inputmode_container">
                    <label for="picowatt_InputMode">Input Mode</label>
                    <select id="picowatt_InputMode" name="picowatt_InputMode">
                        <option value="0">Grounded</option>
                        <option value="1">Measure</option>
                        <option value="2">Calibrate</option>
                    </select>
                </div>
                
                <div class="config--parameter" id="cryo_page_picowatt_inputmode_container">
                    <label>Channel</label>
                    <select id="picowatt_MultiplexerChannel" name="picowatt_MultiplexerChannel">
                        <option value="0">0</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                        <option value="6">6</option>
                        <option value="7">7</option>
                    </select>
                </div>
                
                <div class="config--parameter" id="cryo_page_picowatt_range_container">
                    <label>Range</label>
                    <select id="picowatt_Range" name="picowatt_Range">
                        <option value="0">Open</option>
                        <option value="2">2 Ohm</option>
                        <option value="20">20 Ohm</option>
                        <option value="200">200 Ohm</option>
                        <option value="2000">2K Ohm</option>
                        <option value="20000">20K Ohm</option>
                        <option value="200000">200K Ohm</option>
                        <option value="2000000">2M Ohm</option>
                    </select>
                </div>
                
                <div class="config--parameter" id="cryo_page_picowatt_excitation_container">
                    <label>Excitation</label>
                    <select id="picowatt_Excitation" name="picowatt_Excitation">
                        <option value="0">No excitation</option>
                        <option value="3e-6">3e-6V</option>
                        <option value="1e-5">1e-5V</option>
                        <option value="3e-5">3e-5V</option>
                        <option value="1e-4">1e-4V</option>
                        <option value="3e-4">3e-4V</option>
                        <option value="1e-3">1e-3V</option>
                        <option value="3e-3">3e-3V</option>
                    </select>
                </div>
                
                <div class="config--parameter" id="cryo_page_picowatt_display_container">
                    <label>Display</label>
                    <select id="picowatt_Display" name="picowatt_Display">
                        <option value="0">R</option>
                        <option value="1">Delta R</option>
                        <option value="2">Adjust reference voltage</option>
                        <option value="3">Reference voltage</option>
                        <option value="4">Excitation voltage</option>
                    </select>
                </div>
                
                <input type="button" value="Refresh picowatt settings" onclick="update_picowatt_settings()" />
                <input type="button" value="Save picowatt settings" onclick="save_picowatt_settings()" />
            </div>
        </div>
    </form>
    
    ${get_long_temperature_plot()}
    ${get_temperature_plot(state)}
    
    <div class="cryogenics_status status_container">
        <h1 class="h4">Pressures</h1>
        <div class="status_contents plot_container row">
            <div class="pressure-plot--container col-9" id="pressure-plot"></div>
            <div class="pressure--container col-3">
                ${get_pressure_list(state)}
            </div>
        </div>
    </div>`;
}

function get_data_table_html(data) {
    // Create a row for each experiment in the experiment configs
    rows = ''
    data.list.forEach(row => {
        rows += `
        <tr>
          <th scope="row">${row.id}</th>
          <td>${row.created}</td>
          <td>${row.n_points_taken} / ${row.n_points_total}</td>
          <td>${row.data_wait_before_measuring} s</td>
          <td>${row.magnet_min_field} to ${row.magnet_max_field} T in ${row.magnet_sweep_steps} steps</td>
          <td>${row.n9310a_min_amplitude} to ${row.n9310a_max_amplitude} V in ${row.n9310a_sweep_steps} steps</td>
          <td>${row.n9310a_min_frequency} to ${row.n9310a_max_frequency} Hz in ${row.n9310a_sweep_steps} steps</td>
          <td>${row.sr830_sensitivity} V</td>
          <td><a class="btn btn-primary" href="/export?id=${row.id}" role="button" 
                 download="data_export_id_${row.id}.json">Export</a></td>
        </tr>`;
    });

    // If we're past the first page we want to display a back button
    prev_button = '';
    if (data.page > 1) {
        prev_button = `<input type="button" value="Previous page" name="prev_page" 
                              onclick="get_experiments_list(${data.page - 1})">`;
    }

    // If we're not at the last page, we want to display a next button
    next_button = '';
    if ((data.count - data.page * 10) % 10 > 0) {
        next_button = `<input type="button" value="Next page" name="next_page"
                              onclick="get_experiments_list(${data.page + 1})">`;
    }

    // Here we add column headers and collect the HTML we've generated until this point
    return `
    <table class="table">
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Created</th>
          <th scope="col">Datapoints</th>
          <th scope="col">Delay</th>
          <th scope="col">Magnet</th>
          <th scope="col">Excitation amplitude</th>
          <th scope="col">Excitation frequency</th>
          <th scope="col">Lockin sensitivity</th>
          <th scope="col">Export</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
    <hr>
    ${prev_button}
    ${next_button}`;
}

function get_data_page_html() {
    return `
    <div id="datatable_wrapper">
        Loading experiment configurations...
    </div><hr>
    <div>
        <h3>How to import and treat the data</h3>
        
        <p>
            The data is saved to a database when the experiment is running, and is sent to the user in a JSON format.
            The JSON format is a nested object that can be read by builtin methods of most programming languages.
            In Python it is read into a dictionary by default, but pandas for example supports reading it into a 
            series for processing. <br>
            
            The outermost layer of the format contain the most generic options, here you can find the experiment 
            configuration used to generate the steps, as well as a list of all the steps generated.
            Each step contains the specific parameters used in that step and it contains a list of datapoints.
            Each datapoint has a time of when it was saved, and it has some magnetism datapoints, where the ac rms
            field, the dc field, the lockin amplitude, and the lockin phase are saved. It also has pressure datapoints
            where each pressure of the GHS is saved, and finally it has temperature datapoints where all the 
            temperatures are saved. <br>
            
            The following is an example Python script that opens a datafile (set by the variable "data_filename"), it
            prints the entire export dictionary, then it grabs the max function generator frequency used, and it 
            computes the mean lockin amplitudes and prints those out.
        </p>
        
        <!-- HTML generated using hilite.me --><div style="background: #ffffff; overflow:auto;width:auto;border:solid gray;border-width:.1em .1em .1em .8em;padding:.2em .6em;"><table><tr><td><pre style="margin: 0; line-height: 125%"> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61</pre></td><td><pre style="margin: 0; line-height: 125%"><span style="color: #888888"># We need a couple of modules to import the data and print it</span>
<span style="color: #008800; font-weight: bold">import</span> <span style="color: #0e84b5; font-weight: bold">json</span>
<span style="color: #008800; font-weight: bold">from</span> <span style="color: #0e84b5; font-weight: bold">pprint</span> <span style="color: #008800; font-weight: bold">import</span> pprint

<span style="color: #888888"># We import numpy to process data, but we don&#39;t actually need it to import the data</span>
<span style="color: #008800; font-weight: bold">import</span> <span style="color: #0e84b5; font-weight: bold">numpy</span> <span style="color: #008800; font-weight: bold">as</span> <span style="color: #0e84b5; font-weight: bold">np</span>

<span style="color: #888888"># We set the filename here</span>
data_filename <span style="color: #333333">=</span> <span style="background-color: #fff0f0">&#39;data_export_id_17.json&#39;</span>

<span style="color: #888888"># We open the file</span>
<span style="color: #008800; font-weight: bold">with</span> <span style="color: #007020">open</span>(data_filename, <span style="background-color: #fff0f0">&#39;r&#39;</span>) <span style="color: #008800; font-weight: bold">as</span> df:
    <span style="color: #888888"># And read the contents</span>
    file_contents <span style="color: #333333">=</span> <span style="background-color: #fff0f0">&#39;&#39;</span><span style="color: #333333">.</span>join(df<span style="color: #333333">.</span>readlines())

<span style="color: #888888"># Next we decode the file contents using the json module    </span>
experiment_configuration <span style="color: #333333">=</span> json<span style="color: #333333">.</span>loads(file_contents)

<span style="color: #888888">## Now we have all the data available</span>

<span style="color: #888888"># And we print it to see what is going on</span>
<span style="color: #008800; font-weight: bold">print</span>(<span style="background-color: #fff0f0">&#39;the entire experiment&#39;</span>)
pprint(experiment_configuration)

<span style="color: #888888"># After this we create a new line to seperate the content</span>
<span style="color: #008800; font-weight: bold">print</span>(<span style="background-color: #fff0f0">&#39;</span><span style="color: #666666; font-weight: bold; background-color: #fff0f0">\\n</span><span style="background-color: #fff0f0">&#39;</span>)

<span style="color: #888888"># It is a deep dictionary where the outermost layer contains the experiment configuration</span>
<span style="color: #888888"># To see a specific experiment configuration parameter (for example the max frequency of </span>
<span style="color: #888888"># the function generator) we can run:</span>
<span style="color: #008800; font-weight: bold">print</span>(<span style="background-color: #fff0f0">&#39;the max frequency:&#39;</span>, experiment_configuration[<span style="background-color: #fff0f0">&#39;n9310a_max_frequency&#39;</span>])

<span style="color: #888888"># After this we create a new line to seperate the content</span>
<span style="color: #008800; font-weight: bold">print</span>(<span style="background-color: #fff0f0">&#39;</span><span style="color: #666666; font-weight: bold; background-color: #fff0f0">\\n</span><span style="background-color: #fff0f0">&#39;</span>)

<span style="color: #888888"># Inside the configuration we have a parameter called steps, which contains all the steps </span>
<span style="color: #888888"># generated by this specific configuration.</span>
<span style="color: #888888"># We can either iterate through each step, or we can select a specific step.</span>
<span style="color: #888888"># Let&#39;s iterate through the steps, and find the mean lockin_amplitude for each step</span>

<span style="color: #888888"># We start with an empty list</span>
mean_lockin_amplitudes <span style="color: #333333">=</span> []

<span style="color: #888888"># Then we run through each step</span>
<span style="color: #008800; font-weight: bold">for</span> step <span style="color: #000000; font-weight: bold">in</span> experiment_configuration[<span style="background-color: #fff0f0">&#39;steps&#39;</span>]:
    <span style="color: #888888"># We create a second, temporary, list to hold the the amplitudes of this step (the ones we take the mean of)</span>
    lockin_amplitude_datapoints <span style="color: #333333">=</span> []
    
    <span style="color: #888888"># We iterate through the datapoints</span>
    <span style="color: #008800; font-weight: bold">for</span> datapoint <span style="color: #000000; font-weight: bold">in</span> step[<span style="background-color: #fff0f0">&#39;datapoints&#39;</span>]:
        <span style="color: #888888"># And we iterate through the magnetism datapoints</span>
        <span style="color: #008800; font-weight: bold">for</span> mdp <span style="color: #000000; font-weight: bold">in</span> datapoint[<span style="background-color: #fff0f0">&#39;magnetism_datapoints&#39;</span>]:
            <span style="color: #888888"># We add the lockin amplitude to the list we created inside the for loop</span>
            lockin_amplitude_datapoints<span style="color: #333333">.</span>append(mdp[<span style="background-color: #fff0f0">&#39;lockin_amplitude&#39;</span>])
            
    <span style="color: #888888"># Now we find a mean of that list and add it to the list of mean amplitudes</span>
    mean_lockin_amplitudes<span style="color: #333333">.</span>append(np<span style="color: #333333">.</span>mean(lockin_amplitude_datapoints))
    
<span style="color: #888888"># Finally we print out the list of mean amplitudes</span>
<span style="color: #008800; font-weight: bold">print</span>(<span style="background-color: #fff0f0">&#39;the mean lockin amplitudes&#39;</span>)
pprint(mean_lockin_amplitudes)
</pre></td></tr></table></div>
    </div>
`;
}

function get_info_page_html() {
    return `
    This page was made for a thesis
    `
}

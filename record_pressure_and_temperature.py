from instrument_drivers.PfeifferVacuum_MaxiGauge import MaxiGauge
from instrument_drivers.LeidenCryogenics_GHS_2T_1T_700_CF import LC_GHS
from instrument_drivers.Picowatt_AVS47B_direct import Avs_47b_direct
from instrument_drivers.Keysight_2700_DMM import Keysight_2700_DMM

import time
from json import dumps

def get_temperature(rb, channel):
    # First we change to the channel we want to measure
    rb.MultiplexerChannel.set(channel)

    # And we set the alarmline, so we get a signal when data is ready
    rb.AlarmLine.set(0)

    # Now we send the updated configuration
    # We set it to remote mode for it all to function
    # And we don't want to overwrite our users configuration
    rb.send_config(True, False)

    # Then we get the resistance
    resistance = rb.get_resistance()

    # And convert it to a temperature
    return rb.convert_to_temperature(channel, resistance)


def main_run():
    # Open the connection
    maxigauge = MaxiGauge('maxigauge', 'COM10')
    ghs = LC_GHS('frontpanel', 'ASRL7::INSTR')
    dmm = Keysight_2700_DMM('dmm', 'ASRL6::INSTR')
    rb = Avs_47b_direct('avs', 'COM9')

    # Setup the resistance bridge
    rb['InputMode'].set(1)
    rb['Display'].set(0)
    rb['Excitation'].set(0.0003)
    rb['Range'].set(200000)
    rb['ReferenceVoltage'].set(0)

    # First we update the bridge to reflect the setting we just set
    # The bools are remote, save config, and return decoded
    rb.send_config(True, False, False)

    # Next we update our local config to reflect what the state of the device actually is
    rb.send_config(True, True, False)

    # And we create a filename
    filename = 'time_pressure_temperature_' + str(int(time.time())) + '.jsonlist'

    # Wait for the instruments to initialize
    time.sleep(5)

    while True:
        # Query the maxigauge for pressures
        s5, p_max_5 = maxigauge.get_pressure(5)
        s6, p_max_6 = maxigauge.get_pressure(6)

        # Query the ghs for pressures
        ghs.get_all_params()
        p_1 = ghs.pressure_p1.get_latest()
        p_2 = ghs.pressure_p2.get_latest()
        p_3 = ghs.pressure_p3.get_latest()
        p_4 = ghs.pressure_p4.get_latest()
        p_5 = ghs.pressure_p5.get_latest()
        p_6 = ghs.pressure_p6.get_latest()
        p_7 = ghs.pressure_p7.get_latest()
        p_8 = ghs.pressure_p8.get_latest()

        # Query the temperature controllers for the new temperatures
        t_still = get_temperature(rb, 1)
        t_mixing_chamber_1 = get_temperature(rb, 2)
        t_mixing_chamber_2 = get_temperature(rb, 3)
        scan_data = dmm.scan_channels()

        # Create a datastring
        dataString = dumps({
            'time': time.time(),
            'pressures': [p_max_5, p_max_6, p_1, p_2, p_3, p_4, p_5, p_6, p_7, p_8],
            'temperatures': [
                scan_data['Upper HEx'],
                scan_data['Lower HEx'],
                scan_data['He Pot CCS'],
                scan_data['1st stage'],
                scan_data['2nd stage'],
                scan_data['Inner Coil'],
                scan_data['Outer Coil'],
                scan_data['Switch'],
                scan_data['He Pot'],
                t_still,
                t_mixing_chamber_1,
                t_mixing_chamber_2
            ]
        })

        # print it out
        print(dataString)

        # And write it to a file
        with open(filename, 'a') as f:
            f.writelines(dataString + '\n')

        # Sleep for 1 second
        time.sleep(15)


if __name__ == '__main__':
    main_run()

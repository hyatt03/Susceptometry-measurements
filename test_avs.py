import time
import instrument_drivers.Picowatt_AVS47B_direct as Avs_47b


def main_run():
    avs = Avs_47b.Avs_47b_direct('avs', 'COM9')
    
    for i in range(10):
        for i in range(8):
            # Check the resistance on channel i
            ovr, temperature, ch_out = avs.query_for_temperature(i)

            # Print out the result
            if ovr:
                print(f'Channel {ch_out} is overranged')
            else:
                print(f'Temperature on channel {ch_out}: {temperature}K')
        
        time.sleep(1)

if __name__ == '__main__':
    main_run()

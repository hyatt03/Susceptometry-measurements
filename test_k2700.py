from instrument_drivers.Keysight_2700_DMM import Keysight_2700_DMM

from time import sleep

def main_run():
    # Open the connection
    dmm = Keysight_2700_DMM('DMM', 'ASRL6::INSTR')

    for i in range(100):
        # query the scan
        print('trying to scan channels')
        print(dmm.scan_channels())
        sleep(1)

if __name__ == '__main__':
    main_run()

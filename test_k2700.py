from instrument_drivers.Keysight_2700_DMM import Keysight_2700_DMM

def main_run():
    # Open the connection
    dmm = Keysight_2700_DMM('frontpanel', 'ASRL7::INSTR')

    # query the scan
    dmm.scan_channels()


if __name__ == '__main__':
    main_run()

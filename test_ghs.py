from instrument_drivers.LeidenCryogenics_GHS_2T_1T_700_CF import LC_GHS

def main_run():
    # Open the connection
    ghs = LC_GHS('frontpanel', 'ASRL7::INSTR')

    # Ask for an update on the parameters
    ghs.get_all_params()

    # Print the current status
    ghs.print_readable_snapshot()


if __name__ == '__main__':
    main_run()

from instrument_drivers.LeidenCryogenics_TripleCurrentSource import LC_TCS
import time

def main_run():
    # Open the connection
    tcs = LC_TCS('tripple_current_source', 'ASRL8::INSTR')

    # Ask for an update on the parameters
    tcs.get_all_params()

    # Set the current on a channel
    tcs.set_current(2, 1)

    # Turn on the channel
    tcs.toggle_channel_on(2)

    # Wait a bit
    time.sleep(5)

    # Turn of the channel
    tcs.toggle_channel_on(2)

    # Set the current back to 0
    tcs.set_current(2, 0)

    # Print the current status
    tcs.print_readable_snapshot()


if __name__ == '__main__':
    main_run()

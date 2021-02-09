import numpy as np
import instrument_drivers.Picowatt_AVS47B_direct as Avs_47b


def main_run():
    avs = Avs_47b.Avs_47b_direct('avs', 'COM9')
    
    avs.print_readable_snapshot()


if __name__ == '__main__':
    main_run()

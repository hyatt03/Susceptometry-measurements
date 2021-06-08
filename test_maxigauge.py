from instrument_drivers.PfeifferVacuum_MaxiGauge import MaxiGauge

from matplotlib import pyplot as plt

from time import sleep

def main_run():
    # Open the connection
    maxigauge = MaxiGauge('maxigauge', 'COM10')

    time = []
    pressure5 = []
    pressure6 = []

    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    t = 0
    while True:
        # Query the maxigauge for pressures
        s5, p5 = maxigauge.get_pressure(5)
        s6, p6 = maxigauge.get_pressure(6)

        # Add the new data to the lists
        time.append(t)
        pressure5.append(p5)
        pressure6.append(p6)

        # Clear the axes
        ax.clear()

        # Replot the data
        ax.plot(time, pressure5, '-', label='p5')
        ax.plot(time, pressure6, '-', label='p6')

        # Style the plot
        plt.legend()
        plt.xlabel('time [~s]')
        plt.ylabel('pressure [mbar]')
        plt.grid()

        # Draw the image
        fig.canvas.draw()
        fig.canvas.flush_events()

        # Sleep for 1 second
        sleep(1)

        # Update the time
        t += 1

if __name__ == '__main__':
    main_run()

import numpy as np
import matplotlib.pyplot as plt


def main_run():
    parameters_1 = [79362.66285435, -134213.20861799, 101026.7304322, -44413.273683345, 12564.321465816,
                    -2371.588181102, 298.641277814, -24.188904628, 1.143358358, -0.024026573]

    pol_1 = np.polynomial.polynomial.Polynomial(parameters_1)
    numbers = pol_1.linspace(100, [100, 10000])

    print(numbers)

    plt.plot(numbers[0], numbers[1], '.')
    # plt.yscale('log')
    # plt.xscale('log')
    plt.show()


if __name__ == '__main__':
    main_run()

import numpy as np

calib_file = np.loadtxt("3)He Pot CCS.txt", delimiter=",")

for i in range(calib_file.shape[0]):
    print(calib_file[i, 0], calib_file[-i - 1, 1])

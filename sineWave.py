import math

import matplotlib.pyplot as plt
import numpy as np
import sys,argparse,csv
import pandas as pd

df = pd.read_csv("sine_wave3_10Hz.csv", delimiter=",")
Ax = list(df['ax'])
Ay = list(df['ay'])
Az = list(df['az'])

Ax = np.array(Ax)
Ay = np.array(Ay)
Az = np.array(Az)



acc_norm = []
acc_norm.append(
                math.sqrt(
                    Ax*Ax + Ay*Ay + Az*Az  # rootOf (Ax^2, Ay^2, Az^2)
                )
            )

plt.plot(acc_norm, label='Norm of 3D Acceleration')
# plt.plot( acc_LP, label='Result of Low Pass Butterworth filter')
plt.xlabel('sample(n)')
plt.ylabel('Acceleration')
plt.legend()
plt.show()



# with open ('sine_wave3_10Hz.csv') as csv_file:
#     csv_reader=csv.DictReader(csv_file,delimiter=',')
#     line_count=0
#     for row in csv_reader:
#                 ax =row['ax']
#                 ay =row['ay']
#                 az =row['az']
#                 acc_norm = []
#                 acc_norm.append(
#                     math.sqrt(
#                         ax ** 2 + ay ** 2 + az ** 2  # rootOf (Ax^2, Ay^2, Az^2)
#                     )
#                 )
#
#                 plt.plot(acc_norm, label='Norm of 3D Acceleration')
#                 # plt.plot( acc_LP, label='Result of Low Pass Butterworth filter')
#                 plt.xlabel('sample(n)')
#                 plt.ylabel('Acceleration')
#                 plt.legend()
#                 plt.show()
#
#
# csv_file.close()

# Fs = 8000
# f = 5
# Ax=0
# Ay=0
# sample = 8000
# sample_n = np.arange(sample)
# Az = np.sin(2 * np.pi * f * sample_n / Fs)
# temp = []
# temp[0]= Ax
# temp[1]= Ay
# temp[2]= Az

# plt.plot(sample_n, Az)
# plt.xlabel('sample(n)')
# plt.ylabel('acc')
# plt.show()
# acc_norm = []
# acc_norm.append(
# math.sqrt(
# Ax ** 2 + Ay ** 2 + Az ** 2  # rootOf (Ax^2, Ay^2, Az^2)
#     )
#     )
#
# plt.plot(acc_norm, label='Norm of 3D Acceleration')
# # plt.plot( acc_LP, label='Result of Low Pass Butterworth filter')
# plt.xlabel('sample(n)')
# plt.ylabel('Acceleration')
# plt.legend()
# plt.show()

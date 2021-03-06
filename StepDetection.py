from quaternion import *
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv


# ####
# in the sensor.csv file:
# X axis: pedestrian moving direction
# Y axis: it is perpendicular to both X and Z axis
# Z axis: It is parallel to gravity pointing upward. Therefore, it will show +1g value
# ####
class Worker:

    def __init__(self):
        # sensor data for processing
        self.sensor_data_process = []

        # sample rate. This is used as delta T in integration
        self.sampling_rate = 100  # 400

        # Used for integration
        self.delta_time = 1.0 / self.sampling_rate

        # Madwick filter tuning parameter
        self.beta = 0.1

        # Madwick filter tuning parameter
        self.epsilon = 0.001

        # Earth gravity in m/s
        self.gravity = 9.7

        # K value for step length calculation. Changes person to person
        self.magic_number_scale = 5.1  # value of K from research paper

        # Gravity scaling
        self.scale = self.gravity * self.magic_number_scale  # 9.7 * 5.1 = 49.47

        lowpass_cutoff = 2.0  # low pass filter

        self.LP_b, self.LP_a = signal.butter(2, 2.0 * lowpass_cutoff * self.delta_time,
                                           'low')  # to normalise extra 2 has been multipied w=Fc/(Fs/2)

        # PLP_Cutoff = 0.05
        # self.PLP_b, self.PLP_a = signal.butter(1, 2.0 * PLP_Cutoff * self.delta_time, 'low')

        # pass band ripple
        # self.fs = 0.1

        # z, p = signal.bilinear(self.PLP_b, self.PLP_a, self.fs)

        # ?
        self.reserve_data_length = 200

        # flag for walking
        self.walking = False

        # step count store
        self.step_number = 0

        # ?
        self.start_pressure = -1.0  # added

        return

    def Run(self):

        # read time related information from Timer.txt file. Timer.txt is
        in_file = open('Timer.txt', 'r')
        in_file.readline()
        temp_line = in_file.readline()
        time_calibrate = float(temp_line.split(',')[1])  # line by line read and store the value in the variable
        temp_line = in_file.readline()
        time_start = float(temp_line.split(',')[1])
        temp_line = in_file.readline()
        time_end = float(temp_line.split(',')[1])
        in_file.close()

        in_file = open('sensors.csv', 'r')
        in_file.readline()
        self.current_pose = Quaternion()
        deg2rad = math.pi / 180.0
        temp_data_buffer = []
        buffer_size = 0
        buffer_size_max = 800
        for temp_line in in_file.readlines():
            temp_seq = temp_line.split(',')
            temp_time = float(temp_seq[0])
            temp_data = []
            for i in range(1, 7):
                temp_data.append(float(temp_seq[i]))
            temp_data.append(float(temp_seq[10]))  # pressure data
            if temp_time > time_end:  # time end is given timer.txt file
                break
            elif temp_time > time_start:
                temp_data_buffer.extend(temp_data)
                buffer_size += 1
                if buffer_size > buffer_size_max:
                    if self.start_pressure < 0.0:
                        self.start_pressure = 0.0
                        for i in range(buffer_size):
                            self.start_pressure += temp_data_buffer[i * 7 + 6]
                        self.start_pressure /= buffer_size
                    self.sensor_data_process.extend(temp_data_buffer)
                    self.StepDetection()  # step detection

                    temp_data_buffer = []
                    buffer_size = 0
            elif temp_time > time_calibrate:
                self.current_pose.Update(
                    temp_data[0] * deg2rad, temp_data[1] * deg2rad, temp_data[2] * deg2rad,
                    temp_data[3], temp_data[4], temp_data[5],
                    self.delta_time,
                    self.beta,
                    self.epsilon
                )
        in_file.close()

        return

    ####### StepDisplacement ###############################
    def StepDisplacement(self, _data, _type=0):
        # data: acc_x, acc_y, acc_z, pressure,...
        displacement = Vector3()

        delta_time = self.delta_time

        data_length = len(_data) // 4

        velocity_x = 0.0
        velocity_y = 0.0

        for i in range(data_length):
            velocity_x += _data[i * 4] * delta_time
            velocity_y += _data[i * 4 + 1] * delta_time
            displacement.x += velocity_x * delta_time
            displacement.y += velocity_y * delta_time
            displacement.z += _data[i * 4 + 3]  # pressure value

        displacement.x *= -self.scale  # scale= k= - Dg/Dd
        displacement.y *= -self.scale
        displacement.z /= data_length

        # Scale first step (start to move) and last step (stop)
        if _type == -1:
            displacement.x *= -0.5
            displacement.y *= -0.5
        elif _type == -2:
            displacement.x *= 0.5
            displacement.y *= 0.5

        self.Update(displacement.x, displacement.y, displacement.z)

        self.step_number += 1

        return displacement

    def Update(self, _dx, _dy, _z, _check_floor=True):
        step_length = math.sqrt(_dx ** 2 + _dy ** 2)
        if (step_length < 0.1) or (step_length > 1.5):
            print('Dropped step, length: %.3fm' % step_length)

        else:

            print('step lenth: %.3fm' % step_length)
            # step_length.to_csv('stepLength.csv')
            # for i in range(step_length):
            #    with open("random.csv", "w") as fp:
            #       fp.write(str(step_length))

            # df = pd.DataFrame(eval(step_length))
            # print(df)
            # df.to_csv('export_dataframe.csv', sep=',', index=False)
            # plt.plot(step_length)  #####added
            # plt.xlabel('Time')
            # # naming the y axis
            # plt.ylabel('Step length')
            # plt.show()  #####added
            return

    ####### Step Detection ###############################

    def StepDetection(self):

        # timeaxis = self.timeValue###added
        # print("time", timeaxis)
        data_process = self.sensor_data_process

        data_length = len(data_process) // 7
        if data_length < 800:
            # BUG in real time mode, I should return data_process to self.sensor_data_process here
            return
        current_pose = self.current_pose
        delta_time = self.delta_time
        beta = self.beta
        epsilon = self.epsilon

        acc_norm = []
        pressure = []
        for i in range(data_length):
            acc_norm.append(
                math.sqrt(
                    data_process[i * 7 + 3] ** 2 + data_process[i * 7 + 4] ** 2 + data_process[i * 7 + 5] ** 2
                    # rootOf (Ax^2, Ay^2, Az^2)
                )
            )

            pressure.append(data_process[i * 7 + 6])

        acc_LP = signal.filtfilt(self.LP_b, self.LP_a, acc_norm)
        pressure_LP = signal.filtfilt(self.PLP_b, self.PLP_a, pressure)


        # plt.plot( acc_norm, label='Norm of 3D Acceleration')
        # plt.plot( acc_LP, label='Result of Low Pass Butterworth filter')
        # plt.xlabel('no. of samples')
        # plt.ylabel('Acceleration')
        # plt.legend()
        # plt.show()



        temp_detected_step = []
        step_begin = 0
        step_mid = 0

        grad_threshold = 0.1
        length_threshold_min = self.sampling_rate * 0.3  # 0.3
        length_threshold_max = self.sampling_rate * 0.8  # 0.8

        for i in range(1, data_length - self.reserve_data_length):  # check 1 to 801-200
            if (acc_LP[i] < acc_LP[i - 1]) and (acc_LP[i] < acc_LP[i + 1]):
                step_mid = i
            if (acc_LP[i] > acc_LP[i - 1]) and (acc_LP[i] > acc_LP[i + 1]):
                if (acc_LP[step_begin] - acc_LP[step_mid] >= grad_threshold) and (
                        acc_LP[i] - acc_LP[step_mid] >= grad_threshold):
                    if (i - step_begin >= length_threshold_min) and (i - step_begin <= length_threshold_max):
                        temp_detected_step.append((step_begin, step_mid, i))
                step_begin = i

        detected_step = []

        if self.walking and len(temp_detected_step) == 0:
            detected_step.append((0, -2, int(self.sampling_rate * 0.5)))

        if len(temp_detected_step) > 0:
            last_index = 0
            for temp_step in temp_detected_step:
                if last_index == 0:
                    if self.walking:
                        if temp_step[0] > self.sampling_rate:
                            detected_step.append((0, -2, int(self.sampling_rate * 0.5)))
                            detected_step.append((temp_step[0] - int(self.sampling_rate * 0.5), -1, temp_step[0]))
                    else:
                        if temp_step[0] > int(self.sampling_rate * 0.3):
                            detected_step.append(
                                (max(0, temp_step[0] - int(self.sampling_rate * 0.5)), -1, temp_step[0]))
                else:
                    if temp_step[0] - last_index > self.sampling_rate:
                        detected_step.append((last_index, -2, last_index + int(self.sampling_rate * 0.5)))
                        detected_step.append((temp_step[0] - int(self.sampling_rate * 0.5), -1, temp_step[0]))
                detected_step.append(temp_step)
                last_index = temp_step[2]

            if data_length - self.reserve_data_length - temp_detected_step[-1][2] > self.sampling_rate:
                detected_step.append(
                    (temp_detected_step[-1][2], -2, temp_detected_step[-1][2] + int(self.sampling_rate * 0.5)))

        last_index = 0
        deg2rad = math.pi / 180.0
        for temp_step in detected_step:
            if temp_step[0] > last_index:
                for i in range(last_index, temp_step[0]):
                    current_pose.Update(
                        data_process[i * 7] * deg2rad, data_process[i * 7 + 1] * deg2rad,
                        data_process[i * 7 + 2] * deg2rad,
                        data_process[i * 7 + 3], data_process[i * 7 + 4], data_process[i * 7 + 5],
                        delta_time,
                        beta,
                        epsilon
                    )
            temp_data = []
            for i in range(temp_step[0], temp_step[2]):
                current_pose.Update(
                    data_process[i * 7] * deg2rad, data_process[i * 7 + 1] * deg2rad, data_process[i * 7 + 2] * deg2rad,
                    data_process[i * 7 + 3], data_process[i * 7 + 4], data_process[i * 7 + 5],
                    delta_time,
                    beta,
                    epsilon
                )
                acc_linear = current_pose.RotateVector(data_process[i * 7 + 3], data_process[i * 7 + 4],
                                                       data_process[i * 7 + 5])
                temp_data.append(acc_linear.x)
                temp_data.append(acc_linear.y)
                temp_data.append(acc_linear.z)
                temp_data.append(pressure_LP[i])
            step_disp = self.StepDisplacement(temp_data, temp_step[1])
            last_index = temp_step[2]
            # print('step displacement', step_disp)

        if len(detected_step) > 0:
            if detected_step[-1][1] == -2:
                self.walking = False
            else:
                self.walking = True
            data_process = data_process[(last_index * 7):]

        self.sensor_data_process = data_process

        return


if __name__ == '__main__':
    worker = Worker()
    worker.Run()

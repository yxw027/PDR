import logging
import math
import sys
import traceback

from scipy import signal
from pdr.quaternion import Vector3

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger("Step Detection")


class StepDetection:
    def __init__(self, step_detection_config, data_acquisition_packet):
        """

        :param step_detection_config:
        :param measurements:
        :param quaternion:
        """
        try:
            self.measurements = data_acquisition_packet["measurements"]
            self.measurement_column_count = len(step_detection_config["measurements"]["column_style"])
            self.measurement_count = len(self.measurements) // self.measurement_column_count
            if self.measurement_count < step_detection_config["measurements"]["thresholds"]["min_count"]:
                raise "insufficient measurement"

            self.column_style = data_acquisition_packet["column_style"]
            self.quaternion = data_acquisition_packet["quaternion"]

            self.sample_rate = step_detection_config["sampling"]
            self.delta_time = 1.0 / self.sample_rate

            self.beta = step_detection_config["beta"]
            self.epsilon = step_detection_config["epsilon"]

            # calculate norm of acceleration
            self.acceleration_norm = list()
            for i in range(self.measurement_count):
                acc_x = self.measurements[i * self.measurement_column_count + self.column_style.index("ax")]
                acc_y = self.measurements[i * self.measurement_column_count + self.column_style.index("ay")]
                acc_z = self.measurements[i * self.measurement_column_count + self.column_style.index("az")]
                self.acceleration_norm.append(math.sqrt(acc_x ** 2 + acc_y ** 2 + acc_z ** 2))

            # create filter for accelerometer data filtering
            accelerometer_lpf_cutoff = step_detection_config["accelerometer"]["lpf"]["cutoff_hz"]
            accelerometer_lpf_order = step_detection_config["accelerometer"]["lpf"]["order"]
            self.acc_lpf_b, self.acc_lpf_a = signal.butter(accelerometer_lpf_order,
                                                           2.0 * accelerometer_lpf_cutoff * self.delta_time,
                                                           'low')

            # filter accelerometer norm with the low pass filter
            self.acceleration_norm_lpf = signal.filtfilt(self.acc_lpf_b,
                                                         self.acc_lpf_a,
                                                         self.acceleration_norm)

            self.grad_threshold = step_detection_config["thresholds"]["grad"]
            self.time_length_factor_min = step_detection_config["thresholds"]["time_length_factor"]["min"]
            self.time_length_factor_max = step_detection_config["thresholds"]["time_length_factor"]["max"]

            self.walking = False
            self.reserve_data_length = step_detection_config["measurements"]["thresholds"]["reverse_data_len"]
            self.scale = step_detection_config["gravity"] * step_detection_config["k"]
            self.total_step_count = 0
            self.total_steps = []
        except (KeyError, Exception) as e:
            logger.error("Exception occured" + e)
            logger.error(traceback.format_exc())
            sys.exit()

    def detect(self):
        """

        :return:
        """
        try:
            _detected_step_ = []
            detected_step = []
            step_begin = 0
            step_mid = 0

            for i in range(1, self.measurement_count - self.reserve_data_length):
                # detect valley and determine middle point of valley, mid point valley is middle of step
                if (self.acceleration_norm_lpf[i] < self.acceleration_norm_lpf[i - 1]) and \
                        (self.acceleration_norm_lpf[i] < self.acceleration_norm_lpf[i + 1]):
                    step_mid = i

                # detect peak, this determines heel strike which is start of step
                if (self.acceleration_norm_lpf[i] > self.acceleration_norm_lpf[i - 1]) and \
                        (self.acceleration_norm_lpf[i] > self.acceleration_norm_lpf[i + 1]):
                    if (self.acceleration_norm_lpf[step_begin] - self.acceleration_norm_lpf[
                        step_mid] >= self.grad_threshold) and \
                            (self.acceleration_norm_lpf[i] - self.acceleration_norm_lpf[
                                step_mid] >= self.grad_threshold):
                        if (i - step_begin >= self.time_length_factor_min) and (
                                i - step_begin <= self.time_length_factor_max):
                            _detected_step_.append((step_begin, step_mid, i))
                    step_begin = i

            if self.walking and len(_detected_step_) == 0:
                detected_step.append((0, -2, int(self.sample_rate * 0.5)))

            if len(_detected_step_) > 0:
                last_index = 0
                for each_step in _detected_step_:
                    if last_index == 0:
                        if self.walking:
                            if each_step[0] > self.sample_rate:
                                detected_step.append((0, -2, int(self.sample_rate * 0.5)))
                                detected_step.append((each_step[0] - int(self.sample_rate * 0.5), -1, each_step[0]))
                        else:
                            if each_step[0] > int(self.sample_rate * 0.3):
                                detected_step.append(
                                    (max(0, each_step[0] - int(self.sample_rate * 0.5)), -1, each_step[0]))
                    else:
                        if each_step[0] - last_index > self.sample_rate:
                            detected_step.append((last_index, -2, last_index + int(self.sample_rate * 0.5)))
                            detected_step.append((each_step[0] - int(self.sample_rate * 0.5), -1, each_step[0]))
                    detected_step.append(each_step)
                    last_index = each_step[2]

                if self.measurement_count - self.reserve_data_length - _detected_step_[-1][2] > self.sample_rate:
                    detected_step.append(
                        (_detected_step_[-1][2], -2, _detected_step_[-1][2] + int(self.sampling_rate * 0.5)))

            last_index = 0
            deg2rad = math.pi / 180.0
            for each_step in detected_step:
                if each_step[0] > last_index:
                    for i in range(last_index, each_step[0]):
                        self.quaternion.Update(
                            self.measurements[
                                i * self.measurement_column_count + self.column_style.index("gx")] * deg2rad,
                            self.measurements[
                                i * self.measurement_column_count + self.column_style.index("gy")] * deg2rad,
                            self.measurements[
                                i * self.measurement_column_count + self.column_style.index("gz")] * deg2rad,
                            self.measurements[i * self.measurement_column_count + self.column_style.index("ax")],
                            self.measurements[i * self.measurement_column_count + self.column_style.index("ay")],
                            self.measurements[i * self.measurement_column_count + self.column_style.index("az")],
                            self.delta_time,
                            self.beta,
                            self.epsilon
                        )
                linear_acceleration = []
                for i in range(each_step[0], each_step[2]):
                    self.quaternion.Update(
                        self.measurements[i * self.measurement_column_count + self.column_style.index("gx")] * deg2rad,
                        self.measurements[i * self.measurement_column_count + self.column_style.index("gy")] * deg2rad,
                        self.measurements[i * self.measurement_column_count + self.column_style.index("gz")] * deg2rad,
                        self.measurements[i * self.measurement_column_count + self.column_style.index("ax")],
                        self.measurements[i * self.measurement_column_count + self.column_style.index("ay")],
                        self.measurements[i * self.measurement_column_count + self.column_style.index("az")],
                        self.delta_time,
                        self.beta,
                        self.epsilon
                    )
                    acc_linear = self.quaternion.RotateVector(self.measurements[i * self.measurement_column_count +
                                                                                self.column_style.index("ax")],
                                                              self.measurements[i * self.measurement_column_count +
                                                                                self.column_style.index("ay")],
                                                              self.measurements[i * self.measurement_column_count +
                                                                                self.column_style.index("az")])
                    linear_acceleration.append(acc_linear.x)
                    linear_acceleration.append(acc_linear.y)
                    linear_acceleration.append(acc_linear.z)

                displacement = self.displacement(linear_acceleration, each_step[1])
                last_index = each_step[2]

            if len(detected_step) > 0:
                if detected_step[-1][1] == -2:
                    self.walking = False
                else:
                    self.walking = True
                self.measurements = self.measurements[(last_index * self.measurement_column_count):]

            return {
                "measurements": self.measurements,
                "step_displacement": displacement
            }

        except (KeyError, Exception) as e:
            logger.error("Exception occured" + e)
            logger.error(traceback.format_exc())
            sys.exit()

    def displacement(self, linear_acceleration_data, _type=0):
        """

        :param linear_acceleration_data:
        :param _type:
        :return:
        """
        try:
            # data: acc_x, acc_y, acc_z, pressure,...
            displacement = Vector3()
            velocity = {"x": 0, "y": 0}

            # 3 because linear acceleration has 3 components (x,y,z)
            data_length = len(linear_acceleration_data) // 3

            for i in range(data_length):
                velocity["x"] += linear_acceleration_data[i * 3] * self.delta_time
                velocity["y"] += linear_acceleration_data[i * 3 + 1] * self.delta_time
                displacement.x += velocity["x"] * self.delta_time
                displacement.y += velocity["y"] * self.delta_time
                displacement.z += 0  # No displacement in Z direction as we dont measure pressure

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

            # update steps
            self.update_steps(displacement)

            return {
                "displacement": displacement
            }
        except (KeyError, Exception) as e:
            logger.error("Exception occured" + e)
            logger.error(traceback.format_exc())
            sys.exit()

    def update_steps(self, displacement):
        """

        :param displacement:
        :return:
        """
        try:
            step_length = math.sqrt(displacement.x ** 2 + displacement.y ** 2 + displacement.z ** 2)
            if (step_length < 0.1) or (step_length > 1.5):
                logger.warning(f"Invalid step length. step length: {step_length}")
                self.total_steps.append(None)
            else:
                logger.debug(f"step length detected. step length: {step_length}")
                self.total_step_count += 1
                self.total_steps.append(step_length)
        except Exception as e:
            logger.error("Exception occured" + e)
            logger.error(traceback.format_exc())
            sys.exit()


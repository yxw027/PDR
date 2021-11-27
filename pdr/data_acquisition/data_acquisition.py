import math
import sys
import logging
import traceback
from pdr.quaternion import Quaternion

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger("Data Acquisition:")


class DataAcquisition:
    """

    """
    def __init__(self, setup_config):
        """

        :param setup_config:
        """
        try:
            self.measurement_column_count = len(setup_config["measurements"]["column_style"])
            self.measurement_column_style = setup_config["measurements"]["column_style"]
            self.calibrate = setup_config["time"]["calibrate"]
            self.start = setup_config["time"]["start"]
            self.end = setup_config["time"]["end"]
            self.file_path = setup_config["measurements"]["file_path"]
            self.measurements = []
            self.quaternion = Quaternion()
        except (KeyError, Exception) as e:
            logger.error("Exception Occurred:" + e)
            logger.error(traceback.format_exc())
            sys.exit()

    def read_data_from_csv(self):
        """

        :return:
        """
        try:
            csv_file = open(self.file_path, 'r')
        except FileNotFoundError as e:
            logger.error("CSV file not found. Check csv file_path in configuration")
            sys.exit()

        try:
            first_line = csv_file.readline()
            column_style = map(str,first_line.split(','))
            if set(column_style) != set(self.measurement_column_style):
                raise ValueError("Column style not matching. Check column field pattern in CSV")

            deg2rad = lambda: math.pi / 180.0

            measurements = []
            new_column_style = []
            buffer_size = 0
            buffer_size_max = 800

            for each_line in csv_file.readlines():
                columns = each_line.split(',')
                current_time = float(columns[0])
                each_measurement = []
                for i in range(1, 7):
                    each_measurement.append(float(columns[i]))
                if current_time > self.end:  # time end is given timer.txt file
                    break
                elif current_time > self.start > self.calibrate:
                    measurements.extend(each_measurement)
                    buffer_size += 1
                    if buffer_size > buffer_size_max:
                        self.measurements.extend(measurements)
                        new_column_style = [ele for index, ele in enumerate(self.measurement_column_style) if index != 0]
                        break
                else:
                    self.quaternion.Update(
                        each_measurement[0] * deg2rad,
                        each_measurement[1] * deg2rad,
                        each_measurement[2] * deg2rad,
                        each_measurement[3],
                        each_measurement[4],
                        each_measurement[5],
                        self.delta_time,
                        self.beta,
                        self.epsilon
                    )
            csv_file.close()
            return {
                "measurements": self.measurements,
                "column_style": new_column_style,
                "quaternion": self.quaternion
            }
        except ValueError as e:
            logger.error(e)
            sys.exit()
        except Exception as e:
            logger.error("Exception occured" + e)
            logger.error(traceback.format_exc())
            sys.exit()

"""Command-Line Utility Python Script to be installed as binary
   usage: robot-generator -c /path/to/config.yaml
"""

import argparse
import asyncio
import functools
import logging
import os
import signal
import sys
import yaml
from step_detection import StepDetection
from data_acquisition import DataAcquisition

logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')

# logger for this file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/pdr.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# TURN OFF asyncio logger
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.setLevel(logging.WARNING)

wdt_logger = logging.getLogger('watchdog_timer')
wdt_logger.setLevel(logging.WARNING)

# Global objects are defined here
is_sighup_received = False


def _graceful_shutdown():
    """
    Do things needed before application shutdown
    :return: NA
    """
    return


def parse_arguments():
    """Arguments to run the script"""
    parser = argparse.ArgumentParser(description='PDR')
    parser.add_argument('--config', '-c', required=True, help='YAML Configuration File for PDR with path')
    return parser.parse_args()


def sighup_handler(name):
    """SIGHUP HANDLER"""
    # logger.debug(f'signal_handler {name}')
    logger.info('Updating the PDR Configuration')
    global is_sighup_received
    is_sighup_received = True


async def app(eventloop, config):
    """Main application for PDR"""
    global is_sighup_received
    data_acquisition_agent = None
    step_detection_agent = None

    while True:
        # Read configuration
        try:
            pdr_config = read_config(config)
        except Exception as e:
            logger.error('Error while reading configuration:')
            logger.error(e)
            break

        logger.debug("Robot Generator Version: %s", pdr_config['version'])

        # setup or init pdr
        try:
            data_acquisition_agent = DataAcquisition(setup_config=pdr_config["setup"])
        except Exception as e:
            logger.error("Failed to Init Data Acquisition")
            sys.exit()

        # read measurement csv file
        data_acquisition_packet = data_acquisition_agent.read_data_from_csv()
        if "measurements" and "column_style" and "quaternion" in data_acquisition_packet:
            if data_acquisition_packet["measurements"] is not None and \
                    data_acquisition_packet["column_style"] is not None and \
                    data_acquisition_packet["quaternion"] is not None:
                try:
                    step_detection_agent = StepDetection(step_detection_config=pdr_config["step_detection"],
                                                         data_acquisition_packet=data_acquisition_packet)
                except Exception as e:
                    logger.error("Step detection failed to initialize")
                    sys.exit()
            else:
                raise ValueError("Data Acquisition failed to process data. Stopping now")
        else:
            raise KeyError("Data acquisition packet does not contain required fields")

        # continuously monitor signal handle and update robot motion
        while not is_sighup_received:
            step_detection_agent.detect()
            break  # because only one file processed for now. Batch processing not supported

        # If SIGHUP Occurs, Delete the instances
        _graceful_shutdown()

        # reset sighup handler flag
        is_sighup_received = False


def read_config(yaml_config_file):
    """Parse the given Configuration File"""
    if os.path.exists(yaml_config_file):
        with open(yaml_config_file, 'r') as config_file:
            yaml_as_dict = yaml.load(config_file, Loader=yaml.FullLoader)
        return yaml_as_dict['pdr']
    else:
        logger.error('YAML Configuration File not Found.')
        raise FileNotFoundError


def main():
    """Initialization"""
    args = parse_arguments()
    if not os.path.isfile(args.config):
        logging.error("configuration file not readable. Check path to configuration file")
        sys.exit(-1)

    event_loop = asyncio.get_event_loop()
    event_loop.add_signal_handler(signal.SIGHUP, functools.partial(sighup_handler, name='SIGHUP'))
    try:
        event_loop.run_until_complete(app(event_loop, args.config))
    except KeyboardInterrupt:
        logger.error('CTRL+C Pressed')
        _graceful_shutdown()


if __name__ == "__main__":
    main()

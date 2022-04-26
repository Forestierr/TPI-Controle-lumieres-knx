""" Log.py | Robin Forestier | 9.03.2022

This file is used to generate log file.
"""

import logging
from os import path


def create_log_file():
    """Create a log file if it doesn't exist"""

    if not path.exists("camera.log"):

        logging.basicConfig(filename='camera.log',
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            encoding='utf-8',
                            level=logging.DEBUG)

        logging.info(" *** Create Log file ***")


def log(type, msg):
    """Create a new line in the docs file
    :param type: info, debug, warning, error, critical
    :param msg: The message you want to log
    """

    # Creating a log file if it doesn't exist.
    create_log_file()

    if type == 'info':
        logging.info(msg)
    elif type == 'debug':
        logging.debug(msg)
    elif type == 'warning':
        logging.warning(msg)
    elif type == 'error':
        logging.error(msg)
    elif type == 'critical':
        logging.critical(msg)
    else:
        logging.info(msg)


if __name__ == '__main__':
    pass

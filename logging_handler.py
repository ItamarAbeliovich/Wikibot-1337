import logging
import os

# ~~~ Logging Constants ~~~ #
LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)-15s logging_handler.py %(levelname)-8s %(message)s"
LOGGING_FILE = "Logs/main.log"
# ~~~~~~~~~~~~~~~~~~~~~~~~~ #

# ~~~ Error Constants ~~~ #
FILE_DOESNT_EXIST = "Error! The log file does not exist. "
INCORRECT_LOGGER_INPUT = "Error! The logger must be a valid logging.Logger object. "
INCORRECT_FILE_TYPE = "Error! The file variable must be a string. "

ERROR_DETAILS = "Detailed message: {}"
FILE_PERMISSION_ERROR = "Error! There was a problem with the file's permissions. " + ERROR_DETAILS
# ~~~~~~~~~~~~~~~~~~~~~~~ #

logger = logging.getLogger(__name__)


def logger_to_file(old_logger, file, level=LOGGING_LEVEL, log_format=LOGGING_FORMAT):
    """ This function configures the module's logger - severity, file handling and formatting.
            It accepts a logger, configures it using default or inputted variables and returns it.
            If the mandatory input is incorrect - logger or file not entered correctly,
            file doesn't exist or lacks permissions, log the error and raise an appropriate exception and message

    :param logging.Logger old_logger: The logger to be configured and returned
    :param str file: The file to store the logs in
    :param log_format: The format in which the logs should be saved
    :param level: The logging level logging.(DEBUG, INFO, WARNING, ERROR, CRITICAL)

    :return logging.Logger old_logger: The configured logger
    :except PermissionError:
    :raise TypeError: With an appropriate message if the logger or file variables are of the wrong type
    :raise FileNotFoundError: With an appropriate message if the file doesn't exist
    """

    if not isinstance(old_logger, logging.Logger):
        logger.error(INCORRECT_LOGGER_INPUT)
        raise TypeError(INCORRECT_LOGGER_INPUT)
    elif not isinstance(file, str):
        logger.error(INCORRECT_FILE_TYPE)
        raise TypeError(INCORRECT_FILE_TYPE)
    elif not os.path.exists(file):
        logger.error(FILE_DOESNT_EXIST)
        raise FileNotFoundError(FILE_DOESNT_EXIST)

    # setting the logger's level
    old_logger.setLevel(level)

    # create file handler which logs even @LOGGING_LEVEL messages to @LOGGING_FILE
    fh = logging.FileHandler(file)
    fh.setLevel(level)

    # create formatter that uses @LOGGING_FORMAT and add it to the handlers
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)

    # add the handler to old_logger
    old_logger.addHandler(fh)

    return old_logger


def logger_to_console(old_logger, level=LOGGING_LEVEL, log_format=LOGGING_FORMAT):
    pass


logger = logger_to_file(logger, LOGGING_FILE)

print(logger_to_file(logger, "Logs/noperm.log"))

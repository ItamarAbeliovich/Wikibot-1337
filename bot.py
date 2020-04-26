import facebook_handler, logging_handler
import configparser, os

import logging


# ~~~ Globals ~~~ #

DEFAULT_CONF_HEAD = "BotConf"
DEFAULT_CONF_CONTENTS = {"LogToConsole": True}

CONF_PATH = "Configurations/bot.conf"
# ~~~~~~~~~~~~~~~ #

# ~~ Logging Globals ~~ #
FAILURE_DETAILS = "Detailed Error: {}"
LOG_ERROR = "Could not perform action. " + FAILURE_DETAILS
LOG_PERMISSION_ERROR = "Could not access file due to a permission error. " + FAILURE_DETAILS

LOGGING_FILE = "Logs/bot.log"
LOGGING_LEVEL = logging.DEBUG
# ~~~~~~~~~~~~~~~~~~~~~ #

# Global conf variable
botConf = ""

# Creating the logger and configuring it in conf_logger to save the logs to @LOGGING_FILE
# TODO - Optional log to console
logger = logging.getLogger(__name__)
logger = logging_handler.logger_to_file(logger, LOGGING_FILE, level=LOGGING_LEVEL)


def reset_conf():
    """

    :return:
    :except PermissionError: Return False, log error
    """

    try:
        config = configparser.ConfigParser()
        config[DEFAULT_CONF_HEAD] = DEFAULT_CONF_CONTENTS
        with open(CONF_PATH, "w") as configfile:
            config.write(configfile)
    except PermissionError as e:
        logger.error(LOG_PERMISSION_ERROR.format(e))

    return True


# TODO - CONF HANDLING
def handle_conf():
    global botConf

    if not os.path.exists(CONF_PATH):
        pass

    botConf = configparser.ConfigParser()
    botConf.read(CONF_PATH)

    print(botConf)


if __name__ == "__main__":
    # TODO - CONF HANDLING
    # reset_conf()
    # logger.error("NOOOO")
    facebook_handler.get_last_post(True)
    pass


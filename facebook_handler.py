import facebook, logging
import logging_handler
from requests.exceptions import ConnectionError

# The Facebook Graph token used to perform operations on the page.
# TODO - Find a neat way of combining this with the config
TOKEN = ''
with open('token.txt', 'rt') as tokenfile:
    TOKEN = tokenfile.read()

if not TOKEN:
    print('Could not read token from token.txt. Aborting.')
    exit()

# ~~ Logging Constants ~~ #
LOG_POST_SUCCESS = "Successfully posted! Post ID {0}"
LOG_COMMENT_SUCCESS = "Successfully commented! Comment ID {0}"
LOG_DELETE_SUCCESS = "Successfully deleted! Object ID {0}"
LOG_PULL_SUCCESS = "Successfully pulled feed!"

FAILURE_DETAILS = "Detailed Error: {}"
LOG_TOKEN_FAILURE = "Facebook GraphAPI Error. " + FAILURE_DETAILS
LOG_CONNECTION_ERROR = "Could not connect to facebook due to a network error. " + FAILURE_DETAILS
LOG_PULL_ERROR = "Could not pull feed. " + FAILURE_DETAILS

LOG_INVALID_VARIABLES_STR = "Could not proceed, variables have to be strings"
LOGGING_FILE = "Logs/facebook.log"
LOGGING_LEVEL = logging.INFO
# ~~~~~~~~~~~~~~~~~~~~~ #

# Creating the module's logger and configuring it with logging_handler.
logger = logging.getLogger(__name__)
logger = logging_handler.logger_to_file(logger, LOGGING_FILE, level=LOGGING_LEVEL)

# Connecting to Facebook Graph API
graph = facebook.GraphAPI(TOKEN)


def error_decorator(func):
    """ A decorator for common exceptions with the FacebookAPI:
            facebook.GraphAPIError and requests.exceptions.ConnectionError

    :param func: The function to decorate
    :return: func results
    :except facebook.GraphAPIError: Encountered a GraphAPI error. Log it and return False
    :except requests.exceptions.ConnectionError: Network error caused post failure. Log it and return False
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except facebook.GraphAPIError as e:
            # Handling facebook GraphAPI errors
            logger.error(LOG_TOKEN_FAILURE.format(e))
            return False
        except ConnectionError as e:
            # Handling connection errors and logging them
            logger.error(LOG_CONNECTION_ERROR.format(e))
            return False

    return wrapper


@error_decorator
def post_to_facebook(message):
    """ This function posts to facebook using the global TOKEN
        It posts the message parameter with a blank 400x1 image for not-being-taken-down purposes
                                                    (Hail Zucc that removes text only posts)
        Expecting to get @message as a string since there is no user input

    :param string message: The message the post should contain
    :return string: Post id
    """

    # Attempting to authenticate with the token and post the message    =
    post_id = graph.put_photo(image=open("Resources\\400.jpg", "rb"), message=message)["post_id"]

    # Success! Log and return the post id
    logger.info(LOG_POST_SUCCESS.format(post_id))
    return post_id


@error_decorator
def comment_on_post_id(comment, obj_id):
    """ Comments on object by ID

    :param comment: The text to comment
    :param obj_id: The object to comment on
    :return string: Comment ID on success
    :except @comment or @obj_id is not a string: Return False
    """

    if type(comment) != str or type(obj_id) != str:
        logger.error(LOG_INVALID_VARIABLES_STR)
        return False

    # Success! Log and return the post id
    comment_id = graph.put_comment(object_id=obj_id, message=comment)["id"]
    logging.info(LOG_COMMENT_SUCCESS.format(comment_id))
    return comment_id


@error_decorator
def comment_on_last_post(comment):
    """ This function comments on the most recent post in the bot's feed.
        Returns the comment's ID on success or False on failure or if @comment is not a string

    :param string comment: The string to be commented on the post
    :return string: The new comment's ID
    :except: Return False
    """

    if type(comment) != str:
        logger.error(LOG_INVALID_VARIABLES_STR)
        return False

    comment_id = graph.put_comment(object_id=get_last_post()["id"], message=comment)["id"]
    logger.info(LOG_COMMENT_SUCCESS.format(comment_id))

    return comment_id


@error_decorator
def get_last_post(verbose=False):
    """ This function returns the last post made by the bot in dictionary form.
            Pretty simple, the name gave it away didn't it? Why are you even reading this?

    :param bool verbose: Should the pull be logged
    :return string: Last post if it exists and has access to it, False if an error came up
    """

    last_post = graph.get_connections(id="me", connection_name="feed")["data"][0]

    if verbose:
        logger.info(LOG_PULL_SUCCESS)

    return last_post


@error_decorator
def delete_object(object_id, verbose=True):
    """ This function deletes an object by ID

    :param bool verbose: Should the action be logged
    :param object_id: The ID of the object to be deleted
    :return: True on success, False on failure
    """

    graph.delete_object(object_id)

    if verbose:
        logger.info(LOG_DELETE_SUCCESS.format(object_id))

    return True

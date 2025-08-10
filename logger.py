import logging
import sys


def get_logger(name):
    """Create and return a logger with the specified name."""
    # Create a logger object
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the log level you want

    # Create a console handler and set its log level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add the formatter to both handlers
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)

    # Avoid logging messages multiple times
    logger.propagate = False

    return logger

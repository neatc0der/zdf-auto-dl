# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
import inspect
import logging
import sys

from colorlog import ColoredFormatter, StreamHandler


def init_logger(level=logging.INFO, no_color=False):
    """
    Initialize loggers to certain log level and optional colorization.

    :param level: default log level for new loggers
    :param no_color: deactivate colorized log
    """
    if sys.stdin.isatty() and not no_color:
        color_formatter = ColoredFormatter(
            '%(message_log_color)s%(asctime)-15s %(log_color)s[%(levelname)s]'
            '%(message_log_color)s %(name)s.%(funcName)s:%(lineno)s %(message)s',
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'bold_black,bg_green',
                'INFO': 'bold_black,bg_white',
                'WARNING': 'bold_black,bg_yellow',
                'ERROR': 'bold_white,bg_red',
                'CRITICAL': 'bold_white,bg_red',
            },
            secondary_log_colors={
                'message': {
                    'DEBUG': 'reset,green',
                    'INFO': 'reset,white',
                    'WARNING': 'reset,yellow',
                    'ERROR': 'reset,red',
                    'CRITICAL': 'reset,red',
                }
            },
            style='%'
        )

        handler = StreamHandler()
        handler.setFormatter(color_formatter)

    else:
        formatter = logging.Formatter('%(asctime)-15s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)s %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

    if any(logging.root.handlers):
        logging.root.removeHandler(logging.root.handlers[0])

    logging.root.addHandler(handler)
    logging.root.setLevel(level)


def get_logger(name=None):
    """
    Returns logger according to given name.

    :param name: logger name
    :return: logger
    """
    inspect_result = inspect.stack()[2][1]
    if inspect_result.startswith('<frozen'):
        inspect_result = inspect.stack()[1][1]

    logger_name = inspect_result.rpartition('.')[0].replace('/', '.').rpartition(
        'zdf_auto_dl.'
    )[-1].partition('.__init__')[0]
    if name is not None:
        logger_name += '.%s' % name

    return logging.getLogger(logger_name)


def add_logger(decorated_cls):
    """
    Adds logger to decorated class.

    :param decorated_cls: class to be extended
    :return: extended class
    """
    decorated_cls.logger = get_logger(decorated_cls.__name__)

    return decorated_cls

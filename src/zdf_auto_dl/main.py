#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main.

:authors: - Tobias Grosch
"""
import argparse
import locale
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zdf_auto_dl.action import ZdfDownloader
from zdf_auto_dl.config import ConfigurationLoader
from zdf_auto_dl.exceptions import DownloaderException
from zdf_auto_dl.logger import init_logger, get_logger


CONFIG_FILE_DEFAULT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'config', 'zdf.ini')
)


def get_arguments(argv):
    parser = argparse.ArgumentParser(description='ZDF Mediathek Auto Downloader')

    parser.add_argument(
        '-c',
        '--config',
        metavar='CONFIG_FILE',
        default=CONFIG_FILE_DEFAULT_PATH,
        help='set path to configuration file',
    )
    parser.add_argument('-f', '--find', action='store_true', help='display available episodes only (no download)')
    parser.add_argument('-l', '--log-level', metavar='LOG_LEVEL', default='INFO', help='set log level')
    parser.add_argument('-p', '--progress', action='store_true', help='print download progress')
    parser.add_argument('--no-color', action='store_true', help='disable colorize output')

    return parser.parse_args(argv[1:])


def execute(arguments):
    locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
    config = ConfigurationLoader.get_config(arguments)

    downloader = ZdfDownloader(config)
    downloader.start()


def main(argv=sys.argv):
    arguments = get_arguments(argv)

    init_logger(arguments.log_level.upper())
    logger = get_logger()

    logger.debug('start processing')

    try:
        execute(arguments)

    except KeyboardInterrupt:
        logger.info('execution interrupted by user')

    except DownloaderException as error:
        logger.error(error)

    except Exception as error:
        logger.exception(error)

    finally:
        logger.debug('finished processing')


if __name__ == '__main__':
    main()

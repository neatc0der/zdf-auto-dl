# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import

import codecs
import os
import sys

from zdf_auto_dl.logger import add_logger
from .content import Configuration
from .exceptions import ConfigurationError

if sys.version[0] == 2:
    from ConfigParser import ConfigParser

else:
    from configparser import ConfigParser


@add_logger
class ConfigurationLoader(object):
    @classmethod
    def get_config(cls, arguments):
        config_file = arguments.config

        if not os.path.isfile(config_file):
            raise ConfigurationError('configuration file not found: %s' % config_file)

        cls.logger.debug('using config file: %s' % config_file)

        config_parser = ConfigParser()
        with codecs.open(config_file, "r", "utf8") as config_fp:
            if hasattr(config_parser, 'read_file'):
                config_parser.read_file(config_fp)
            else:
                config_parser.readfp(config_fp)

        return Configuration(arguments, config_parser)

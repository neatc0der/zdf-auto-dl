# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import

import os
import shlex

import six
import sys

from zdf_auto_dl.logger import add_logger
from .exceptions import ConfigurationError

if sys.version[0] == 2:
    from ConfigParser import NoOptionError, NoSectionError

else:
    from configparser import NoOptionError, NoSectionError


@add_logger
class Configuration(object):
    def __init__(self, arguments, config_parser):
        self.progress = arguments.progress

        self.speed_limit = self._get_value(config_parser, 'user', 'speed')
        self.previous_episodes = self._get_value(config_parser, 'user', 'previous')
        self.shows = self._get_value(config_parser, 'user', 'shows')
        self.media_dir = self._get_value(config_parser, 'user', 'media_dir')
        self.filename_format = self._get_value(config_parser, 'user', 'filename')
        self.finish_script = self._get_value(config_parser, 'user', 'finished')

        self._validate()

    def _get_value(self, config_parser, section, option):
        try:
            return config_parser.get(section, option)

        except (NoOptionError, NoSectionError) as error:
            self.logger.warn(error)

    def _validate(self):
        if self.speed_limit is not None:
            if isinstance(self.speed_limit, six.string_types) and self.speed_limit.isdigit():
                self.speed_limit = int(self.speed_limit)

            else:
                self.logger.warn('unsupported value for speed limit: %r' % self.speed_limit)
                self.speed_limit = None

        if isinstance(self.previous_episodes, six.string_types) and self.previous_episodes.isdigit():
            self.previous_episodes = int(self.previous_episodes)

        if not isinstance(self.previous_episodes, int) or self.previous_episodes < 1:
            if self.previous_episodes is not None:
                self.logger.warn('unsupported value for previous episodes: %r' % self.previous_episodes)
            self.previous_episodes = 1

        if isinstance(self.shows, six.string_types):
            self.shows = self.shows.split(',')

        else:
            raise ConfigurationError('no shows to download')

        if isinstance(self.media_dir, six.string_types):
            if not os.path.isdir(self.media_dir):
                os.makedirs(self.media_dir)

        else:
            raise ConfigurationError('no media directory defined')

        if not isinstance(self.filename_format, six.string_types) or not self.filename_format:
            raise ConfigurationError('no file name defined')

        if not isinstance(self.finish_script, six.string_types) or not self.finish_script:
            self.finish_script = None
            self.logger.debug('no finish script was defined')

        else:
            cmd = shlex.split(self.finish_script)
            if not os.path.isfile(cmd[0]):
                self.logger.error('configured finish script does not exist: %s' % cmd[0])
                self.finish_script = None

            elif not os.access(cmd[0], os.X_OK):
                self.logger.error('configured finish script is not executable: %s' % cmd[0])
                self.finish_script = None

        self.logger.debug('configuration validation complete')

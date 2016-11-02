# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from zdf_auto_dl.exceptions import DownloaderException


class ConfigurationWarning(Warning):
    def __init__(self, *args, **kwargs):
        super(ConfigurationWarning, self).__init__(*args, **kwargs)


class ConfigurationError(DownloaderException):
    def __init__(self, *args, **kwargs):
        super(ConfigurationError, self).__init__(*args, **kwargs)

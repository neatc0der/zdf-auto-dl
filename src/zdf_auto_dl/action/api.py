# -*- coding: utf-8 -*-
"""

:copyright: GNS Systems GmbH, 2016

:authors: - Tobias Grosch (GNS Systems GmbH)
"""
import requests


class ApiKeyCollector(object):
    _KEY = None

    @classmethod
    def get_api_key(cls, config_url=None):
        if cls._KEY is None and config_url is not None:
            result = requests.get(config_url)

            cls._KEY = result.json()['apiToken']

        return cls._KEY

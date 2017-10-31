# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
import requests


class ApiTokenStorage(object):
    _API_TOKEN = None

    @classmethod
    def set_api_token(cls, api_token):
        cls._API_TOKEN = api_token

    @classmethod
    def get_api_token(cls):
        return cls._API_TOKEN

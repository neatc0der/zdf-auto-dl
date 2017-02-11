# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
import os


class RegisterFactory:
    @staticmethod
    def get_register(arguments, config_parser):
        return SimpleRegister()


class SimpleRegister:
    def check(self, file_path):
        return os.path.isfile(sile_path)

    def add(self, file_path):
        pass


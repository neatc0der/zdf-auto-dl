# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""


class DownloaderException(Exception):
    def __init__(self, *args, **kwargs):
        super(DownloaderException, self).__init__(*args, **kwargs)

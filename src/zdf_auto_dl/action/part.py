# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import

import math
import requests
import sys
import time

from zdf_auto_dl.logger import add_logger
from .api import ApiTokenStorage
from .buffer import RingBuffer


@add_logger
class PartDownloader(object):
    # todo: refactor

    def __init__(self, config, link, target_file):
        self.config = config
        self.link = link
        self.target_file = target_file

    def start(self):
        self.logger.debug('starting download of a single part: %s' % self.link)

        r = requests.get(self.link, headers={'Api-Auth': 'Bearer %s' % ApiTokenStorage.get_api_token()}, stream=True)

        chunk_max = math.ceil(float(r.headers.get('content-length'))/1024)

        ticks = RingBuffer(50)
        i = 0
        start = time.time()
        ticks.append(start)
        sleep_time = 0

        with open(self.target_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    i += 1

                    percent = float(i * 100) / chunk_max
                    speed = float(len(ticks.data)) / (time.time() - ticks.get())
                    ticks.append(time.time())

                    if self.config.progress:
                        sys.stdout.write('\r%.1f %% - %.1f KB/s speed     ' % (percent, speed))

                    if self.config.speed_limit is None:
                        continue

                    waiting_time = 1024.0 * (1.0 / self.config.speed_limit - 1.0 / speed)
                    if waiting_time > sleep_time:
                        sleep_time += 0.000001

                    if sleep_time > 0:
                        if waiting_time < sleep_time:
                            sleep_time -= 0.000001

                        if sleep_time > 0:
                            time.sleep(sleep_time)

                        else:
                            sleep_time = 0

        sys.stdout.write('\n')

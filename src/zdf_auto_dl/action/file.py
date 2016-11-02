# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import

import shlex
import subprocess

import dateutil.parser
import json
import math
import os
import re
import requests
import sys
import time
from lxml import html

from zdf_auto_dl.logger import add_logger
from .buffer import RingBuffer


@add_logger
class ZdfExtractor(object):
    DATE_REGEX = re.compile(r'^.* vom (?P<date>((\d{1,2}\.){2}\d{4})|(\d{2}. (?P<month>\w+) \d{4})).*$', re.IGNORECASE)

    MONTH_TRANSLATION = {
        'Januar': 'January',
        'Februar': 'February',
        'März': 'March',
        'Mai': 'May',
        'Juni': 'June',
        'Juli': 'July',
        'Oktober': 'October',
        'Dezember': 'December',
    }

    MONTHS = tuple(MONTH_TRANSLATION.keys())

    def __init__(self, show, content):
        self.show = show
        self.document = html.fromstring(content.encode("utf8"))

    def get_episodes(self):
        title_elements = self.document.cssselect('a.teaser-title-link')
        episodes = {}
        for title_element in title_elements:
            episode_title = title_element.text_content().strip()
            if self.show.lower() not in episode_title.lower():
                continue

            match = self.DATE_REGEX.match(episode_title)
            if match is None:
                continue

            episode_date_str = match.group('date')
            if match.group('month') in self.MONTHS:
                episode_date_str = episode_date_str.replace(
                    match.group('month'),
                    self.MONTH_TRANSLATION[match.group('month')],
                )

            episode_date = dateutil.parser.parse(episode_date_str)
            episodes[episode_date] = ZdfDownloader.BASE_URL + title_element.get('href').strip()

        self.logger.debug('found %i fitting episodes of %i results' % (len(episodes), len(title_elements)))

        return episodes


@add_logger
class ZdfDownloader(object):
    API_BASE_URL = 'https://api.zdf.de'
    BASE_URL = 'https://www.zdf.de'
    SEARCH_URL = BASE_URL + '/suche'

    BANDWIDTH_REGEX = re.compile(r'^.*BANDWIDTH=(?P<bandwidth>\d+).*$')
    FORMAT_REGEX = re.compile(r'^.*\.(?P<format>[a-zA-Z0-9]+)(\?.*)?$')

    API_KEY = None

    def __init__(self, config):
        self.config = config
        self.show = None

    def start(self):
        self.logger.debug('starting download')

        for show in self.config.shows:
            self._download_show(show)

        self.show = None

    def _download_show(self, show):
        self.logger.debug('searching show: %s' % show)

        self.show = show

        show_data = {
            'q': show,
            'contentTypes': 'episode',
        }
        result = requests.get(self.SEARCH_URL, show_data)

        extractor = ZdfExtractor(show, result.text)
        episodes = extractor.get_episodes()

        for episode_date in sorted(episodes.keys())[-self.config.previous_episodes:]:
            self._download_episode(episode_date, episodes[episode_date])

    @staticmethod
    def _get_video_data(video_url):
        result = requests.get(video_url)
        document = html.fromstring(result.text)

        video_data = document.cssselect('article.b-video-module div.js-rb-live')[0].get('data-zdfplayer-jsb')

        return json.loads(video_data)

    @classmethod
    def _get_api_key(cls, config_url):
        if cls.API_KEY is None:
            result = requests.get(config_url)

            cls.API_KEY = result.json()['apiToken']

        return cls.API_KEY

    def _get_best_quality_link(self, video_master_file):
        video_files = {}

        bandwidth = None
        for file_url in video_master_file.split('\n'):
            if file_url.strip().startswith('http'):
                if bandwidth is None:
                    self.logger.warn('there might be a problem during video bandwidth detection')
                    continue

                video_files[bandwidth] = file_url

            else:
                match = self.BANDWIDTH_REGEX.match(file_url)
                if match is not None:
                    bandwidth = int(match.group('bandwidth'))

        best_quality = max(video_files.keys())

        return video_files[best_quality]

    def _get_video_master(self, video_meta_url):
        video_meta_data = self._get_video_data(video_meta_url)
        config_path = video_meta_data['config']

        api_key = self._get_api_key(self.BASE_URL + config_path)
        content_url = video_meta_data['content']

        video_data = requests.get(content_url, headers={'Api-Auth': 'Bearer %s' % api_key}).json()
        attribute_path = video_data['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd']

        video_attribute_data = requests.get(self.API_BASE_URL + attribute_path).json()
        video_masters_url = \
            video_attribute_data['priorityList'][0]['formitaeten'][0]['qualities'][0]['audio']['tracks'][0]['uri']

        video_master_url = requests.get(video_masters_url).text
        return requests.get(self._get_best_quality_link(video_master_url)).text

    def _download_episode(self, episode_date, video_meta_url):
        video_master = self._get_video_master(video_meta_url)

        video_downloader = VideoDownloader(self.config, self.show, video_master, episode_date)
        video_downloader.start()


@add_logger
class VideoDownloader(object):
    def __init__(self, config, show, video_master, episode_date):
        self.config = config
        self.show = show
        self.video_master = video_master

        self.episode_date = episode_date
        self.season, self.episode = self._get_session_and_episode()
        self.format = 'ts'

        self.target_file = self._get_output_file()
        self.episode_name = os.path.basename(self.target_file).rpartition('.')[0]
        self.temp_dir = os.path.join(self.config.media_dir, self.show, self.episode_name)

    def _get_session_and_episode(self):
        # todo: determine season and episode
        return '00', self.episode_date.strftime('%Y%m%d')

    def _get_output_file(self):
        return os.path.join(
            self.config.media_dir,
            self.show,
            self.config.filename_format.format(
                show=self.show,
                season=self.season,
                episode=self.episode,
                date=self.episode_date,
                format=self.format,
            ),
        )

    def start(self):
        if os.path.isfile(self.target_file):
            self.logger.debug('file already exists')
            return

        self.logger.debug('starting download of parts')

        if not os.path.isdir(self.temp_dir):
            os.makedirs(self.temp_dir)

        try:
            self._download()

        finally:
            for part_file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, part_file))

            os.rmdir(self.temp_dir)

    def _download(self):
        parts = []
        for part_url in self.video_master.split('\n'):
            if not part_url.strip().startswith('http'):
                continue

            part_file = self._get_part_path(part_url)
            parts.append(part_file)

            part_downloader = PartDownloader(self.config, part_url, part_file)
            part_downloader.start()

        self._join_files(parts)
        self._call_finish()

    def _get_part_path(self, part_url):
        part_name = part_url.partition('?')[0].rpartition('/')[-1]

        return os.path.join(self.temp_dir, part_name)

    def _join_files(self, parts):
        self.logger.debug('joining %i parts to a single video file' % len(parts))

        with open(self.target_file, 'wb') as target_fp:
            for part_file in parts:
                with open(part_file, 'rb') as source_fp:
                    target_fp.write(source_fp.read())

    def _call_finish(self):
        if self.config.finish_script is None:
            return

        self.logger.debug('executing finish script')
        cmd = shlex.split(self.config.finish_script.format(
            show=self.show,
            season=self.season,
            episode=self.episode,
            date=self.episode_date,
            format=self.format,
        ))

        subprocess.call(cmd)


@add_logger
class PartDownloader(object):
    # todo: refactor

    def __init__(self, config, link, target_file):
        self.config = config
        self.link = link
        self.target_file = target_file

    def start(self):
        self.logger.debug('starting download of a single part: %s' % self.link)

        r = requests.get(self.link, headers={'Api-Auth': 'Bearer %s' % ZdfDownloader.API_KEY}, stream=True)

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
                    waiting_time = 1024.0 * (1.0 / self.config.speed_limit - 1.0 / speed)

                    if self.config.progress:
                        sys.stdout.write('\r%.1f %% - %.1f KB/s speed     ' % (percent, speed))

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

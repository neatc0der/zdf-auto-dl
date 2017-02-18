# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import, print_function

import json
import re
import requests
from lxml import html

from zdf_auto_dl.logger import add_logger
from .api import ApiKeyCollector
from .buffer import RingBuffer
from .episode import EpisodeData
from .extractor import ZdfExtractor
from .file import VideoDownloader


@add_logger
class ZdfDownloader(object):
    API_BASE_URL = 'https://api.zdf.de'
    SEARCH_URL = ZdfExtractor.BASE_URL + '/suche'

    BANDWIDTH_REGEX = re.compile(r'^.*BANDWIDTH=(?P<bandwidth>\d+).*$')
    FORMAT_REGEX = re.compile(r'^.*\.(?P<format>[a-zA-Z0-9]+)(\?.*)?$')

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
        result = requests.get(self.SEARCH_URL, params=show_data)

        zdf_extractor = ZdfExtractor(show, result.text)
        episodes = zdf_extractor.get_episodes()

        for episode_date in sorted(episodes.keys())[-self.config.previous_episodes:]:
            episode_data = EpisodeData(self.show, episode_date)
            episode_data.retrieve()

            if self.config.find is True:
                print('found: {show} (S{season}E{episode})'.format(**episode_data.as_dict()))
            else:
                self._download_episode(episode_data, episodes[episode_date])

    @staticmethod
    def _get_video_data(video_url):
        result = requests.get(video_url)
        document = html.fromstring(result.text)

        video_data = document.cssselect('article.b-video-module div.js-rb-live')[0].get('data-zdfplayer-jsb')

        return json.loads(video_data)

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

        api_key = ApiKeyCollector.get_api_key(ZdfExtractor.BASE_URL + config_path)
        content_url = video_meta_data['content']

        video_data = requests.get(content_url, headers={'Api-Auth': 'Bearer %s' % api_key}).json()
        attribute_path = video_data['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd']

        response = requests.get(self.API_BASE_URL + attribute_path)
        try:
            video_attribute_data = response.json()
        except json.decoder.JSONDecodeError:
            self.logger.error('unable to parse video attribute data for show "%s": %s' % (self.show, response.text))
            self.logger.debug('url responsible for error: %s' % response.url)
            return

        video_masters_url = \
            video_attribute_data['priorityList'][0]['formitaeten'][0]['qualities'][0]['audio']['tracks'][0]['uri']

        video_master_url = requests.get(video_masters_url).text
        return requests.get(self._get_best_quality_link(video_master_url)).text

    def _download_episode(self, episode_data, video_meta_url):
        video_master = self._get_video_master(video_meta_url)

        if not video_master:
            self.logger.warn(
                'skipping episode S%sE%s for show %s' % (episode_data.season, episode_data.episode, self.show)
            )
            return

        video_downloader = VideoDownloader(self.config, self.show, video_master, episode_data)
        video_downloader.start()

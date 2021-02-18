# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
from __future__ import absolute_import

import os
import shlex
import subprocess

from zdf_auto_dl.logger import add_logger
from .part import PartDownloader


@add_logger
class VideoDownloader(object):
    def __init__(self, config, show, video_master, episode_data):
        self.config = config
        self.show = show
        self.video_master = video_master

        self.episode_data = episode_data
        self.format = 'ts'

        self.target_file = self._get_output_file()
        self.episode_name = os.path.basename(self.target_file).rpartition('.')[0]
        self.temp_dir = os.path.join(self.config.media_dir, self.show, self.episode_name)

    def _get_output_file(self):
        return os.path.join(
            self.config.media_dir,
            self.show,
            self.config.filename_format.format(
                format=self.format,
                **self.episode_data.as_dict()
            ),
        )

    def start(self):
        self.logger.info(
            'Starting download of episode S{0.season}E{0.episode} for show {1}'.format(self.episode_data, self.show)
        )

        if self.config.register.check(self.target_file):
            self.logger.info('episode already exists')
            return

        if not os.path.isdir(self.temp_dir):
            os.makedirs(self.temp_dir)

        try:
            self._download()
            self.config.register.add(self.target_file)

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
            format=self.format,
            **self.episode_data.as_dict()
        ))

        subprocess.call(cmd)

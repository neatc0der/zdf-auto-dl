# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""


class EpisodeData(object):
    def __init__(self, show, episode_date):
        self.show = show
        self.episode_date = episode_date

        self.season = None
        self.episode = None

    def retrieve(self):
        # todo: determine actual season and episode
        self.season = '00'
        self.episode = self.episode_date.strftime('%Y%m%d')

    def as_dict(self):
        return {
            'show': self.show,
            'season': self.season,
            'episode': self.episode,
            'date': self.episode_date,
        }

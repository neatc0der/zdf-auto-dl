# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""
import dateutil.parser
import json
import re
from lxml import html

from zdf_auto_dl.logger import add_logger


@add_logger
class ZdfExtractor(object):
    BASE_URL = 'https://www.zdf.de'
    DATE_REGEX = re.compile(r'^.* vom (?P<date>((\d{1,2}\.){2}\d{4})|(\d{1,2}\.? (?P<month>\w+) \d{4})).*$', re.IGNORECASE)

    TITLE_REGEX = re.compile(r'^.*\"actionDetail\":\s*\"(?P<title>.*)\"\s*}$')

    MONTH_TRANSLATION = {
        'januar': 'January',
        'februar': 'February',
        'maerz': 'March',
        'märz': 'March',
        'mai': 'May',
        'juni': 'June',
        'juli': 'July',
        'oktober': 'October',
        'dezember': 'December',
    }

    MONTHS = tuple(MONTH_TRANSLATION.keys())

    def __init__(self, show, content):
        self.show = show
        self.document = html.fromstring(content.encode("utf8"))

    def get_episodes(self):
        title_elements = self.document.cssselect('a.teaser-title-link')
        episodes = {}
        for title_element in title_elements:
            for title_attribute in ('data-track', 'title'):
                data_track = title_element.get(title_attribute)
                if data_track is None:
                    self.logger.warn('unable to find title: no data track in element "%s"' % title_element.text.replace('\n', ' ').strip())
                    continue

                if title_attribute == 'title':
                    episode_title = data_track

                else:
                    title_match = self.TITLE_REGEX.match(data_track.replace('\n', ' '))
                    if title_match is None:
                        self.logger.warn('unable to find title: %r' % data_track.replace('\n', ' '))
                        continue

                    episode_title = title_match.group('title').rpartition('Linkziel:')[-1].replace('-', ' ').strip()
                    if self.show.lower() not in episode_title.lower():
                        continue

                match = self.DATE_REGEX.match(episode_title)
                if match is None:
                    self.logger.warn('this should actually match the show, but cannot find date: %s' % episode_title)
                    continue

                episode_date_str = match.group('date')
                if match.group('month').lower() in self.MONTHS:
                    episode_date_str = episode_date_str.replace(
                        match.group('month'),
                        self.MONTH_TRANSLATION[match.group('month').lower()],
                    )

                episode_date = dateutil.parser.parse(episode_date_str)
                episodes[episode_date] = title_element.get('href').strip()

        self.logger.debug('found %i fitting episodes of %i results' % (len(episodes), len(title_elements)))

        return episodes

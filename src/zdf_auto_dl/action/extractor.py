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
    DATE_REGEX = re.compile(r'^.* vom (?P<date>((\d{1,2}\.){2}\d{4})|(\d{1,2}. (?P<month>\w+) \d{4})).*$', re.IGNORECASE)

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
            episode_title = json.loads(
                title_element.get('data-track')
            )['actionDetail'].rpartition('Teaser:')[-1].strip()
            if self.show.lower() not in episode_title.lower():
                continue

            match = self.DATE_REGEX.match(episode_title)
            if match is None:
                self.logger.warn('this should actually match the show: %s' % episode_title)
                continue

            episode_date_str = match.group('date')
            if match.group('month') in self.MONTHS:
                episode_date_str = episode_date_str.replace(
                    match.group('month'),
                    self.MONTH_TRANSLATION[match.group('month')],
                )

            episode_date = dateutil.parser.parse(episode_date_str)
            episodes[episode_date] = self.BASE_URL + title_element.get('href').strip()

        self.logger.debug('found %i fitting episodes of %i results' % (len(episodes), len(title_elements)))

        return episodes

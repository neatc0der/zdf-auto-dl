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
        title_elements = self.document.cssselect('article.b-content-teaser-item')
        episodes = {}
        for title_element in title_elements:
            if self.show.lower() not in title_element.cssselect('.teaser-cat-brand-ellipsis')[0].text.lower():
                continue
            episode_title = title_element.cssselect('a.teaser-title-link .normal-space')[0].text.strip()
            episode_date_str = title_element.cssselect('.special-info')[0].text.strip()
            episode_date = dateutil.parser.parse(episode_date_str)
            episodes[episode_date] = title_element.cssselect('a.teaser-title-link')[0].get('href').strip()

        self.logger.debug('found %i fitting episodes of %i results' % (len(episodes), len(title_elements)))

        return episodes

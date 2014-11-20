# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Representation of a (manifest) feed.'''

__all__ = ['Feed']

import collections
import datetime
import json
import re
import urllib.parse

import cc
import cc.http
import cc.pformat

from cc import logging


class Feed:
    '''The (manifest) feed of the show within a date range.'''

    @staticmethod
    def from_show_url(show_url):
        parts = urllib.parse.urlparse(show_url)
        new_parts = urllib.parse.ParseResult(scheme=parts.scheme,
                                             netloc=parts.netloc,
                                             path='/videos',
                                             params='',
                                             query='',
                                             fragment='')
        videos_url = urllib.parse.urlunparse(new_parts)
        return Feed(show_url, videos_url, None, None, None)

    def __init__(self, show_url, videos_url, url, start, end):
        '''You should use factory method(s) to construct Feed objects.'''
        self.show_url = show_url
        self.videos_url = videos_url
        self._url = url
        self._start = start
        self._end = end
        self._feed = None
        self._video_blobs = None

    def replace_date_range(self, start, end, step=None):
        if step is None:
            return [self._replace_date_range(start, end)]
        steps = {'y': 0, 'm': 0}
        for unit in 'ym':
            match = re.search(r'(\d+)' + unit, step, re.IGNORECASE)
            if match:
                steps[unit] = int(match.group(1))
        if all(v == 0 for v in steps.values()):
            raise cc.Error('date step is zero: %s' % step)
        feeds = []
        date = start
        while date < end:
            # Very naive date calculation.
            next_year = date.year + steps['y']
            next_month = date.month + steps['m']
            if next_month > 12:
                next_year += (next_month - 1) // 12
                next_month %= 12
                if next_month == 0:
                    next_month = 12
            next_date = date.replace(next_year, next_month)
            next_date = min(next_date, end)
            feeds.append(self._replace_date_range(date, next_date))
            date = next_date
        return feeds

    def _replace_date_range(self, start, end):
        match = re.fullmatch(r'(.*)/(\d+)/(\d+)', self.url)
        if not match:
            raise cc.Error('feed.url has no date: %s' % self.url)
        url = ('%s/%s/%s' %
               (match.group(1), int(start.timestamp()), int(end.timestamp())))
        return Feed(self.show_url, self.videos_url, url, start, end)

    @property
    def url(self):
        if self._url is None:
            props = ('manifest', 'zones', 't6_lc_promo1', 'feed')
            doc = cc.http.get_url(self.videos_url)
            self._url = _get_manifest_feed_property(doc, props)
        return self._url

    @property
    def start(self):
        if self._start is None:
            self._start, self._end = self._get_dates()
        return self._start

    @property
    def end(self):
        if self._end is None:
            self._start, self._end = self._get_dates()
        return self._end

    def _get_dates(self):
        match = re.search(r'/(\d+)/(\d+)$', self.url)
        if not match:
            raise cc.Error('Could not find dates in %s', self.url)
        return (datetime.datetime.fromtimestamp(int(match.group(1))),
                datetime.datetime.fromtimestamp(int(match.group(2))))

    @property
    def feed(self):
        if self._feed is None:
            self._feed = cc.http.get_url_json(self.url)
            logging.trace('feed.feed=\n%s',
                          cc.pformat.PrettyFormatter(self._feed))
        return self._feed

    @property
    def video_blobs(self):
        if self._video_blobs is None:
            self._video_blobs = []
            for video in self.feed['result']['videos']:
                page_url = video['canonicalURL']
                logging.debug('video_blobs: page_url=%s', page_url)
                # Zero out time part of datetime object.
                date = datetime.datetime.fromtimestamp(int(video['airDate']))
                date = datetime.datetime(date.year, date.month, date.day)
                page_doc = cc.http.get_url(page_url)
                self._video_blobs.append(VideoBlob(
                    uri=_get_uri(page_doc, video['id']),
                    page_url=page_url,
                    episode_url=_get_episode_url(page_doc),
                    date=date))
        return self._video_blobs


VideoBlob = collections.namedtuple(
    'VideoBlob', 'uri page_url episode_url date')


# uri format: mgid:arc:video:HOST_NAME:UUID
_PATTERN_URI = re.compile(
    r'(mgid:arc:video:'
    r'[^:]+:'
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')


def _get_uri(video_page_doc, uuid):
    for match in _PATTERN_URI.finditer(video_page_doc):
        uri = match.group(1)
        if uri.endswith(uuid):
            return uri
    raise cc.Error('Could not find uri')


def _get_episode_url(video_page_doc):
    props = ('manifest', 'zones', 't4_lc_promo1', 'feedData', 'result',
             'episode', 'canonicalURL')
    try:
        return _get_manifest_feed_property(video_page_doc, props)
    except (KeyError, cc.Error):
        return None


_PATTERN_MANIFEST_FEED = re.compile(r'var triforceManifestFeed = (.*);')


def _get_manifest_feed_property(manifest_feed_doc, property_names):
    '''Extract triforceManifestFeed from doc and read the nested property.'''
    match = _PATTERN_MANIFEST_FEED.search(manifest_feed_doc)
    if not match:
        raise cc.Error('Could not find manifest feed')
    manifest_feed = json.loads(match.group(1))
    logging.trace('triforceManifestFeed=\n%s',
                  cc.pformat.PrettyFormatter(manifest_feed))
    blob = manifest_feed
    for property_name in property_names:
        blob = blob[property_name]
    return blob

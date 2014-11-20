# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Representation of a video.'''

__all__ = ['Video']

import collections
import os.path
import re
import urllib.parse

import cc.http


class Video(collections.namedtuple(
        'Video', 'page_url episode_url fne date rtmps captions')):
    '''One video.

    Note: 'fne' stands for file name no extension.
    '''

    @staticmethod
    def make_videos(feed):
        videos = []
        part_indexes = collections.defaultdict(int)
        for video_blob in feed.video_blobs:
            fne = _make_fne(video_blob.page_url)
            if (video_blob.episode_url is not None and
                    not _look_like_recap_video(video_blob.page_url)):
                index = part_indexes[video_blob.episode_url] + 1
                part_indexes[video_blob.episode_url] = index
                fne = 'part-%d-%s' % (index, fne)
            mediagen_tree = _get_mediagen_tree(feed, video_blob)
            videos.append(Video(
                page_url=video_blob.page_url,
                episode_url=video_blob.episode_url,
                fne=fne,
                date=video_blob.date,
                rtmps=_get_rtmps(mediagen_tree),
                captions=_get_captions(mediagen_tree)))
        return videos


Rtmp = collections.namedtuple('Rtmp', 'url ext width height')


def _get_rtmps(mediagen_tree):
    rtmps = []
    for rendition in mediagen_tree.findall('.//rendition'):
        url = rendition.find('./src').text
        url = url.replace('viacomccstrm', 'viacommtvstrm')
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or '.mp4'
        width = int(rendition.get('width'))
        height = int(rendition.get('height'))
        rtmps.append(Rtmp(url=url, ext=ext, width=width, height=height))
    return rtmps


Caption = collections.namedtuple('Caption', 'url ext')


def _get_captions(mediagen_tree):
    captions = []
    for typographic in mediagen_tree.findall('.//typographic'):
        url = typographic.get('src')
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1]
        if not ext:
            ext = '.' + typographic.get('format')
        captions.append(Caption(url=url, ext=ext))
    return captions


def _get_mediagen_tree(feed, video_blob):
    parts = urllib.parse.urlparse(feed.show_url)
    new_parts = urllib.parse.ParseResult(
        scheme=parts.scheme,
        netloc=parts.netloc,
        path='feeds/mrss',
        params='',
        query=urllib.parse.urlencode({'uri': video_blob.uri}),
        fragment='')
    mrss_url = urllib.parse.urlunparse(new_parts)
    mrss_tree = cc.http.get_url_dom_tree(mrss_url)
    content = mrss_tree.find('.//{http://search.yahoo.com/mrss/}content')
    mediagen_url = content.get('url')
    return cc.http.get_url_dom_tree(mediagen_url)


_PATTERN_RECAP_VIDEO = re.compile(r'in-+60-+seconds|recap-+week-+of')


def _look_like_recap_video(video_page_url):
    return _PATTERN_RECAP_VIDEO.search(video_page_url) is not None


def _make_fne(url):
    '''Extract fne (file name no extension) part from url.'''
    return re.sub(r'-+', '-', url[url.rfind('/')+1:]).strip('-')

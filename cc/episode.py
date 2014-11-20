# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Representation of one episode.'''

__all__ = ['Episode']

import collections
import re

import cc
import cc.video


class Episode(collections.namedtuple('Episode', 'url date dir_name videos')):
    '''One episode of the show.'''

    @staticmethod
    def make_episodes(feed):
        '''Select Video object from feed and group by (date, episode_url).'''
        video_groups = collections.defaultdict(list)
        for video in cc.video.Video.make_videos(feed):
            video_groups[(video.date, video.episode_url)].append(video)
        episodes = [Episode(url=episode_url,
                            date=date,
                            dir_name=_make_dir_name(episode_url, date),
                            videos=videos)
                    for (date, episode_url), videos in video_groups.items()]
        return episodes


def _make_dir_name(episode_url, date):
    date_string = date.strftime('%Y-%m-%d')
    if episode_url is None:
        return date_string
    name = episode_url[episode_url.rfind('/')+1:]
    # XXX: Colbert Report uses a 'MONTH_STRING-DD-YYYY-GUEST_NAME' naming
    # rule; so slicing [:3] gets rid of the (duplicated) date part.
    name = '-'.join(re.split(r'-+', name)[3:]).strip('-')
    return '%s-%s' % (date_string, name)

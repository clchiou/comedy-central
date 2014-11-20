# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Actor starter.'''

__all__ = ['starter']

import datetime

import cc
import cc.actor
import cc.actor.downloader
import cc.episode
import cc.feed
import cc.inits

from cc import logging


@cc.inits.init(cc.inits.Level.EARLIER)
def init_argparser():

    def date(date_string):
        '''Parse date string of the form YYYY-MM-DD.'''
        return datetime.datetime.strptime(date_string, '%Y-%m-%d')

    parser = cc.statics.parser
    parser.add_argument(
        '--start', required=True, type=date,
        help='set start date (required, format: YYYY-MM-DD)')
    parser.add_argument(
        '--end', required=True, type=date,
        help='set end date (required, format: YYYY-MM-DD)')
    parser.add_argument(
        '--step', default='1m',
        help='set date step size (default: %(default)s)')
    parser.add_argument(
        'show_url',
        help='the show website, such as http://thecolbertreport.cc.com/')


@cc.inits.init
def init_check_dates():
    parser = cc.statics.parser
    args = cc.statics.args
    if args.start > args.end:
        parser.error('start date (%s) is later than end date (%s)' %
                     (args.start, args.end))


@cc.actor.actor
def starter():
    '''Start the actor formation!'''
    args = cc.statics.args
    _starter(args.show_url, args.start, args.end, args.step)


def _starter(show_url, start, end, step):
    logging.info('starter: show_url=%s', show_url)
    feed = cc.feed.Feed.from_show_url(show_url)
    logging.debug('feed...'
                  '\n  url=%s'
                  '\n  videos_url=%s'
                  '\n  start=%s'
                  '\n  end=%s',
                  feed.url, feed.videos_url, feed.start, feed.end)
    for sub_feed in feed.replace_date_range(start, end, step):
        starter_helper(sub_feed)


@cc.actor.actor
def starter_helper(sub_feed):
    '''Retrieve episodes and pass them to downloader().'''
    logging.info('starter_helper: sub_feed.url=%s', sub_feed.url)
    for episode in cc.episode.Episode.make_episodes(sub_feed):
        cc.actor.downloader.downloader(episode)

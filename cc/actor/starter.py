# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Actor starter.'''

__all__ = ['starter']

import datetime
import pickle
import threading

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
        '--start', type=date,
        help='set start date (required, format: YYYY-MM-DD)')
    parser.add_argument(
        '--end', type=date,
        help='set end date (required, format: YYYY-MM-DD)')
    parser.add_argument(
        '--step', default='1m',
        help='set date step size (default: %(default)s)')
    parser.add_argument(
        '--stash',
        help='store download job info to file')
    parser.add_argument(
        '--unstash',
        help='load download job info from file')
    parser.add_argument(
        'show_url',
        help='the show website, such as http://thecolbertreport.cc.com/')


@cc.inits.init
def init_check_args():
    parser = cc.statics.parser
    args = cc.statics.args
    if args.stash is not None and args.unstash is not None:
        parser.error('can only set either --stash or --unstash')
    if args.start is not None and args.end is not None:
        if args.unstash is not None:
            parser.error('cannot set both --unstash and --start/--end')
        if args.start > args.end:
            parser.error('start date (%s) is later than end date (%s)' %
                         (args.start, args.end))
    else:
        if args.unstash is None or args.stash is not None:
            parser.error('need at least --start and --end')


@cc.inits.init(cc.inits.Level.LATE)
def init_stash():
    args = cc.statics.args
    if args.stash is not None:
        cc.statics.pickle_file = open(args.stash, 'wb')
        cc.statics.pickle_lock = threading.RLock()
    elif args.unstash is not None:
        cc.statics.pickle_file = open(args.unstash, 'rb')
        cc.statics.pickle_lock = threading.RLock()


@cc.inits.final
def final_stash():
    args = cc.statics.args
    if args.stash is not None or args.unstash is not None:
        cc.statics.pickle_file.close()


@cc.actor.actor
def starter():
    '''Start the actor formation!'''
    args = cc.statics.args
    _starter(args.show_url,
             args.unstash is not None,
             args.start,
             args.end,
             args.step)


def _starter(show_url, is_unstashing, start, end, step):
    logging.info('starter: show_url=%s', show_url)
    if is_unstashing:
        with cc.statics.pickle_lock:
            pickle_file = cc.statics.pickle_file
            try:
                while True:
                    episode = pickle.load(pickle_file)
                    cc.actor.downloader.downloader(episode)
            except EOFError:
                pass
        return
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
    args = cc.statics.args
    _starter_helper(sub_feed, args.stash is not None)


def _starter_helper(sub_feed, is_stashing):
    logging.info('starter_helper: sub_feed.url=%s', sub_feed.url)
    for episode in cc.episode.Episode.make_episodes(sub_feed):
        if is_stashing:
            with cc.statics.pickle_lock:
                pickle.dump(episode, cc.statics.pickle_file)
        else:
            cc.actor.downloader.downloader(episode)

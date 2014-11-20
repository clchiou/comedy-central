# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Actor downloader.'''

__all__ = ['downloader']

import functools
import os
import os.path
import shutil
import tempfile

import cc
import cc.actor
import cc.actor.counter
import cc.http
import cc.inits
import cc.rtmp
import cc.pformat
import cc.salvage

from cc import logging


@cc.inits.init(cc.inits.Level.EARLIER)
def init_argparser():
    parser = cc.statics.parser
    parser.add_argument(
        '--output',
        help='set output directory (default: current directory)')
    parser.add_argument(
        '--simulate', action='store_true',
        help='do not download')
    parser.add_argument(
        '--salvage', action='append',
        help='add salvage directory')


@cc.actor.actor
def downloader(episode):
    '''Download an episode.'''
    _downloader(episode,
                cc.statics.args.output or os.getcwd(),
                bool(cc.statics.args.simulate),
                cc.statics.args.salvage or [])


def _downloader(episode, output_dir_path, simulate, salvage_dirs):
    logging.info('downloader: episode .date=%s .url=%s',
                 episode.date, episode.url)
    logging.trace('downloader: episode...'
                  '\n  url=%s'
                  '\n  dir_name=%s'
                  '\n  date=%s'
                  '\n  videos=\n%s',
                  episode.url, episode.dir_name, episode.date,
                  cc.pformat.PrettyFormatter(episode.videos))
    # Check/make paths.
    dir_path = os.path.join(output_dir_path, episode.dir_name)
    if os.path.exists(dir_path):
        logging.info('downloader: skip: dir_path=%s', dir_path)
        return
    salvage = cc.salvage.Salvage(episode.dir_name, salvage_dirs)
    if simulate:
        tmp_dir_path = os.path.join(
            output_dir_path, 'tmpXXXXXXXX-' + episode.dir_name)
    else:
        tmp_dir_path = tempfile.mkdtemp(
            suffix='-'+episode.dir_name, dir=output_dir_path)
    logging.debug('downloader: tmp_dir_path=%s', tmp_dir_path)
    # Construct actors.
    counter = cc.actor.counter.Counter(
        functools.partial(_downloader_success,
                          episode.url,
                          tmp_dir_path,
                          dir_path,
                          simulate),
        functools.partial(_downloader_failed,
                          episode.url))
    dlers = _make_dlers(episode, tmp_dir_path, counter, simulate, salvage)
    counter.count = len(dlers)
    # Start actors.
    for dler in dlers:
        dler()


def _make_dlers(episode, tmp_dir_path, counter, simulate, salvage):
    dlers = []
    for dl, url, fne, ext in _get_dls(episode):
        src_path = salvage.find(episode.dir_name, fne + ext)
        if src_path is not None:
            logging.debug('downloader: salvage: %s', src_path)
            dl, url = _dl_copy, src_path
        if simulate:
            dl = _dl_none
        dlers.append(functools.partial(
            _dler, dl, url, tmp_dir_path, fne, ext, counter))
    return dlers


def _get_dls(episode):
    if episode.url is not None:
        yield _dl_url, episode.url, 'index', '.html'
    for video in episode.videos:
        rtmp = max(video.rtmps, key=lambda r: r.width)
        yield _dl_rtmp, rtmp.url, video.fne, rtmp.ext
        for caption in video.captions:
            yield _dl_url, caption.url, video.fne, caption.ext


@cc.actor.actor
def _dler(dl, url, dir_path, fne, ext, counter):
    logging.debug(
        'downloader: %s -> %s', url, os.path.join(dir_path, fne + ext))
    try:
        dl(url, dir_path, fne, ext)
    except:
        counter.cancel()
        raise
    else:
        counter.countdown()


def _downloader_success(episode_url, tmp_dir_path, dir_path, simulate):
    logging.debug('downloader: %s -> %s', tmp_dir_path, dir_path)
    if not simulate:
        os.rename(tmp_dir_path, dir_path)
    logging.info('downloader: success: episode.url=%s', episode_url)


def _downloader_failed(episode_url):
    logging.error('downloader: error: episode.url=%s', episode_url)


def _dl_url(url, dir_path, fne, ext):
    doc = cc.http.get_url(url)
    with open(os.path.join(dir_path, fne + ext), 'w') as output:
        output.write(doc)


def _dl_copy(src_path, dir_path, *_):
    shutil.copy2(src_path, dir_path)


def _dl_rtmp(url, dir_path, fne, ext):
    cc.rtmp.download(url, fne + ext, cwd=dir_path)


def _dl_none(*_):
    pass

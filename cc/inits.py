# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Manage initializations.'''

__all__ = [
    'Level',
    'init',
    'run_inits',
    # Early logging machinery.
    'debug',
    'emit_early_logs',
    'log',
]

import collections
import enum
import functools
import logging

import cc


cc.statics.inits = cc.Namespace()
cc.statics.inits.levels = collections.defaultdict(list)
cc.statics.inits.log_buffer = []


class Level(enum.IntEnum):
    '''Initialization level.  You may add customized levels.'''
    EARLIEST = -30
    EARLIER = -20
    EARLY = -10
    NORMAL = 0
    LATE = 10
    LATER = 20
    LATEST = 30


def init(init_func=None, level=Level.NORMAL):
    '''Add init_func to the list of initializers.'''
    if init_func is None:
        return functools.partial(init, level=level)
    if not callable(init_func):
        return functools.partial(init, level=init_func)
    cc.statics.inits.levels[level].append(init_func)
    return init_func


def run_inits():
    for level in sorted(cc.statics.inits.levels):
        debug('inits: level=%s', getattr(level, 'name', level))
        # init_func is appended in reverse order of module dependency.
        # So add a reversed() here makes (although this does not change
        # behavior) init_argparser calls in a prettier order.
        for init_func in reversed(cc.statics.inits.levels[level]):
            debug('inits: run: %s.%s',
                  init_func.__module__, init_func.__name__)
            init_func()
    del cc.statics.inits


def emit_early_logs(log_func=None):
    '''Some logs might be logged before the logging module be
    configured; so we defer those logs, and emit them out later.
    '''
    log_func = log_func or logging.log
    for log in cc.statics.inits.log_buffer:
        log_func(*log[0], **log[1])
    log_func(logging.DEBUG, 'inits: remove log_buffer')
    cc.statics.inits.log_func = log_func
    del cc.statics.inits.log_buffer


def log(*args, **kwargs):
    if hasattr(cc.statics.inits, 'log_buffer'):
        cc.statics.inits.log_buffer.append((args, kwargs))
    else:
        cc.statics.inits.log_func(*args, **kwargs)


debug = functools.partial(log, logging.DEBUG)

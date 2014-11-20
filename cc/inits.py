# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Manage initializations.'''

__all__ = [
    'Level',
    'final',
    'init',
    'run_finals',
    'run_inits',
    # Early logging machinery.
    'emit_early_logs',
]

import collections
import enum
import functools
import logging

import cc


cc.statics.inits = cc.Namespace()
cc.statics.inits.levels = collections.defaultdict(list)
cc.statics.inits.early_log_buffer = []

cc.statics.finals = cc.Namespace()
cc.statics.finals.levels = collections.defaultdict(list)


class Level(enum.IntEnum):
    '''Initialization level.  You may add customized levels.'''
    EARLIEST = -30
    EARLIER = -20
    EARLY = -10
    NORMAL = 0
    LATE = 10
    LATER = 20
    LATEST = 30


def _register(func=None, level=Level.NORMAL, levels=None):
    '''Add func to the list of initializers or finalizers.'''
    if func is None:
        return functools.partial(init, level=level)
    if not callable(func):
        return functools.partial(init, level=func)
    levels[level].append(func)
    return func


init = functools.partial(_register, levels=cc.statics.inits.levels)
final = functools.partial(_register, levels=cc.statics.finals.levels)


def run_inits():
    for level in sorted(cc.statics.inits.levels):
        _log(logging.DEBUG, 'inits: level=%s', getattr(level, 'name', level))
        # init_func is appended in reverse order of module dependency.
        # So add a reversed() here makes (although this does not change
        # behavior) init_argparser calls in a prettier order.
        for init_func in reversed(cc.statics.inits.levels[level]):
            _log(logging.DEBUG,
                 'inits: run: %s.%s', init_func.__module__, init_func.__name__)
            init_func()
    del cc.statics.inits


def run_finals():
    import cc.logging  # Pull in cc.logging here to avoid circular importing.
    for level in sorted(cc.statics.finals.levels):
        cc.logging.debug('finals: level=%s', getattr(level, 'name', level))
        for func in reversed(cc.statics.finals.levels[level]):
            cc.logging.debug(
                'finals: run: %s.%s', func.__module__, func.__name__)
            func()
    del cc.statics.finals


def emit_early_logs(log_func=None):
    '''Some logs might be logged before the logging module be
    configured; so we defer those logs, and emit them out later.
    '''
    log_func = log_func or logging.log
    for log in cc.statics.inits.early_log_buffer:
        log_func(*log[0], **log[1])
    log_func(logging.DEBUG, 'inits: remove early_log_buffer')
    cc.statics.inits.log_func = log_func
    del cc.statics.inits.early_log_buffer


def _log(*args, **kwargs):
    if hasattr(cc.statics.inits, 'early_log_buffer'):
        cc.statics.inits.early_log_buffer.append((args, kwargs))
    else:
        cc.statics.inits.log_func(*args, **kwargs)

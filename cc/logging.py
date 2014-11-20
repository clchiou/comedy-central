# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Initialize logger.'''

__all__ = [
    'debug',
    'error',
    'exception',
    'info',
    'trace',
    'warning',
]

import functools
import logging

import cc.inits


# My extra level of logging.
TRACE = logging.DEBUG - 1

debug = None
error = None
exception = None
info = None
trace = None
warning = None


@cc.inits.init(cc.inits.Level.EARLIER)
def init_argparser():
    parser = cc.statics.parser
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='verbose output')


@cc.inits.init
def init_logging():
    global debug, error, exception, info, trace, warning
    args = cc.statics.args
    # Configure logger object.
    logging.addLevelName(TRACE, 'TRACE')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger = logging.getLogger('cc')
    logger.addHandler(handler)
    for count, level in ((3, TRACE), (2, logging.DEBUG), (1, logging.INFO)):
        if args.verbose >= count:
            logger.setLevel(level)
            break
    # Create log functions.
    debug = functools.partial(logger.log, logging.DEBUG)
    error = functools.partial(logger.log, logging.ERROR)
    exception = functools.partial(logger.log, logging.ERROR, exc_info=True)
    info = functools.partial(logger.log, logging.INFO)
    trace = functools.partial(logger.log, TRACE)
    warning = functools.partial(logger.log, logging.WARNING)
    # Now logging is ready; emit early logs.
    cc.inits.emit_early_logs(log_func=logger.log)

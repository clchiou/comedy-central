# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''A naive implementation of the actor model.'''

__all__ = [
    'actor',
    'interface',
    'join',
]

import collections
import functools
import itertools
import queue
import threading
import time

import cc
import cc.inits

from cc import logging


@cc.inits.init(cc.inits.Level.EARLIER)
def init_argparser():
    parser = cc.statics.parser
    # It seems like that Comedy Central limits the concurrent
    # connections to be 6.  Since rtmp.download() implements
    # exponential back-off, it should be okay to set --jobs
    # greater than 6.
    parser.add_argument(
        '-j', '--jobs', type=int, default=1,
        help='set number of worker threads (default: %(default)s)')
    parser.add_argument(
        '--queue', choices=('fifo', 'lifo'), default='fifo',
        help='set message queue type (default: %(default)s)')


@cc.inits.init(cc.inits.Level.LATE)
def init_threads():
    args = cc.statics.args
    if args.queue == 'fifo':
        cc.statics.message_queue = queue.Queue()
    else:
        cc.statics.message_queue = queue.LifoQueue()
    if args.jobs < 1:
        raise cc.Error('Could not set non-positive number of threads: %d',
                       args.jobs)
    for i in range(args.jobs):
        name = 'thread-%02d' % (i + 1)
        threading.Thread(target=thread_main, name=name, daemon=True).start()


class Message(collections.namedtuple('Message', 'obj func args kwargs')):

    def __str__(self):
        args_string = ', '.join(itertools.chain(
            (repr(a) for a in self.args),
            ('%s=%s' % (k, repr(a)) for k, a in self.kwargs.items())))
        if self.obj is None:
            return '%s(%s)' % (self.func.__name__, args_string)
        else:
            return ('%s<%s>.%s(%s)' %
                    (self.obj.__class__.__name__,
                     hex(id(self.obj)),
                     self.func.__name__,
                     args_string))

    def process(self):
        if self.obj is None:
            self.func(*self.args, **self.kwargs)
        else:
            self.func(self.obj, *self.args, **self.kwargs)


def actor(func):
    '''Wrap a function as an actor.'''
    @functools.wraps(func)
    def stub(*args, **kwargs):
        cc.statics.message_queue.put(
            Message(obj=None, func=func, args=args, kwargs=kwargs))
    return stub


def interface(method):
    '''Wrap a method as an interface method of an actor.'''
    @functools.wraps(method)
    def stub(self, *args, **kwargs):
        cc.statics.message_queue.put(
            Message(obj=self, func=method, args=args, kwargs=kwargs))
    return stub


def thread_main():
    thread_name = threading.current_thread().name
    logging.info('%s: start', thread_name)
    while True:
        message = cc.statics.message_queue.get()
        logging.trace('%s: %s', thread_name, message)
        try:
            message.process()
        except Exception:
            logging.exception('%s: %s', thread_name, message)
        finally:
            cc.statics.message_queue.task_done()
    logging.error('%s: exit (impossible!)', thread_name)


def join():
    cc.statics.message_queue.join()

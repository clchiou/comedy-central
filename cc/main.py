# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''main().'''

__all__ = ['main']

import argparse
import functools

import cc
import cc.actor
import cc.actor.starter
import cc.inits

from cc import logging


@cc.inits.init(cc.inits.Level.EARLIEST)
def init_argparser():
    parser = argparse.ArgumentParser(description='''
    Download the entire show, all episodes. This program assumes
    that the show website is a Comedy Central website.
    ''')
    cc.statics.parser = parser


@cc.inits.init(cc.inits.Level.EARLY)
def init_args():
    argv = cc.statics.argv
    parser = cc.statics.parser
    cc.statics.args = parser.parse_args(argv[1:])


@cc.inits.init(cc.inits.Level.LATEST)
def init_cleanup():
    del cc.statics.argv
    del cc.statics.parser


def main(argv):
    cc.statics.argv = argv
    cc.inits.run_inits()
    cc.actor.starter.starter()
    cc.actor.join()
    cc.inits.run_finals()
    logging.info('main: exit')
    return 0

# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Download videos through rtmp.'''

__all__ = ['download']

import hashlib
import itertools
import os
import os.path
import psutil
import shutil
import threading
import time

import cc
import cc.inits

from cc import logging


RTMPDUMP_INCOMPLETE = 2


@cc.inits.init(cc.inits.Level.EARLIER)
def init_argparser():
    parser = cc.statics.parser
    parser.add_argument(
        '--rtmp-program', choices=('ffmpeg', 'rtmpdump'), default='rtmpdump',
        help='set rtmp download program (default: %(default)s)')
    parser.add_argument(
        '--rtmp-timeout', default=60*60, type=int,
        help='set rtmp download timeout in seconds (default: %(default)s)')
    parser.add_argument(
        '--rtmp-monitor-period', default=5, type=int,
        help='set rtmp monitor period in seconds (default: %(default)s)')
    parser.add_argument(
        '--rtmp-cpu-bound', default=10, type=int,
        help='set rtmp cpu bound in percent (default: %(default)s)')
    parser.add_argument(
        '--rtmp-memory-bound', default=10, type=int,
        help='set rtmp memory bound in percent (default: %(default)s)')
    parser.add_argument(
        '--rtmp-partial-okay', action='store_true',
        help='treat partial downloads as success')


@cc.inits.init
def init_check_programs():
    parser = cc.statics.parser
    args = cc.statics.args
    if shutil.which(args.rtmp_program) is None:
        parser.error('could not find %s' % args.rtmp_program)


def download(url, file_name, cwd=None):
    args = cc.statics.args
    _download(url, file_name, cwd,
              args.rtmp_program,
              args.rtmp_timeout,
              args.rtmp_monitor_period,
              args.rtmp_cpu_bound,
              args.rtmp_memory_bound,
              args.rtmp_partial_okay)


def _download(url, file_name, cwd,
              prog,
              download_timeout,
              monitor_period,
              cpu_bound,
              memory_bound,
              partial_okay):
    cwd = cwd or os.getcwd()
    file_name_part = file_name + '.part'
    output_path = os.path.join(cwd, file_name)
    output_path_part = os.path.join(cwd, file_name_part)
    digest = None
    for retry_exp in itertools.count():
        timer = threading.Timer(download_timeout, lambda: None)
        timer.daemon = True
        proc = _make_subprocess(url, file_name_part, cwd, prog)
        timer.start()
        ret = -1
        while True:
            try:
                ret = proc.wait(timeout=monitor_period)
                break
            except psutil.TimeoutExpired:
                pass
            cpu_percent = proc.get_cpu_percent(interval=None)
            memory_percent = proc.get_memory_percent()
            logging.trace('rtmp: pid=%d cpu=%.1f memory=%.1f',
                          proc.pid, cpu_percent, memory_percent)
            if cpu_percent > cpu_bound:
                logging.error('rtmp: cpu limit exceeded')
                proc.kill()
                break
            if memory_percent > memory_bound:
                logging.error('rtmp: memory limit exceeded')
                proc.kill()
                break
            if timer.finished.is_set():
                logging.error('rtmp: timeout: %s -> %s', url, output_path_part)
                proc.kill()
                break
        timer.cancel()
        if prog == 'rtmpdump' and ret == RTMPDUMP_INCOMPLETE:
            if partial_okay:
                logging.warning(
                    'rtmp: partial download %s to %s', url, file_name)
                ret = 0
                break
            with open(output_path_part, 'rb') as output_file:
                new_digest = hashlib.sha1(output_file.read()).digest()
            if digest is not None and digest == new_digest:
                # We made no progress; the download might be completed.
                # Let's not retry and assume it was.
                logging.warning(
                    'rtmp: no progress: url=%s file_name=%s', url, file_name)
                ret = 0
                break
            digest = new_digest
            # rtmpdump didn't complete the transfer; resume might get further.
            retry = 2 ** retry_exp
            if retry > download_timeout:
                logging.error('rtmp: retry timeout: %s -> %s',
                              url, output_path_part)
            else:
                logging.trace('rtmp: retry=%d url=%s', retry, url)
                time.sleep(retry)
                continue
        if ret is not None and ret != 0:
            raise cc.Error('Could not download (ret=%s): %s' % (ret, url))
        # Okay, we are done.
        break
    os.rename(output_path_part, output_path)
    logging.info('rtmp: success: %s -> %s', url, output_path)


def _make_subprocess(url, file_name, cwd, prog):
    if prog == 'rtmpdump':
        cmd = ['rtmpdump',
               '--quiet',
               '--rtmp', url,
               '--flv', file_name,
               '--resume',
               '--skip', '1']
    else:
        cmd = ['ffmpeg', '-i', url, file_name]
    logging.debug('exec: CWD=%s %s', cwd, ' '.join(cmd))
    return psutil.Popen(cmd, cwd=cwd)

# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Download documents through http.'''

__all__ = [
    'get_url',
    'get_url_bytes',
    'get_url_dom_tree'
    'get_url_json',
]

import time

import lxml.etree
import requests

from cc import logging


def get_url(url):
    return _get_url_with_retry(url).text


def get_url_bytes(url):
    return _get_url_with_retry(url).content


def get_url_dom_tree(url):
    return lxml.etree.fromstring(get_url_bytes(url))


def get_url_json(url):
    return _get_url_with_retry(url).json()


def _get_url_with_retry(url):
    for retry in (1, 2, 4, 8, 16, 32, 64):
        try:
            return _get_url(url)
        except:
            time.sleep(retry)
    return _get_url(url)


def _get_url(url):
    logging.debug('get_url: url=%s', url)
    response = requests.get(url, timeout=60)
    if logging.is_enabled_for(logging.TRACE):
        for header, value in response.headers.items():
            logging.trace('get_url: %s: %s', header, value)
    response.raise_for_status()
    return response

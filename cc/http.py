# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Download documents through http.'''

__all__ = [
    'get_url',
    'get_url_dom_tree'
    'get_url_json',
]

import lxml.etree
import requests

from cc import logging


def get_url(url):
    return _get_url(url).text


def get_url_dom_tree(url):
    return lxml.etree.fromstring(_get_url(url).content)


def get_url_json(url):
    return _get_url(url).json()


def _get_url(url):
    logging.debug('get_url: url=%s', url)
    response = requests.get(url)
    for header, value in response.headers.items():
        logging.debug('get_url: %s: %s', header, value)
    response.raise_for_status()
    return response

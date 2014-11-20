# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Lazy wrapper of pprint.pfromat().'''

___all__ = ['PrettyFormatter']

import pprint


class PrettyFormatter:

    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return pprint.pformat(self.obj)

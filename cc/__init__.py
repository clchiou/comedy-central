# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Package of accessing Comedy Central website.
The package name 'cc' stands for Comedy Central.
'''

__author__ = 'Che-Liang Chiou'
__version__ = '0.0.1'

__all__ = [
    'Error',
    'Namespace',
    'statics',
]

# NOTE: To prevent circular dependency, this __init__.py should not import
# any other cc.* modules (so that cc.statics is always initialized before any
# other module).


class Error(Exception):
    '''Error of the cc package.'''
    pass


class Namespace:
    '''A write-once namespace.'''

    _NO_ATTR = "'Namespace' object has no attribute '%s'"
    _NO_NONE = "can't set None to attributes: '%s'"
    _OVERWRITE = "can't overwrite attribute '%s'"

    def __init__(self):
        # Bypass Namespace.__setattr__().
        object.__setattr__(self, 'namespace', {})

    def __hasattr__(self, name):
        return name in self.namespace

    def __getattr__(self, name):
        try:
            return self.namespace[name]
        except KeyError:
            raise AttributeError(self._NO_ATTR % name)

    def __setattr__(self, name, value):
        if name in self.namespace:
            raise AttributeError(self._OVERWRITE % name)
        if value is None:
            raise AttributeError(self._NO_NONE % name)
        self.namespace[name] = value

    def __delattr__(self, name):
        try:
            self.namespace.pop(name)
        except KeyError:
            raise AttributeError(self._NO_ATTR % name)


# The 'root' of all global variables.
statics = Namespace()

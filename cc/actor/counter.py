# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Actor Counter.'''

__all__ = ['Counter']

import threading

import cc.actor


class Counter:

    def __init__(self, on_success, on_canceled):
        self._on_success = on_success
        self._on_canceled = on_canceled
        self._lock = threading.RLock()
        self._count = None

    @property
    def count(self):
        with self._lock:
            return self._count

    @count.setter
    def count(self, count):
        with self._lock:
            self._count = count
            if self._count <= 0:
                self._success_with_lock()

    @cc.actor.interface
    def countdown(self):
        with self._lock:
            if self._on_success is None:
                return
            self._count -= 1
            if self._count <= 0:
                self._success_with_lock()

    def _success_with_lock(self):
        self._on_success()
        self._on_success = None
        self._on_canceled = None

    @cc.actor.interface
    def cancel(self):
        with self._lock:
            if self._on_success is None:
                return
            self._on_canceled()
            self._on_success = None
            self._on_canceled = None

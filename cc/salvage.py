# Copyright (C) 2014 Che-Liang Chiou.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Salvage results from failed/partial downloads.'''

__all__ = ['Salvage']

import os
import os.path


class Salvage:

    def __init__(self, dir_name, salvage_dirs):
        self.salvage = {}
        for salvage_dir in salvage_dirs:
            _update_salvage_map(self.salvage, dir_name, salvage_dir)

    def find(self, dir_name, file_name):
        return self.salvage.get(os.path.join(dir_name, file_name))


def _update_salvage_map(salvage_map, dir_name, salvage_dir):
    for tmp_dir_name in os.listdir(salvage_dir):
        # Search '*DIR_NAME*/*' but ignore '*.part' file.
        if dir_name not in tmp_dir_name:
            continue
        tmp_dir_path = os.path.join(salvage_dir, tmp_dir_name)
        for file_name in os.listdir(tmp_dir_path):
            if file_name.endswith('.part'):
                continue
            key = os.path.join(dir_name, file_name)
            salvage_path = os.path.join(tmp_dir_path, file_name)
            salvage_map[key] = salvage_path

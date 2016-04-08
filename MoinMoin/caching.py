"""
    MoinMoin

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: caching.py,v 1.2 2001/02/22 22:18:09 jhermann Exp $
"""
__version__ = "$Revision: 1.2 $"[11:-2]

# Imports
import os

from MoinMoin import config


class CacheEntry:
    def __init__(self, arena, key):
        self.arena = arena
        self.key = key

        # create cache if necessary
        if not os.path.isdir(config.cache_dir):
            os.mkdir(config.cache_dir, 0777)
            os.chmod(config.cache_dir, 0777)

        # create arena if necessary
        arena_dir = os.path.join(config.cache_dir, arena)
        if not os.path.isdir(arena_dir):
            os.mkdir(arena_dir, 0777)
            os.chmod(arena_dir, 0777)

    def _filename(self):
        return os.path.join(config.cache_dir, self.arena, self.key)

    def exists(self):
        return os.path.exists(self._filename())

    def mtime(self):
        try:
            return os.path.getmtime(self._filename())
        except IOError:
            return 0

    def needsUpdate(self, filename):
        if not self.exists(): return 1

        try:
            ctime = os.path.getmtime(self._filename())
            ftime = os.path.getmtime(filename)
        except IOError:
            return 1

        return ftime > ctime

    def copyto(self, filename):
        shutil.copyfile(filename, self._filename())
        os.chmod(self._filename(), 0666)

    def update(self, content):
        open(self._filename(), 'wb').write(content)
        os.chmod(self._filename(), 0666)

    def remove(self):
        try:
            os.remove(self._filename())
        except OSError:
            pass

    def content(self):
        return open(self._filename(), 'rb').read()


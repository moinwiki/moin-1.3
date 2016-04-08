# -*- coding: iso-8859-1 -*-
"""
    MoinMoin

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: caching.py,v 1.5 2003/11/09 21:00:48 thomaswaldmann Exp $
"""
__version__ = "$Revision: 1.5 $"[11:-2]

# Imports
import os, shutil

from MoinMoin import config


class CacheEntry:
    def __init__(self, arena, key):
        self.arena = arena
        self.key = key

        # create cache if necessary
        if not os.path.isdir(config.cache_dir):
            os.mkdir(config.cache_dir, 0777 & config.umask)
            os.chmod(config.cache_dir, 0777 & config.umask)

        # create arena if necessary
        arena_dir = os.path.join(config.cache_dir, arena)
        if not os.path.isdir(arena_dir):
            os.mkdir(arena_dir, 0777 & config.umask)
            os.chmod(arena_dir, 0777 & config.umask)

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

        try:
            os.chmod(self._filename(), 0666 & config.umask)
        except OSError:
            pass

    def update(self, content):
        open(self._filename(), 'wb').write(content)

        try:
            os.chmod(self._filename(), 0666 & config.umask)
        except OSError:
            pass

    def remove(self):
        try:
            os.remove(self._filename())
        except OSError:
            pass

    def content(self):
        return open(self._filename(), 'rb').read()


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - File System Utilities

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: filesys.py,v 1.3 2003/11/09 21:01:15 thomaswaldmann Exp $
"""

import os
from MoinMoin import config


#############################################################################
### Misc Helpers
#############################################################################

def makeDirs(name, mode=0777):
    """ Like os.makedirs(), but with explicit chmod() calls.
        Fixes some practical permission problems on Linux.
    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        makeDirs(head, mode)

    os.mkdir(name, mode & config.umask)
    os.chmod(name, mode & config.umask)


#############################################################################
### File Locking
#############################################################################

# Code from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65203

# portalocker.py - Cross-platform (posix/nt) API for flock-style file locking.
#                  Requires python 1.5.2 or better.

#!!! need to move this docs to the functions, or the class interface
"""Cross-platform (posix/nt) API for flock-style file locking.

Synopsis:

   import portalocker
   file = open("somefile", "r+")
   portalocker.lock(file, portalocker.LOCK_EX)
   file.seek(12)
   file.write("foo")
   file.close()

If you know what you're doing, you may choose to

   portalocker.unlock(file)

before closing the file, but why?

Methods:

   lock( file, flags )
   unlock( file )

Constants:

   LOCK_EX
   LOCK_SH
   LOCK_NB

I learned the win32 technique for locking files from sample code
provided by John Nielsen <nielsenjf@my-deja.com> in the documentation
that accompanies the win32 modules.

Author: Jonathan Feinberg <jdf@pobox.com>
"""

try:
    # give future python versions a chance (they might implement fcntl)
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32con
        import win32file
        import pywintypes

        LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
        LOCK_SH = 0 # the default
        LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY

        # is there any reason not to reuse the following structure?
        __overlapped = pywintypes.OVERLAPPED()
    
        def lock(file, flags):
            hfile = win32file._get_osfhandle(file.fileno())
            win32file.LockFileEx(hfile, flags, 0, 0xffff0000, __overlapped)
    
        def unlock(file):
            hfile = win32file._get_osfhandle(file.fileno())
            win32file.UnlockFileEx(hfile, 0, 0xffff0000, __overlapped)
    else:
        #!!! this will certainly break macs, before your scream, send code ;)
        # macostools.mkalias might help (if it's atomic)
        # similarly os.rename, if it behaves like the win32 one (i.e. 
        # non-POSIX-conformant); if all else fails, we can use simple
        # non-atomic flags files and live with race conditions.
        raise ImportError("Locking only available for nt and posix platforms")
else:
    # implementation using fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB

    def lock(file, flags):
        fcntl.flock(file.fileno(), flags)

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)

#!!! move to unittests
#~ if __name__ == '__main__':
    #~ from time import time, strftime, localtime
    #~ import sys
    #~ import portalocker

    #~ log = open('log.txt', "a+")
    #~ portalocker.lock(log, portalocker.LOCK_EX)

    #~ timestamp = strftime("%m/%d/%Y %H:%M:%S\n", localtime(time()))
    #~ log.write( timestamp )

    #~ print "Wrote lines. Hit enter to release lock."
    #~ dummy = sys.stdin.readline()

    #~ log.close()

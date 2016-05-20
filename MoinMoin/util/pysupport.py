# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Supporting function for Python magic

    @copyright: 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

#############################################################################
### Module import / Plugins
#############################################################################

import sys


def isImportable(module):
    """ Check whether a certain module is available.
    """
    try:
        __import__(module)
        return 1
    except ImportError:
        return 0


def getPackageModules(packagefile):
    """ Return a list of modules for a package, omitting any modules
        starting with an underscore (note that this uses file system
        calls, i.e. it won't work with ZIPped packages and the like).
    """
    import os, re

    pyre = re.compile(r"^([^_].*)\.py$")
    pyfiles = filter(None, map(pyre.match, os.listdir(os.path.dirname(packagefile))))
    modules = map(lambda x: x.group(1), pyfiles)
    modules.sort()
    return modules


def importName(modulename, name):
    """ Import name dynamically from module

    Used to do dynamic import of modules and names that you know their
    names only in runtime.
    
    @param modulename: full qualified mudule name, e.g. x.y.z
    @param name: name to import from modulename
    @rtype: any object
    @return: name from module or None if there is no such name
    """
    try:
        module = __import__(modulename, globals(), {}, [name])
        return getattr(module, name, None)
    except ImportError:
        return None


def makeThreadSafe(function, lock=None):
    """ Call with a function you want to make thread safe

    Call without lock to make the function thread safe using one lock per
    function. Call with existing lock object if you want to make several
    functions use same lock, e.g. all functions that change same data
    structure.

    @param function: function to make thread safe
    @param lock: threading.Lock instance or None
    @rtype: function
    @retrun: function decorated with locking
    """
    if lock is None:
        import threading
        lock = threading.Lock()
    
    def decorated(*args, **kw):
        lock.acquire()
        try:
            return function(*args, **kw)
        finally:
            lock.release()
            
    return decorated

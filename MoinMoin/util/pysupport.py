# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Supporting function for Python magic

    @copyright: 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

#############################################################################
### Module import / Plugins
#############################################################################

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
    """ Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.

        Return None on failure.
    """
    try:
        module = __import__(modulename, globals(), {}, [name]) # {} was: locals()
    except ImportError:
        return None
    return getattr(module, name, None)

# if you look for importPlugin: see wikiutil.importPlugin


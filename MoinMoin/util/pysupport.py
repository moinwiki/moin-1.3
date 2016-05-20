# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Supporting function for Python magic

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
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


def importName(modulename, name, path=None):
    """ Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.

        Return None on failure.
    """
    if path:
        #
        # see Python-src/Demo/imputil/knee.py how import should be done
        #
        import imp, sys

        items = modulename.split('.')
        parent = None
        real_path = [path]
        fqname = None
        for part_name in items:
            # keep full qualified module name up to date
            if fqname is None:
                fqname = part_name
            else:
                fqname = fqname + '.' + part_name
            ## this is the place to check sys.modules if the module
            ## is already available
            ## WARNING: this does not work with farm wikis, cause all
            ## farm plugin paths would map to the same 'plugin' top
            ## module!
            ## We need a dummy module ('wiki_'+sha(path)) to keep them
            ## apart (create with imp.new_module()?)
            # find & import the module
            try:
                fp, pathname, stuff = imp.find_module(part_name, real_path or parent.__path__)
            except ImportError:
                # no need to close fp here, cause its only open if no
                # error occurs
                return None
            try:
                try:
                    mod = imp.load_module(fqname, fp, pathname, stuff)
                except ImportError: # ValueError, if fp is no file, not possible
                    return None
            finally:
                if fp: fp.close()
            # update parent module up to date
            if parent is None:
                # we only need real_path for the first import, after
                # this parent.__path__ is enough
                real_path = None
            else:
                setattr(parent, part_name, mod)
            parent = mod
        return getattr(mod, name, None)
    else:
        # this part is for MoinMoin imports, we use __import__
        # which will also use sys.modules as cache, but thats
        # no harm cause MoinMoin is global anyway.
        try:
            module = __import__(modulename, globals(), {}, [name]) # {} was: locals()
        except ImportError:
            return None
        return getattr(module, name, None)

# if you look for importPlugin: see wikiutil.importPlugin


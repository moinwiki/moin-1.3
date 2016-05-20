# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mod_python wrapper for broken mod_python versions

    @copyright: 2004 by Oliver Graf <ograf@bitart.de>
    @license: GNU GPL, see COPYING for details.
"""
##
## add a .htaccess to the path below which you want to have your
## wiki instance:
##
## <Files wiki>
##   SetHandler python-program
##   PythonPath "['/path/to/moin/share/moin/cgi-bin']+sys.path"
##   PythonHandler moinmodpy
## </Files>
##
## Note: this is a wrapper needed because of a bug in
##       mod_python < 3.1.3
## 
##
## mod_python.apache.resolve_object fails to parse a object with dots.
##
## If you have a newer version, take a look at moinmodpy.htaccess
## to see how to use MoinMoin without this wrapper. You can also
## look into INSTALL.html to see how you can fix the bug on your own
## (a simple one line change).
##


# System path configuration

# The path to MoinMoin package and configuration files. Note that the
# path is the path of the directory where the item lives, not the path
# to the item itself!
# If you did a standard install, and you are not a developer, you
# probably want to skip these settings.

## import sys
## sys.path.insert(0, '/path/to/MoinMoin/dir')
## sys.path.insert(0, '/path/to/wikiconfig/dir')
## sys.path.insert(0, '/path/to/farmconfig/dir')


from MoinMoin.request import RequestModPy

def handler(request):
    moinreq = RequestModPy(request)
    return moinreq.run(request)

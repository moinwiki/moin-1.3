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
##   PythonHandler moin_modpy
## </Files>
##
## Note: this is a wrapper needed because of a bug in
##       mod_python < 3.1.3
## 
##
## mod_python.apache.resolve_object fails to parse a object with dots.
##
## If you have a newer version, take a look at moin_modpy.htaccess
## to see how to use MoinMoin without this wrapper. You can also
## look into INSTALL.html to see how you can fix the bug on your own
## (a simple one line change).
##

#import sys
#sys.path[0:0]=['/path/to/moin/lib/python', '/path/to/moin/config']

from MoinMoin.request import RequestModPy

def handler(request):
    moinreq = RequestModPy(request)
    return moinreq.run(request)

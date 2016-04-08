# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Main CGI Module

   #########################################################################
   # Using cgimain.py is DEPRECATED, please use the new cgi-bin/moin.cgi.  #
   # cgimain.py will be removed very soon.                                 #
   #########################################################################
"""

from MoinMoin.request import RequestCGI

def test():
    from MoinMoin.wikitest import runTest
    request = RequestCGI()    
    runTest(request)

def run(properties={}):
    request = RequestCGI(properties)
    request.run()
    return request


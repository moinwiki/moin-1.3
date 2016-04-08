#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI Driver Script

    Copyright (c) 2000-2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: moin.cgi,v 1.5 2003/11/19 00:31:11 thomaswaldmann Exp $
"""

#import sys
#sys.path.append('/usr/local/home/USERNAME/lib/python')

import os
if os.environ.get('QUERY_STRING') == 'test':
    print "Content-Type: text/plain\n\nMoinMoin CGI Diagnosis\n======================\n"

    try:
        from MoinMoin import cgimain
        print 'Package "MoinMoin" successfully imported.\n'
        cgimain.test()
    except:
        import sys, traceback, string, pprint
        type, value, tb = sys.exc_info()
        if type == ImportError:
            print 'Your PYTHONPATH is:\n%s' % pprint.pformat(sys.path)
        print "\nTraceback (innermost last):\n%s" % string.join(
            traceback.format_tb(tb) + traceback.format_exception_only(type, value))
else:
    from MoinMoin import cgimain
    cgimain.run()


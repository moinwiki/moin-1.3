#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI Driver Script

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

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


from MoinMoin.request import RequestCGI

request = RequestCGI()
request.run()


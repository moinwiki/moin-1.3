#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script puts some content it gets via standard input onto a wiki page
using xmlrpc. We use wiki rpc v2 here.

This script only works if you edited MoinMoin/wikirpc.py (see the comment
in the putPage handler) to not require http auth (trusted user) and to
really use the pagename we give.

This can be done for migrating data into an offline moin wiki running on
localhost - don't put a wiki configured like this on the internet!

GPL software, 2005 Thomas Waldmann
"""

import sys, xmlrpclib
sys.path.insert(0, '../../..')

from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

user = "ThomasWaldmann" # must be a known Wiki account
password = "wrong"
pagename = sys.argv[1] # must be in same encoding as wiki, usually utf-8
pagedata = sys.stdin.read() # must be in wiki encoding, usually utf-8

authtrans = BasicAuthTransport(user, password)
wiki = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de/?action=xmlrpc2", transport=authtrans)

wiki.putPage(pagename, pagedata)


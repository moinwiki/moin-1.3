#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.
    Use this for small, private and local wikis *ONLY*,
    like when using on your local PC or notebook.

    Don't forget to set httpd_host/port/user/docs in
    moin_config.py to fit your needs.

    @copyright: 2004 Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys

# adapt these to fit your needs (maybe you can comment out all
# of these appends if you did a standard installation and put
# moin_config.py in that same directory as moin.py.

# moin_config is here:
sys.path.append('/org/org.linuxwiki.devel/cgi-bin/main')

# stuff used by moin_config (farm config):
sys.path.append('/org/wiki')

# moin code is here:
sys.path.append('/home/twaldmann/moincvs/moin--main')

# start the server:
from MoinMoin import httpdmain
httpdmain.run()


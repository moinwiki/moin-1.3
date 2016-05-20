#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Version Information

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

try:
    from patchlevel import patchlevel
except:
    patchlevel = '1.3.4 release'

project = "MoinMoin"
release  = '1.3.4'
revision = patchlevel

if __name__ == '__main__':
    print project, release, revision


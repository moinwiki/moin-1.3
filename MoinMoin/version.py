# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Version Information

    Copyright (c) 2000-2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.178 2003/11/29 16:37:17 thomaswaldmann Exp $
"""

project = "MoinMoin"
revision = '$Revision: 1.178 $'[11:-2]
release  = '1.1'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')


"""
    MoinMoin - Version Information

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.134 2001/10/27 14:31:33 jhermann Exp $
"""

project = "MoinMoin"
revision = '$Revision: 1.134 $'[11:-2]
release  = '0.10'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')

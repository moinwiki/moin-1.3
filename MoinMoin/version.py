"""
    MoinMoin - Version Information

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.108 2001/01/23 21:44:21 jhermann Exp $
"""

revision = '$Revision: 1.108 $'[11:-2]
release  = '0.8'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')

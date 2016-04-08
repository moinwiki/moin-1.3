"""
    MoinMoin - Version Information

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.128 2001/05/07 22:18:18 jhermann Exp $
"""

revision = '$Revision: 1.128 $'[11:-2]
release  = '0.9'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')

"""
    MoinMoin - Version Information

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.99 2000/12/06 19:16:58 jhermann Exp $
"""

revision = '$Revision: 1.99 $'[11:-2]
release  = '0.7'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')

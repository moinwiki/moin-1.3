"""
    MoinMoin - Version Information

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: version.py,v 1.159 2002/05/10 18:43:16 jhermann Exp $
"""

project = "MoinMoin"
revision = '$Revision: 1.159 $'[11:-2]
release  = '1.0'

if __name__ == "__main__":
    # Bump own revision
    import os
    os.system('cvs ci -f -m "Bumped revision" version.py')


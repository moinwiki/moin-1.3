"""
   Save the setdefaultencoding function from extinction.
   This is only possible from this (automatically loaded) file.
   To be found, it must be in system's pythonpath, e.g. in
   site-packages directory.

   @copyright: 2004 Thomas Waldmann
   @license: GNU GPL, see COPYING for details
"""

import sys
sys.setappdefaultencoding = sys.setdefaultencoding


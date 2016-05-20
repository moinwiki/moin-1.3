#!/usr/bin/env python
""" 
    display unused directories in data/pages
    
    Usage:
    First change the base path to match your needs.
    Then do ./pagescleaner.py >cleanthem.sh
    Then please review cleanthem.sh and run it, if it is OK.
"""

import filecmp

base = "."
left = base + "/data/text"
right = base + "/data/pages"

d = filecmp.dircmp(left,right)
for p in d.right_only:
    print "rm -rf '%s/%s'" % (right,p)
    # use this to generate some cleanup script,
    # which you can use (after review) for cleaning up

# EOF


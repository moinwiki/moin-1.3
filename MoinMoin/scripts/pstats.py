#!/usr/bin/env python
"""
Print statistics gathered by hotshot profiler

Usage:
    pstats statsfile
    
Typical usesage:
 1. Edit moin.py and activate the hotshot profiler, set profile file name
 2. Run moin.py
 3. Do some request, with a browser, script or ab
 4. Stop moin.py
 5. Run this tool: pstats moin.prof
"""

import sys
from hotshot.stats import load

if len(sys.argv) != 2:
    print __doc__
    sys.exit()
    
# Load and print stats 
s = load(sys.argv[1])
s.strip_dirs()
s.sort_stats('time', 'calls')
s.print_stats(20)
s.print_callers(20)

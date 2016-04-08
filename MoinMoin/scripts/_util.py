"""
    MoinMoin - Command line utilities

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    $Id: _util.py,v 1.1 2001/07/04 16:37:54 uid31396 Exp $
"""
__version__ = "$Revision: 1.1 $"[11:-2]

# Imports
import os, sys

# Globals
flag_quiet = 0


#############################################################################
### Logging
#############################################################################

def fatal(msgtext, **kw):
    """ Print error msg to stderr and exit.
    """
    sys.stderr.write("FATAL ERROR: " + msgtext + "\n")
    if kw.get('usage', 0):
        maindict = vars(sys.modules['__main__'])
        if maindict.has_key('usage'):
            maindict['usage']()
    sys.exit(1)


def log(msgtext):
    """ Optionally print error msg to stderr.
    """
    if not flag_quiet:
        sys.stderr.write(msgtext + "\n")


#############################################################################
### Commandline Support
#############################################################################

def cmdInit():
    """ Common command initialization.
    """
    import time

    global _start_time
    _start_time = time.clock()


def runMain(mainloop):
    """ Run the main function of a command.
    """
    showtime = 1
    try:
        try:
            cmdInit()
            mainloop()
        except KeyboardInterrupt:
            log("*** Interrupted by user!")
        except SystemExit:
            showtime = 0
            raise
    finally:
        if showtime: logRuntime()


def logRuntime():
    """ Print the total command run time.
    """
    import time
    log("Needed %.3f secs." % (time.clock() - _start_time,))


def haveOptions(optlist, options):
    """ Check whether one of the options in "options" is in the list of
        options ("optlist") created from the command line
    """
    return filter(lambda flag, o=options: flag[0] in o, optlist) != []


def getOption(optlist, options):
    """ Get the value of the options in "options", from the list of
        options ("optlist") created from the command line
    """
    match = filter(lambda flag, o=options: flag[0] in o, optlist)
    if match:
        return match[-1][1]
    else:
        return ""


def getOptionList(optlist, options):
    """ Get all the values of the options in "options", from the list of
        options ("optlist") created from the command line
    """
    opts = filter(lambda flag, o=options: flag[0] in o, optlist)
    return map(lambda o: o[1], opts)


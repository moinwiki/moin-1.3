"""
    twisted.web based wiki server

    Run this server with mointwisted script on Linux or Mac OS X, or
    mointwisted.cmd on Windows.
    
    @copyright: 2004 Thomas Waldmann, Oliver Graf, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

# System path configuration

# The path to MoinMoin package and configuration files. Note that the
# path is the path of the directory where the item lives, not the path
# to the item itself!
# If you did a standard install, and you are not a developer, you
# probably want to skip these settings.

import sys
# This is needed if you run a daemon with config files in current directory.
sys.path.append('.')
## sys.path.insert(0, '/path/to/MoinMoin/dir')
## sys.path.insert(0, '/path/to/wikiconfig/dir')
## sys.path.insert(0, '/path/to/farmconfig/dir')


from MoinMoin.server.twistedmoin import TwistedConfig, makeApp


class Config(TwistedConfig):

    # Path to moin shared files (default '/usr/share/moin/wiki/htdocs')
    docs = '/usr/share/moin/wiki/htdocs'

    # The server will run with as this user and group (default 'www-data')
    user = 'www-data'
    group = 'www-data'

    # Port (default 8080)
    # To serve privileged port under 1024 you will have to run as root
    port = 8080

    # Interfaces (default [''])
    # The interfaces the server will listen to. 
    # [''] - listen to all interfaces defined on the server
    # ['red.wikicolors.org', 'blue.wikicolors.org'] - listen to some
    # If '' is in the list, other ignored.
    interfaces = ['']

    # How many threads to use (default 10, max 20)
    # The more threads you use, the more memory moin uses. All thread
    # use one CPU, and will not run faster, but might be more responsive
    # on a very busy server.
    threads = 10

    # Set logfile name (default commented)
    # This is the *Apache compatible* log file, not the twisted-style logfile.
    # Leaving this as None will have no Apache compatible log file. Apache
    # compatible logfiles are useful because there are quite a few programs
    # which analyze them and display statistics.
    ## logPath = 'mointwisted.log'

    # Memory profile (default commented)
    # Useful only if you are a developer or interested in moin memory usage
    ## from MoinMoin.util.profile import TwistedProfiler
    ## memoryProfile = TwistedProfiler('mointwisted',
    ##                            requestsPerSample=100,
    ##                            collect=0)
    
    # Hotshot profile (default commented)
    ## hotshotProfile = "mointwisted.prof"


# Create the application
application = makeApp(Config)


#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.
    Use this for small, private and local wikis *ONLY*,
    like when using on your local PC or notebook.

    @copyright: 2004 Thomas Waldmann, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

# System path configuration

# The path to MoinMoin package and configuration files. Note that the
# path is the path of the directory where the item lives, not the path
# to the item itself!
# If you did a standard install, and you are not a developer, you
# probably want to skip these settings.

## import sys
## sys.path.insert(0, '/path/to/MoinMoin/dir')
## sys.path.insert(0, '/path/to/wikiconfig/dir')
## sys.path.insert(0, '/path/to/farmconfig/dir')


from MoinMoin.server.standalone import StandaloneConfig, run


class Config(StandaloneConfig):

    # Path to moin shared files (default '/usr/share/moin/wiki/htdocs')
    docs = '/usr/share/moin/wiki/htdocs'

    # The server will run with as this user and group (default 'www-data')
    user = 'www-data'
    group = 'www-data'

    # Port (default 8000)
    # To serve privileged port under 1024 you will have to run as root
    port = 8000

    # Interface (default 'localhost')
    # The default will listen only to localhost.
    # '' - will listen to any interface
    interface = 'localhost'

    # Log (default commented)
    # Log is written to stderr or to a file you specify here.
    ## logPath = 'moin.log'
    
    # Memory profile (default commented)
    # Useful only if you are a developer or interested in moin memory usage
    # A memory profile named 'moin_standalone--2004-09-27--01-24.log' is
    # created each time you start the server.
    ## from MoinMoin.util.profile import Profiler
    ## memoryProfile = Profiler('moin_standalone',
    ##                          requestsPerSample=100,
    ##                          collect=0)

    # Hotshot profile (default commented)
    ## import hotshot
    ## hotshotProfile = hotshot.Profile("moin.prof")


# Run moin moin server:
run(Config)


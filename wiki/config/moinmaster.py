# -*- coding: utf-8 -*-
# This is a sample config for a wiki that is part of a wiki farm and uses
# farmconfig for common stuff. Here we define what has to be different from
# the farm's common settings.

# we import the FarmConfig class for common defaults of our wikis:

from farmconfig import FarmConfig

# now we subclass that config (inherit from it) and change what's different:

class Config(FarmConfig):

    show_timings = 1

    # basic options (you normally need to change these)
    sitename = 'MoinMaster'
    interwikiname = 'MoinMaster'
    data_dir = '/org/de.wikiwikiweb.moinmaster/data/'

    navi_bar = ['FrontPage', 'RecentChanges', 'FindPage', 'HelpContents', 'UserPage', ]



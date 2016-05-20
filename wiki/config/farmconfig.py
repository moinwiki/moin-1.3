# -*- coding: utf-8 -*-
"""
    MoinMoin - Configuration for a wiki farm

    If you run a single wiki only, you can omit this file file and just
    use wikiconfig.py - it will be used for every request we get in that
    case.

    Note that there are more config options than you'll find in
    the version of this file that is installed by default; see
    the module MoinMoin.multiconfig for a full list of names and their
    default values.

    Also, the URL http://moinmoin.wikiwikiweb.de/HelpOnConfiguration has
    a list of config options.

    @copyright: 2000-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""


# Wikis in your farm --------------------------------------------------

# If you run multiple wikis, you need this list of pairs (wikiname, url
# regular expression). moin processes that list and tries to match the
# regular expression against the URL of this request - until it matches.
# Then it loads the <wikiname>.py config for handling that request.

wikis = [
    # wikiname,     url regular expression
    ("moinmaster",  r"^moinmaster.wikiwikiweb.de/.*$"),
    ("moinmoin",    r"^moinmoin.wikiwikiweb.de/.*$"),
]


# Common configuration for all wikis ----------------------------------

# Everything that should be configured the same way should go here,
# anything else that should be different should go to the single wiki's
# config.
# In that single wiki's config, we will use the class FarmConfig we define
# below as the base config settings and only override what's different.
#
# In exactly the same way, we first include MoinMoin's Config Defaults here -
# this is to get everything to sane defaults, so we need to change only what
# we like to have different:

from MoinMoin.multiconfig import DefaultConfig

# Now we subclass this DefaultConfig. This means that we inherit every setting
# from the DefaultConfig, except those we explicitely define different.

class FarmConfig(DefaultConfig):

    url_prefix = '/wiki'

    # as it isnt modified, it can be share between all instances:
    data_underlay_dir = '/whereever/underlay'

    # options people are likely to change due to personal taste
    show_hosts = 1                          # show hostnames?
    nonexist_qm = 0                         # show '?' for nonexistent?
    backtick_meta = 1                       # allow `inline typewriter`?
    allow_extended_names = 1                # allow ["..."] markup?
    edit_rows = 20                          # editor size
    max_macro_size = 50                     # max size of RecentChanges in KB (0=unlimited)
    bang_meta = 1                           # use ! to escape WikiNames?
    show_section_numbers = 0                # enumerate headlines?

    # Charting needs "gdchart" installed! (None to disable charting)
    chart_options = {'width': 600, 'height': 300}

    # security critical actions (deactivated by default)
    #allowed_actions = ['DeletePage', 'AttachFile', 'RenamePage',]

    # mail functions. use empty mail_smarthost to disable.
    mail_smarthost = 'localhost'
    mail_from = 'wiki@wikiwikiweb.de'

    acl_enabled = 1
    acl_rights_before = "ThomasWaldmann:admin,read,write,revert,delete"

    page_group_regex = "[a-z]Group$"

    #caching_formats = []

    # Link spam protection for public wikis (uncomment to enable).
    # Needs a reliable internet connection.
    #from MoinMoin.util.antispam import SecurityPolicy


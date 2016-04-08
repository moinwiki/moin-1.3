# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Configuration

    Note that there are more config options than you'll find in
    the version of this file that is installed by default; see
    the module MoinMoin.config for a full list of names and their
    default values.

    Also, the URL http://purl.net/wiki/moin/HelpOnConfiguration has
    a list of config options.

    @copyright: 2000-2003 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""
# If you run several wikis on one host (commonly called a wiki farm),
# uncommenting the following allows you to load global settings for
# all your wikis. You will then have to create "farm_config.py" in
# the MoinMoin package directory.
#
# from MoinMoin.farm_config import *

# use this for protecting your wiki against link spam:
from MoinMoin.util.antispam import SecurityPolicy

# basic options (you normally need to change these)
sitename = 'An Unnamed MoinMoin Wiki'
interwikiname = None
data_dir = './data/'
url_prefix = '/wiki'
logo_url = url_prefix + '/classic/img/moinmoin.png'

# encoding and WikiName char sets
# (change only for outside America or Western Europe)
charset = 'iso-8859-1'
upperletters = "A-ZÀÁÂÃÄÅÆÈÉÊËÌÍÎÏÒÓÔÕÖØÙÚÛÜÝÇÐÑÞ"
lowerletters = "0-9a-zàáâãäåæèéêëìíîïòóôõöøùúûüýÿµßçðñþ"

# options people are likely to change due to personal taste
show_hosts = 1                          # show hostnames?
nonexist_qm = 0                         # show '?' for nonexistent?
backtick_meta = 1                       # allow `inline typewriter`?
allow_extended_names = 1                # allow ["..."] markup?
edit_rows = 20                          # editor size
max_macro_size = 50                     # max size of RecentChanges in KB (0=unlimited)
bang_meta = 1                           # use ! to escape WikiNames?
show_section_numbers = 0                # enumerate headlines?

# charting needs "gdchart" installed!
# you can remove the test and gain a little speed (i.e. keep only
# the chart_options assignment, or remove this code section altogether)
try:
    import gdchart
    chart_options = {'width': 720, 'height': 400}
except ImportError:
    pass

# values that depend on above configuration settings
logo_string = '<img src="%s" alt="%s">' % (logo_url, sitename)

# security critical actions (deactivated by default)
# allowed_actions = ['DeletePage', 'AttachFile']

# for standalone server (see cgi-bin/moin.py)
httpd_host = "localhost"
httpd_port = 80
httpd_user = "nobody"
httpd_docs = "/usr/share/moin/wiki/htdocs/"


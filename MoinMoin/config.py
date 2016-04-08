"""
    MoinMoin - Configuration

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: config.py,v 1.13 2001/04/19 22:49:38 jhermann Exp $
"""

# Imports
import os
from moin_config import *

# defaults for older config files
_cfg_defaults = {
    'allow_extended_names': 0,
    'max_macro_size': 0,

    'allowed_actions': [],
    'url_schemas': [],

    'page_edit_tips': 'HelpOnFormatting',
    'page_user_prefs':  'UserPreferences',

    'check_i18n': 0,
    'charset': 'iso-8859-1',
    'html_head': '',
    'html_head_queries': '',
    'page_footer1': """<a href="http://www.python.org/"><img align="right" vspace="10"
src="%s/PythonPowered.gif" width="55" height="22" border="0"
alt="PythonPowered"></a>""" % (url_prefix,),
    'page_footer2': '',
}

for key, val in _cfg_defaults.items():
    if not vars().has_key(key):
        vars()[key] = val

# create list of excluded actions by first listing all "dangerous"
# actions, and then selectively remove those the user allows
excluded_actions = ['DeletePage']
for _action in allowed_actions:
    try:
        excluded_actions.remove(_action)
    except ValueError:
        pass

# define directories
data_dir = os.path.normpath(data_dir)
text_dir = os.path.join(data_dir, 'text')
user_dir = os.path.join(data_dir, 'user')
cache_dir = os.path.join(data_dir, 'cache')
backup_dir = os.path.join(data_dir, 'backup')
editlog_name = os.path.join(data_dir, 'editlog')

moinmoin_dir = os.path.abspath(os.path.dirname(__file__))

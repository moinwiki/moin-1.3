"""
    MoinMoin - Configuration

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: config.py,v 1.5 2000/11/25 17:39:33 jhermann Exp $
"""

# Imports
import os
from moin_config import *

# defaults for older config files
if not vars().has_key("allow_extended_names"):
    allow_extended_names=0 
if not vars().has_key("html_head"):
    html_head='' 
if not vars().has_key("max_macro_size"):
    max_macro_size=0 
if not vars().has_key("page_edit_tips"):
    page_edit_tips='HelpOnFormatting'
if not vars().has_key("page_user_prefs"):
    page_user_prefs = 'UserPreferences'

if not vars().has_key("page_footer1"):
    page_footer1="""<a href="http://www.python.org/"><img align="right" vspace="10"
src="%s/PythonPowered.gif" width="55" height="22" border="0"
alt="PythonPowered"></a>""" % (url_prefix,)

if not vars().has_key("page_footer2"):
    page_footer2=''

# define directories
data_dir = os.path.normpath(data_dir)
text_dir = os.path.join(data_dir, 'text')
user_dir = os.path.join(data_dir, 'user')
backup_dir = os.path.join(data_dir, 'backup')
editlog_name = os.path.join(data_dir, 'editlog')


"""
    MoinMoin - Configuration

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Load moin_config.py and add any missing values with their defaults.

    $Id: config.py,v 1.62 2002/03/09 15:55:22 jhermann Exp $
"""

# Try to import moin_config. If it fails, either someone forgot moin_config,
# or someone who doesn't know moin_config might be required, tried to import
# us or something (Page, for example) which imports us. One example of such
# a non-Moin-aware importer is pydoc, as shipped with Python 2.1. Continuing
# with reasonable defaults is a friendly way of letting people browse the
# MoinMoin class library with pydoc, and is also friendly to people who for
# some reason forgot they need moin_config. 
default_config = 0
try:
    from moin_config import *
except ImportError, e:
    default_config = 1
    msg = 'import of moin_config failed due to "%s";' \
          ' default configuration used instead.' % e
    try:
        import warnings # new in Python 2.1
        warnings.warn(msg)
        del warnings
    except ImportError:
        import sys
        sys.stderr.write(msg + '\n')
        del sys
    del msg

if not vars().has_key('url_prefix'):
    url_prefix = '.'

# default config values
cfg_defaults = {
    'allow_extended_names': 1,
    'allow_subpages': 1,
    'allow_numeric_entities': 1,
    'allowed_actions': [],
    'attachments': None, # {'dir': path, 'url': url-prefix}
    'bang_meta': 0,
    'backtick_meta': 1,
    'changed_time_fmt': '&nbsp;[%H:%M]',
    'charset': 'iso-8859-1',
    # if you have gdchart, add something like
    # chart_options = {'width': 720, 'height': 540}
    'chart_options': None,
    'check_i18n': 0,
    'css_url': '%s/css/moinmoin.css' % (url_prefix,),
    'data_dir': './data/',
    'date_fmt': '%Y-%m-%d',
    'datetime_fmt': '%Y-%m-%d %H:%M:%S',
    'default_markup': 'wiki',
    'edit_rows': 30,
    'external_diff': 'diff',
    'html_head': '''
<META HTTP-EQUIV="Content-Type" CONTENT="text/html;charset=iso-8859-1">
<META NAME="MSSmartTagsPreventParsing" CONTENT="true">''',
    'html_head_queries': '''
<META NAME="ROBOTS" CONTENT="NOINDEX,NOFOLLOW">''',
    'httpd_host': 'localhost',
    'httpd_port': 8080,
    'httpd_user': 'nobody',
    'httpd_docs': './wiki-moinmoin',
    'interwikiname': None,
    'logo_string': '<img src="/wiki-moinmoin/moinmoin.gif" border=0 alt="MoinMoin">',
    'lowerletters': '0-9a-z\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf2\xf3\xf4\xf5\xf6\xf8\xf9\xfa\xfb\xfc\xfd\xff\xb5\xdf\xe7\xf0\xf1\xfe',
    'mail_smarthost': None,
    'mail_from': None,
    'max_macro_size': 50,
    'navi_bar': [
        'FrontPage',
        'RecentChanges',
        'TitleIndex',
        'WordIndex',
        'SiteNavigation',
        'HelpContents',
    ],
    'nonexist_qm': 0,

    # page names
    'page_front_page': 'FrontPage',
    'page_template_ending': 'Template',
    'page_form_ending': 'Form',
    'page_local_spelling_words': 'LocalSpellingWords',

    'page_footer1': """<hr><a href="http://www.python.org/"><img align="right" vspace="10"
src="%s/img/PythonPowered.gif" width="55" height="22" border="0"
alt="PythonPowered"></a>""" % (url_prefix,),
    'page_footer2': '',
    'page_icons': '''
<a href="%(scriptname)s/%(page_help_contents)s"><img src="%(url)s/img/moin-help.gif" width="12" height="11" border="0" hspace="2" align="right" alt="%(page_help_contents)s"></a>
<a href="%(scriptname)s/%(page_find_page)s?value=%(pagename)s"><img src="%(url)s/img/moin-search.gif" width="12" height="12" border="0" hspace="2" align="right" alt="Search"></a>
<a href="%(scriptname)s/%(pagename)s?action=diff"><img src="%(url)s/img/moin-diff.gif" width="15" height="11" border="0" hspace="2" align="right" alt="Diffs"></a>
<a href="%(scriptname)s/%(pagename)s?action=info"><img src="%(url)s/img/moin-info.gif" width="12" height="11" border="0" hspace="2" align="right" alt="Info"></a>
<a href="%(scriptname)s/%(pagename)s?action=edit"><img src="%(url)s/img/moin-edit.gif" width="12" height="12" border="0" hspace="2" align="right" alt="Edit"></a>
<a href="%(scriptname)s/%(pagename)s?action=subscribe"><img src="%(url)s/img/moin-email.gif" width="14" height="10" border="0" hspace="2" vspace="1" align="right" alt="Subscribe"></a>
<a href="%(scriptname)s/%(pagename)s?action=format&mimetype=text/xml"><img src="%(url)s/img/moin-xml.gif" width="20" height="13" border="0" hspace="2" align="right" alt="XML"></a>
<a href="%(scriptname)s/%(pagename)s?action=print"><img src="%(url)s/img/moin-print.gif" width="12" height="13" border="0" hspace="2" align="right" alt="Print"></a>
<a href="%(scriptname)s/%(pagename)s"><img src="%(url)s/img/moin-show.gif" width="12" height="13" border="0" hspace="2" align="right" alt="View"></a>
''',
    'page_icons_home': '<img src="%(url)s/img/moin-home.gif" width="13" height="12" border="0" hspace="2" align="right" alt="Home">',
    'page_icons_up': '<img src="%(url)s/img/moin-parent.gif" width="15" height="13" border="0" hspace="2" align="right" alt="Up">',
    'shared_intermap': None,
    'shared_metadb': None,
    'show_hosts': 1,
    'show_section_numbers': 1,
    'show_timings': 0,
    'show_version': 0,
    'sitename': 'An Unnamed MoinMoin Wiki',
    'title1': None,
    'title2': '<hr>',
    'trail_size': 5,
    'ua_spiders': 'htdig', # a regex of HTTP_USER_AGENTS that should be excluded from logging
    'umask': 0777,
    'upperletters': 'A-Z\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd2\xd3\xd4\xd5\xd6\xd8\xd9\xda\xdb\xdc\xdd\xc7\xd0\xd1\xde',
    'url_prefix': '/wiki-moinmoin',
    'url_schemas': [],
    'url_mappings': {},
    'LogStore': 'text:editlog',
    'SecurityPolicy': None,
}


# Iterate through defaults, setting any absent variables
for key, val in cfg_defaults.items():
    if not vars().has_key(key):
        vars()[key] = val

del cfg_defaults
del key
del val

### def _smartrepr(str):
###     """Create multi-line string repr if necessary"""
###     rep = repr(str)
###     if rep.count(r'\n'):
###         rep = rep[0] * 2 + rep.replace(r'\n', '\n') + rep[0] * 2
###     return rep
### 
### _l = vars().items()
### _l.sort()
### for key, val in _l:
###     if key[0] == '_': continue
###     print "    " + `key`+':', _smartrepr(val) + ','

# create list of excluded actions by first listing all "dangerous"
# actions, and then selectively remove those the user allows
excluded_actions = ['DeletePage', 'AttachFile']
for _action in allowed_actions:
    try:
        excluded_actions.remove(_action)
    except ValueError:
        pass

# define directories
import os
data_dir = os.path.normpath(data_dir)
moinmoin_dir = os.path.abspath(os.path.dirname(__file__))

for _dirname in ('text', 'user', 'cache', 'backup', 'plugin'):
    _varname = _dirname + '_dir'
    if not vars().has_key(_varname):
        vars()[_varname] = os.path.join(data_dir, _dirname)

del os, _dirname, _varname


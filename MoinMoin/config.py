# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Configuration

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Load moin_config.py and add any missing values with their defaults.

    $Id: config.py,v 1.97 2003/11/09 21:00:49 thomaswaldmann Exp $
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
_cfg_defaults = {
    'acl_enabled': 0,
    'acl_rights_default': "Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write",
    'acl_rights_before': "",
    'acl_rights_after': "",
    'acl_rights_valid': ['read', 'write', 'delete', 'revert', 'admin'],
    'allow_extended_names': 1,
    'allow_subpages': 1,
    'allow_numeric_entities': 1,
    'allowed_actions': [],
    'allow_xslt': 0,
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
    'default_lang': 'en',
    'default_markup': 'wiki',
    'edit_locking': 'warn 10', # None, 'warn <timeout mins>', 'lock <timeout mins>'
    'edit_rows': 30,
    'external_diff': 'diff',
    'hosts_deny': [],
    'html_head': '''
<META HTTP-EQUIV="Content-Type" CONTENT="text/html;charset=iso-8859-1">
<META NAME="MSSmartTagsPreventParsing" CONTENT="true">''',
    'html_head_queries': '''
<META NAME="ROBOTS" CONTENT="NOINDEX,NOFOLLOW">''',
    'html_pagetitle': None,
    'httpd_host': 'localhost',
    'httpd_port': 8080,
    'httpd_user': 'nobody',
    'httpd_docs': './wiki-moinmoin',
    'interwikiname': None,
    'logo_string': '<img src="/wiki-moinmoin/moinmoin.gif" border=0 alt="MoinMoin">',
    'lowerletters': '0-9a-z\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf2\xf3\xf4\xf5\xf6\xf8\xf9\xfa\xfb\xfc\xfd\xff\xb5\xdf\xe7\xf0\xf1\xfe',
    'mail_login': None, # or "user pwd" if you need to use SMTP AUTH
    'mail_smarthost': None,
    'mail_from': None,
    'max_macro_size': 50,
    'navi_bar': [
        'FrontPage',
        'RecentChanges',
        'TitleIndex',
        'WordIndex',
        'SiteNavigation',
        '^HelpContents',
        '[^http://moin.sf.net/ moin.sf.net]',
    ],
    'nonexist_qm': 0,

    # page names
    'page_front_page': 'FrontPage',
    'page_template_regex': '[a-z]Template$',
    'page_form_regex': '[a-z]Form$',
    'page_category_regex': '^Category[A-Z]',
    'page_local_spelling_words': 'LocalSpellingWords',
    'page_group_regex': ".*Group$",

    'page_license_enabled': 0,
    'page_license_page': 'WikiLicense',
    'page_license_text': """<br>
<em>By hitting <strong>%(save_button_text)s</strong> you put your changes under the %(license_link)s.
If you don't want that, hit <strong>%(cancel_button_text)s</strong> to cancel your changes.</em>
""",
    'page_footer1': """<br><br>
<a href="http://www.python.org/"><img align="right" vspace="10" hspace="3"
src="%s/img/PythonPowered.gif" width="55" height="22" border="0"
alt="PythonPowered"></a>""" % (url_prefix,),
    'page_footer2': '',
    'page_icons': '''
<a href="%(scriptname)s/%(page_help_contents)s" target="_blank" title="%(page_help_contents)s"><img src="%(url)s/img/moin-help.gif" alt="%(page_help_contents)s" width="12" height="11" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(page_find_page)s?value=%(pagename)s" title="%(page_find_page)s"><img src="%(url)s/img/moin-search.gif" alt="%(page_find_page)s" width="12" height="12" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=diff" title="Diffs"><img src="%(url)s/img/moin-diff.gif" alt="Diffs" width="15" height="11" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=info" title="Info"><img src="%(url)s/img/moin-info.gif" alt="Info" width="12" height="11" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=edit" title="Edit"><img src="%(url)s/img/moin-edit.gif" alt="Edit" width="12" height="12" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=subscribe" title="Subscribe"><img src="%(url)s/img/moin-email.gif" alt="Subscribe" width="14" height="10" border="0" hspace="2" vspace="1" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=format&mimetype=text/xml" title="XML"><img src="%(url)s/img/moin-xml.gif" alt="XML" width="20" height="13" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s?action=print" title="Print"><img src="%(url)s/img/moin-print.gif" alt="Print" width="16" height="14" border="0" hspace="2" align="right"></a>
<a href="%(scriptname)s/%(pagename)s" title="View"><img src="%(url)s/img/moin-show.gif" alt="View" width="12" height="13" border="0" hspace="2" align="right"></a>
''',
    'page_icons_home': '<img src="%(url)s/img/moin-home.gif" alt="Home" width="13" height="12" border="0" hspace="2" align="right">',
    'page_icons_up': '<img src="%(url)s/img/moin-parent.gif" alt="Up" width="15" height="13" border="0" hspace="2" align="right">',
    'shared_intermap': None, # can be string or list of strings (filenames)
    'shared_metadb': None,
    'show_hosts': 1,
    'show_section_numbers': 1,
    'show_timings': 0,
    'show_version': 0,
    'sitename': 'An Unnamed MoinMoin Wiki',
    'smileys': {},
    'title1': None,
    'title2': '<hr>',
    'trail_size': 5,
    # a regex of HTTP_USER_AGENTS that should be excluded from logging,
    # and receive a FORBIDDEN for anything except viewing a page
    'ua_spiders': 'archiver|crawler|google|htdig|httrack|jeeves|larbin|leech|linkbot' +
                  '|linkmap|linkwalk|mercator|mirror|robot|scooter|search|sitecheck|spider|wget',
    'umask': 0777,
    'upperletters': 'A-Z\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd2\xd3\xd4\xd5\xd6\xd8\xd9\xda\xdb\xdc\xdd\xc7\xd0\xd1\xde',
    'url_prefix': '/wiki',
    'url_schemas': [],
    'url_mappings': {},
    'LogStore': 'text:editlog',
    'SecurityPolicy': None,
}

smiley_defaults = {
    "X-(":  (15, 15, 0, "angry.gif"),
    ":D":   (15, 15, 0, "biggrin.gif"),
    "<:(":  (15, 15, 0, "frown.gif"),
    ":o":   (15, 15, 0, "redface.gif"),
    ":(":   (15, 15, 0, "sad.gif"),
    ":)":   (15, 15, 0, "smile.gif"),
    "B)":   (15, 15, 0, "smile2.gif"),
    ":))":  (15, 15, 0, "smile3.gif"),
    ";)":   (15, 15, 0, "smile4.gif"),
    "/!\\": (15, 15, 0, "alert.gif"),
    "<!>":  (15, 15, 0, "attention.gif"),
    "(!)":  (15, 15, 0, "idea.gif"),

    # copied 2001-11-16 from http://pikie.darktech.org/cgi/pikie.py?EmotIcon
    ":-?":  (15, 15, 0, "tongue.gif"),
    ":\\":  (15, 15, 0, "ohwell.gif"),
    ">:>":  (15, 15, 0, "devil.gif"),
    "%)":   (15, 15, 0, "eyes.gif"),
    "@)":   (15, 15, 0, "eek.gif"),
    "|)":   (15, 15, 0, "tired.gif"),
    ";))":  (15, 15, 0, "lol.gif"),
    
    # some folks use noses in their emoticons
    ":-(":  (15, 15, 0, "sad.gif"),
    ":-)":  (15, 15, 0, "smile.gif"),
    "B-)":  (15, 15, 0, "smile2.gif"),
    ":-))": (15, 15, 0, "smile3.gif"),
    ";-)":  (15, 15, 0, "smile4.gif"),
    "%-)":  (15, 15, 0, "eyes.gif"),
    "@-)":  (15, 15, 0, "eek.gif"),
    "|-)":  (15, 15, 0, "tired.gif"),
    ";-))": (15, 15, 0, "lol.gif"),
    
    # version 1.0
    "(./)":  (20, 15, 0, "checkmark.gif"),
    "{OK}":  (14, 12, 0, "thumbs-up.gif"),
    "{X}":   (16, 16, 0, "icon-error.gif"),
    "{i}":   (16, 16, 0, "icon-info.gif"),
    "{1}":   (15, 13, 0, "prio1.gif"),
    "{2}":   (15, 13, 0, "prio2.gif"),
    "{3}":   (15, 13, 0, "prio3.gif"),

    # version 1.1 (flags)
    # flags for the languages in MoinMoin.i18n
    "{da}":  (18, 12, 1, "flag-da.gif"),
    "{de}":  (18, 12, 1, "flag-de.gif"),
    "{en}":  (24, 12, 0, "flag-en.gif"),
    "{es}":  (18, 12, 0, "flag-es.gif"),
    "{fi}":  (18, 12, 1, "flag-fi.gif"),
    "{fr}":  (18, 12, 1, "flag-fr.gif"),
    "{it}":  (18, 12, 1, "flag-it.gif"),
    "{ja}":  (18, 12, 1, "flag-ja.gif"),
    "{ko}":  (18, 12, 1, "flag-ko.gif"),
    "{nl}":  (18, 12, 1, "flag-nl.gif"),
    "{pt}":  (18, 12, 0, "flag-pt.gif"),
    "{sv}":  (18, 12, 0, "flag-sv.gif"),
    "{us}":  (20, 12, 0, "flag-us.gif"),
    "{zh}":  (18, 12, 0, "flag-zh.gif"),
}

# Iterate through defaults, setting any absent variables
for key, val in _cfg_defaults.items():
    if not vars().has_key(key):
        vars()[key] = val

# Mix in std smileys
smileys.update(smiley_defaults)

del smiley_defaults
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


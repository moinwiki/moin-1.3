"""
    MoinMoin - Configuration

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: moin_config.py,v 1.19 2000/11/25 17:39:34 jhermann Exp $
"""
__version__ = "$Revision: 1.19 $"[11:-2]

# basic options
data_dir = './data/'
url_prefix = '/wiki-moinmoin'

import socket
if socket.gethostname() == "triple.des.encrypted.net":
    url_prefix = '/~jh/moinmoin'

logo_string = '<img src="%s/moinmoin.gif" border=0 alt="MoinMoin">' % (url_prefix,)
changed_time_fmt = '&nbsp; [%H:%M]'
date_fmt = '%Y-%m-%d'
datetime_fmt = '%Y-%m-%d %H:%M:%S'
show_hosts = 1                          # show hostnames?
css_url = '%s/default.css' % (url_prefix,) # stylesheet link, or ''
nonexist_qm = 0                         # show '?' for nonexistent?
edit_rows = 30
show_timings=0
show_version=0
allow_extended_names=1
max_macro_size=50 # max size of RecentChanges in KB (0=unlimited)
html_head="""
<META HTTP-EQUIV="Content-Type" CONTENT="text/html;charset=iso-8859-1">
<META NAME="ROBOTS" CONTENT="NOINDEX,NOFOLLOW">
"""

# page names
front_page      = 'FrontPage'
recent_changes  = 'RecentChanges'
page_edit_tips  = 'HelpOnFormatting'
page_user_prefs = 'UserPreferences'

# char sets (WikiNames)
upperletters = "A-ZÀÁÂÃÄÅÆÈÉÊËÌÍÎÏÒÓÔÕÖØÙÚÛÜÝÇÐÑÞ"
lowerletters = "0-9a-zàáâãäåæèéêëìíîïòóôõöøùúûüýÿµßçðñþ"

# navigation bar (should be generated in the script, from a dictionary or list)
navi_bar="""
<table cellpadding=0 cellspacing=3 border=0 style="background-color:#C8C8C8;text-decoration:none">
  <tr>

    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<b>MoinMoin Wiki</b>&nbsp;
      </font>
    </td>
    
    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/FrontPage">FrontPage</a>&nbsp;
      </font>
    </td>
    
    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/RecentChanges">RecentChanges</a>&nbsp;
      </font>
    </td>

    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/TitleIndex">TitleIndex</a>&nbsp;
      </font>
    </td>

    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/WordIndex">WordIndex</a>&nbsp;
      </font>
    </td>
    
    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/HelpContents">Help</a>&nbsp;
      </font>
    </td>

  </tr>
</table>
"""

page_icons = """
<a href="%(scriptname)s/HelpContents"><img src="%(url)s/img/moin-help.gif" width="12" height="11" border="0" hspace="2" align="right" alt="Help"></a>
<a href="%(scriptname)s/FindPage?value=%(pagename)s"><img src="%(url)s/img/moin-search.gif" width="12" height="12" border="0" hspace="2" align="right" alt="Search"></a>
<a href="%(scriptname)s/%(pagename)s?action=diff"><img src="%(url)s/img/moin-diff.gif" width="15" height="11" border="0" hspace="2" align="right" alt="Diffs"></a>
<a href="%(scriptname)s/%(pagename)s?action=info"><img src="%(url)s/img/moin-info.gif" width="12" height="11" border="0" hspace="2" align="right" alt="Info"></a>
<a href="%(scriptname)s/%(pagename)s?action=edit"><img src="%(url)s/img/moin-edit.gif" width="12" height="12" border="0" hspace="2" align="right" alt="Edit"></a>
<a href="%(scriptname)s/%(pagename)s?action=print"><img src="%(url)s/img/moin-print.gif" width="12" height="13" border="0" hspace="2" align="right" alt="Print"></a>
<a href="%(scriptname)s/%(pagename)s"><img src="%(url)s/img/moin-show.gif" width="12" height="13" border="0" hspace="2" align="right" alt="View"></a>
"""

page_footer1="""<a href="http://www.python.org/"><img align="right" vspace="10"
src="%s/PythonPowered.gif" width="55" height="22" border="0"
alt="PythonPowered"></a>""" % (url_prefix,)

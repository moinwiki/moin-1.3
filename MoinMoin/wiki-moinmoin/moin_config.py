"""
    MoinMoin - Configuration

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: moin_config.py,v 1.6 2000/07/28 22:25:35 jhermann Exp $
"""
__version__ = "$Revision: 1.6 $"[11:-2]

# basic options
data_dir = './data/'
url_prefix = '/wiki-moinmoin'

import socket
if socket.gethostname() == "triple":
    data_dir = '/home/jh/public_html/moinmoin/data/'
    url_prefix = '/~jh/moinmoin'

logo_string = '<img src="%s/moinmoin.gif" border=0 alt="MoinMoin">' % (url_prefix,)
changed_time_fmt = '&nbsp; [%H:%M]'
date_fmt = '%Y-%m-%d'
datetime_fmt = '%Y-%m-%d %H:%M:%S'
show_hosts = 1                          # show hostnames?
css_url = '%s/default.css' % (url_prefix,) # stylesheet link, or ''
nonexist_qm = 0                         # show '?' for nonexistent?
edit_rows = 30

# page names
front_page      = 'FrontPage'
recent_changes  = 'RecentChanges'

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
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/TipsForBeginners">TipsForBeginners</a>&nbsp;
      </font>
    </td>

    <td valign=top align=center bgcolor="#E8E8E8">
      <font face="Arial,Helvetica" size="-1">
        &nbsp;<a style="text-decoration:none" href="%(scriptname)s/EditingTips">EditingTips</a>&nbsp;
      </font>
    </td>

  </tr>
</table>
"""


"""
    MoinMoin - NewWindow Macro

    Copyright (c) 2000-2001 by Changjune Kim <juneaftn@orgio.net>
    All rights reserved, see COPYING for details.

    [[NewWindow("url"[, "linkname"])]]
        Pops up a new window when clicked on

    $Id: NewWindow.py,v 1.1 2001/11/27 20:14:35 jhermann Exp $
"""

# Imports
import cgi, re
from MoinMoin import config

_args_re_pattern = r'(?P<hq1>[\'"])(?P<url>[^\'"]+)((?P<spacer>[\'"],\s*)(?P<hquote>[\'"])(?P<htext>.+?)(?P=hquote))?'

def execute(macro, text, args_re=re.compile(_args_re_pattern)):
    if not text:
        return ('<p><strong class="error">URL Needed!</strong></p>')

    # parse and check arguments
    args = args_re.match(text)
    if not args:
        return '<p><strong class="error">Invalid NewWindow arguments "%s"!</strong></p>' % (text,)

    url = args.group('url')
    htext= args.group('htext')
    if not htext:
        htext=url
    result='<a href="%s" target="_blank">'%cgi.escape(url,1)
    result+='<img src="%s/img/moin-www.gif" width="11" height="11" border="0" hspace="4" alt="[new window]">%s</a>'\
           %(config.url_prefix, htext)
    return result


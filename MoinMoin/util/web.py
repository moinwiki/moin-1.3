# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Helper functions for WWW stuff

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: web.py,v 1.11 2003/11/09 21:01:15 thomaswaldmann Exp $
"""

import cgi
from MoinMoin import config, webapi

_ua_match = None

def isSpiderAgent(ua=None):
    """ Return True if user agent appears to be a spider.
    """
    if not config.ua_spiders:
        return 0

    if ua is None:
        ua = webapi.getUserAgent()

    global _ua_match
    if _ua_match is None:
        import re
        _ua_match = re.compile(config.ua_spiders, re.I)

    return _ua_match.search(ua) is not None


def parseQueryString(qstr):
    """ Parse a querystring "key=value&..." into a dict.
    """
    import urllib

    values = {}
    pairs = qstr.split('&')
    for pair in pairs:
        key, val = pair.split('=')
        values[urllib.unquote(key)] = urllib.unquote(val)

    return values


def makeQueryString(qstr={}, **kw):
    """ Make a querystring from a dict. Keyword parameters are
        added as-is, too.

        If a string is passed in, it's returned verbatim and
        keyword parameters are ignored.
    """
    if isinstance(qstr, type({})):
        import urllib

        qstr = '&'.join([
            urllib.quote_plus(name) + "=" + urllib.quote_plus(str(value))
                for name, value in qstr.items() + kw.items()
        ])

    return qstr


def getIntegerInput(request, fieldname, default=None, minval=None, maxval=None):
    """ Get an integer value from a request parameter. If the value
        is out of bounds, it's made to fit into those bounds.

        Returns `default` in case of errors (not a valid integer, or field
        is missing).
    """
    try:
        result = int(request.form[fieldname].value)
    except (KeyError, ValueError):
        return default
    else:
        if minval is not None:
            result = max(result, minval)
        if maxval is not None:
            result = min(result, maxval)
        return result


def getLinkIcon(request, formatter, scheme):
    """ Get icon for fancy links, or '' if user doesn't
        want them.
    """
    if not request.user.show_fancy_links: return ''

    icon = ("www", 11, 11)
    if scheme == "mailto": icon = ("email", 14, 10)
    if scheme == "news": icon = ("news", 10, 11)
    if scheme == "telnet": icon = ("telnet", 10, 11)
    if scheme == "ftp": icon = ("ftp", 11, 11)
    if scheme == "file": icon = ("ftp", 11, 11)
    #!!! use a map?
    # http|https|ftp|nntp|news|mailto|wiki|file

    return formatter.image(
        src="%s/img/moin-%s.gif" % (config.url_prefix, icon[0]),
        width=icon[1], height=icon[2], border=0, hspace=4,
        alt="[%s]" % icon[0].upper(),
        title="[%s]" % icon[0].upper(),
        )


def makeSelection(name, values, selectedval=None):
    """ Make a HTML <select> element named `name` from a value list.
        The list can either be a list of strings, or a list of
        (value, label) tuples.

        `selectedval` is the value that should be pre-selected.
    """
    from MoinMoin.widget import html

    result = html.SELECT(name=name)
    for val in values:
        if not isinstance(val, type(())):
            val = (val, val)
        result.append(html.OPTION(
            value=val[0], selected=(val[0] == selectedval))
            .append(html.Text(val[1]))
        )

    return result


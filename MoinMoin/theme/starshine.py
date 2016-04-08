# -*- coding: iso-8859-1 -*-
"""
    MoinMoin starshine theme (dark) - thanks to Heather Stern.

    @copyright: 2003 by ThomasWaldmann (LinuxWiki:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.theme.classic import Theme as ThemeBase

class Theme(ThemeBase):
    """ This is the starshine theme. """

    name = 'starshine'

    icons = {
        # key         alt                        filename of icon    w   h   
        # -------------------------------------------------------------------
        # navibar
        'help':       ("%(page_help_contents)s", "moin-help.png",   21, 32),
        'find':       ("%(page_find_page)s",     "moin-find.png",   21, 32),
        'diff':       ("Diffs",                  "moin-diff.png",   21, 32),
        'info':       ("Info",                   "moin-info.png",   21, 32),
        'edit':       ("Edit",                   "moin-edit.png",   21, 32),
        'unsubscribe':("Unsubscribe",            "moin-unsubscribe.png",  21, 32),
        'subscribe':  ("Subscribe",              "moin-subscribe.png",21, 32),
        'raw':        ("Raw",                    "moin-raw.png",    21, 32),
        'xml':        ("XML",                    "moin-xml.png",    21, 32),
        'print':      ("Print",                  "moin-print.png",  21, 32),
        'view':       ("View",                   "moin-show.png",   21, 32),
        'home':       ("Home",                   "moin-home.png",   21, 32),
        'up':         ("Up",                     "moin-parent.png", 21, 32),
        # FileAttach
        'attach':     ("%(attach_count)s",       "moin-attach.png",  7, 15),
        # RecentChanges
        'rss':        ("[RSS]",                  "moin-rss.png",    36, 14),
        'deleted':    ("[DELETED]",              "moin-deleted.png",60, 12),
        'updated':    ("[UPDATED]",              "moin-updated.png",60, 12),
        'new':        ("[NEW]",                  "moin-new.png",    31, 12),
        'diffrc':     ("[DIFF]",                 "moin-diff.png",   15, 11),
        # General
        'bottom':     ("[BOTTOM]",               "moin-bottom.png", 14, 10),
        'top':        ("[TOP]",                  "moin-top.png",    14, 10),
        'www':        ("[WWW]",                  "moin-www.png",    11, 11),
        'mailto':     ("[MAILTO]",               "moin-email.png",  14, 10),
        'news':       ("[NEWS]",                 "moin-news.png",   10, 11),
        'telnet':     ("[TELNET]",               "moin-telnet.png", 10, 11),
        'ftp':        ("[FTP]",                  "moin-ftp.png",    11, 11),
        'file':       ("[FILE]",                 "moin-ftp.png",    11, 11),
        # search forms
        'searchbutton': ("[?]",                  "moin-search.png", 12, 12),
        'interwiki':  ("[%(wikitag)s]",          "moin-inter.png",  16, 16),
    }

    stylesheets = ThemeBase.stylesheets + (
        # theme charset         media       basename
        (name,  'iso-8859-1',   'screen',   'screen'),
    )

def execute(request):
    return Theme(request)


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - List all defined smileys

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    [[ShowSmileys]] will display a table of all the available smileys.

    Based on code by Nick Trout <trout@users.sf.net>

    $Id: ShowSmileys.py,v 1.3 2003/11/09 21:01:04 thomaswaldmann Exp $
"""

# Imports
from MoinMoin import config, wikiutil
from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.widget.browser import DataBrowserWidget

COLUMNS = 3

def execute(macro, args):
    _ = macro.request.getText
    fmt = macro.formatter

    # create data description
    data = TupleDataset()
    data.columns = []
    for dummy in range(COLUMNS):
        data.columns.extend([
            Column('markup', label=_('Markup')),
            Column('image', label=_('Display'), align='center'),
            Column('filename', label=_('Filename')),
            Column('', label=''),
        ])
    data.columns[-1].hidden = 1

    # iterate over smileys, in groups of size COLUMNS
    smileys = config.smileys.items()
    smileys.sort()
    for idx in range(0, len(smileys), COLUMNS):
        row = []
        for off in range(COLUMNS):
            if idx+off < len(smileys):
                markup, smiley = smileys[idx+off]
                img = wikiutil.getSmiley(markup, fmt)
                row.extend([
                    fmt.code(1) + fmt.text(markup) + fmt.code(0),
                    fmt.rawHTML(img),
                    fmt.code(1) + smiley[3] + fmt.code(0),
                    '',
                ])
            else:
                row.extend(['&nbsp;'] * 4)
        data.addRow(tuple(row))

    # display table
    if data:
        browser = DataBrowserWidget(macro.request)
        browser.setData(data)
        return browser.toHTML()

    return ''


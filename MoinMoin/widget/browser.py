# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - DataBrowserWidget

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: browser.py,v 1.5 2003/11/09 21:01:17 thomaswaldmann Exp $
"""

from MoinMoin.widget import base


class DataBrowserWidget(base.Widget):

    def __init__(self, request, **kw):
        base.Widget.__init__(self, request, **kw)
        self.data = None

    def setData(self, dataset):
        """ Sets the data for the browser (see MoinMoin.util.dataset).
        """
        self.data = dataset

    def toHTML(self):
        fmt = self.request.formatter

        result = []
        result.append(fmt.table(1, {
                'border': 1,
                'cellpadding': 3,
                'cellspacing': 0,
            }))

        # add header line
        result.append(fmt.table_row(1))
        for col in self.data.columns:
            if col.hidden: continue
            result.append(fmt.table_cell(1, {'align': 'center'}))
            result.append(fmt.strong(1))
            result.append(col.label or col.name)
            result.append(fmt.strong(0))
            result.append(fmt.table_cell(0))
        result.append(fmt.table_row(0))

        # add data
        self.data.reset()
        row = self.data.next()
        while row:
            result.append(fmt.table_row(1))
            for idx in range(len(row)):
                if self.data.columns[idx].hidden: continue
                attrs = {}
                if self.data.columns[idx].align:
                    attrs['align'] = self.data.columns[idx].align
                result.append(fmt.table_cell(1, attrs))
                result.append(str(row[idx]))
                result.append(fmt.table_cell(0))
            result.append(fmt.table_row(0))
            row = self.data.next()

        result.append(fmt.table(0))
        return ''.join(result)


    def render(self):
        self.request.write(self.toHTML())


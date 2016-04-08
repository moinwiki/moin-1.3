"""
    MoinMoin - Processor for CSV data

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: CSV.py,v 1.2 2002/04/17 19:24:58 jhermann Exp $
"""

import string, sys

def process(request, formatter, lines):
    # parse bangpath for arguments
    exclude = []
    for arg in string.split(lines[0])[1:]:
        if arg[0] == '-':
            try:
                idx = int(arg[1:])
            except ValueError:
                pass
            else:
                exclude.append(idx-1)

    # remove bang path, create output list
    del lines[0]
    output = []

    if lines[0]:
        # expect column headers in first line
        first = 1
    else:
        # empty first line, no bold headers
        first = 0
        del lines[0]

    output.append(formatter.table(1))
    for line in lines:
        output.append(formatter.table_row(1))
        cells = string.split(line, ';')
        for idx in range(len(cells)):
            if idx in exclude: continue
            output.append(formatter.table_cell(1))
            if first: output.append(formatter.strong(1))
            output.append(formatter.text(cells[idx]))
            if first: output.append(formatter.strong(0))
            output.append(formatter.table_cell(0))
        output.append(formatter.table_row(0))
        first = 0
    output.append(formatter.table(0))

    sys.stdout.write(string.join(output, ''))


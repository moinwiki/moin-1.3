# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Pagesize Statistics

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro creates a bar graph of page size classes.

    $Id: pagesize.py,v 1.8 2003/11/09 21:01:08 thomaswaldmann Exp $
"""

_debug = 0

import string
from MoinMoin import config, wikiutil
from MoinMoin.Page import Page


def linkto(pagename, request, params=''):
    _ = request.getText

    if not config.chart_options:
        return _('<div class="message"><b>Charts are not available!</b></div>')

    if _debug:
        return draw(pagename, request)

    page = Page(pagename)
    result = []
    data = {
        'url': page.url("action=chart&type=pagesize"),
    }
    data.update(config.chart_options)
    result.append('<img src="%(url)s" border="0" '
        'width="%(width)d" height="%(height)d">' % data)

    return string.join(result, '')


def _slice(data, lo, hi):
    data = data[:]
    if lo: data[:lo] = [None] * lo
    if hi < len(data): data[hi:] =  [None] * (len(data)-hi)
    return data


def draw(pagename, request):
    import bisect, cgi, sys, shutil, cStringIO
    from MoinMoin import config, webapi
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText
    style = Chart.GDC_3DBAR

    # get data
    pages = wikiutil.getPageDict(config.text_dir)
    sizes = [(p.size(), name) for name, p in pages.items()]
    sizes.sort()

    upper_bound = sizes[-1][0]
    bounds = [s*128 for s in range(1, 9)]
    if upper_bound >= 1024:
        bounds.extend([s*1024 for s in range(2, 9)])
    if upper_bound >= 8192:
        bounds.extend([s*8192 for s in range(2, 9)])
    if upper_bound >= 65536:
        bounds.extend([s*65536 for s in range(2, 9)])
        
    data = [None] * len(bounds)
    for size, name in sizes:
        idx = bisect.bisect(bounds, size)
        ##idx = int((size / upper_bound) * classes)
        data[idx] = (data[idx] or 0) + 1

    labels = ["%d" %b for b in bounds]

    # give us a chance to develop this
    if _debug:
        return "<p>data = %s</p>" % \
            string.join(map(cgi.escape, map(repr, [labels, data])), '<br>')

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    ##c.addData(ChartData(data, 'magenta'))
    c.addData(ChartData(_slice(data, 0, 7), 'blue'))
    if upper_bound >= 1024:
        c.addData(ChartData(_slice(data, 7, 14), 'green'))
    if upper_bound >= 8192:
        c.addData(ChartData(_slice(data, 14, 21), 'red'))
    if upper_bound >= 65536:
        c.addData(ChartData(_slice(data, 21, 28), 'magenta'))
    title = ''
    if config.sitename: title = "%s: " % config.sitename
    title = title + _('Page Size Distribution')
    c.option(
        annotation = (bisect.bisect(bounds, upper_bound), Color('black'), "%d %s" % sizes[-1]),
        title = title,
        xtitle = _('page size upper bound [bytes]'),
        ytitle = _('# of pages of this size'),
        title_font = c.GDC_GIANT,
        threed_depth = 2.0,
        requested_yinterval = 1.0,
        stack_type = c.GDC_STACK_LAYER
    )
    c.draw(style,
        (config.chart_options['width'], config.chart_options['height']),
        image, labels)

    # send HTTP headers
    headers = [
        "Content-Type: image/gif",
        "Content-Length: %d" % len(image.getvalue()),
    ]
    webapi.http_headers(request, headers)

    # copy the image
    image.reset()
    shutil.copyfileobj(image, sys.stdout, 8192)
    sys.exit(0)


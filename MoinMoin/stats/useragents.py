# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User-Agent Statistics

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro creates a pie chart of the type of user agents
    accessing the wiki.

    $Id: useragents.py,v 1.8 2003/11/09 21:01:08 thomaswaldmann Exp $
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
        'url': page.url("action=chart&type=useragents"),
    }
    data.update(config.chart_options)
    result.append('<img src="%(url)s" border="0" '
        'width="%(width)d" height="%(height)d">' % data)

    return string.join(result, '')


def draw(pagename, request):
    import cgi, sys, shutil, cStringIO, operator
    from MoinMoin import config, webapi
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText

    style = Chart.GDC_3DPIE

    # get data
    colors = ['red', 'mediumblue', 'yellow', 'deeppink', 'aquamarine', 'purple', 'beige',
              'blue', 'forestgreen', 'orange', 'cyan', 'fuchsia', 'lime']
    colors = ([Color(c) for c in colors])

    data = {}
    logdata = request.getEventLogger().read(['VIEWPAGE', 'SAVEPAGE'])
    for event in logdata:
        ua = event[2].get('HTTP_USER_AGENT')
        if ua:
            pos = ua.find(" (compatible; ")
            if pos >= 0: ua = ua[pos:].split(';')[1].strip()
            else: ua = ua.split()[0]
            #ua = ua.replace(';', '\n')
            data[ua] = data.get(ua, 0) + 1
    data = [(cnt, ua) for ua, cnt in data.items()]
    data.sort()
    data.reverse()
    maxdata = len(colors) - 1
    if len(data) > maxdata:
        others = [x[0] for x in data[maxdata:]]
        data = data[:maxdata] + [(reduce(operator.add, others, 0), _('Others'))]

    # shift front to end if others is very small
    if data[-1][0] * 10 < data[0][0]:
        data = data[1:] + data[0:1]

    labels = [x[1] for x in data]
    data = [x[0] for x in data]

    # give us a chance to develop this
    if _debug:
        return "<p>data = %s</p>" % \
            string.join(map(cgi.escape, map(repr, [labels, data])), '<br>')

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    c.addData(data)

    title = ''
    if config.sitename: title = "%s: " % config.sitename
    title = title + _('Distribution of User-Agent Types')
    c.option(
        pie_color = colors,
        label_font = Chart.GDC_SMALL,
        label_line = 1,
        label_dist = 20,
        threed_depth = 20,
        threed_angle = 225,
        percent_labels = Chart.GDCPIE_PCT_RIGHT,
        title_font = c.GDC_GIANT,
        title = title)
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


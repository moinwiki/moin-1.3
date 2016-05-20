# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User-Agent Statistics

    This macro creates a pie chart of the type of user agents
    accessing the wiki.

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

_debug = 0

from MoinMoin import wikiutil, caching
from MoinMoin.logfile import eventlog
from MoinMoin.Page import Page
from MoinMoin.util import MoinMoinNoFooter


def linkto(pagename, request, params=''):
    from MoinMoin.util import web
    _ = request.getText

    if not request.cfg.chart_options:
        return (request.formatter.sysmsg(1) +
                request.formatter.text(_('Charts are not available!')) +
                request.formatter.sysmsg(0))

    if _debug:
        return draw(pagename, request)

    page = Page(request, pagename)

    # Create escaped query string from dict and params
    querystr = {'action': 'chart', 'type': 'useragents'}
    querystr = web.makeQueryString(querystr)
    querystr = wikiutil.escape(querystr)
    if params:
        querystr += '&amp;' + params
    
    # TODO: remove escape=0 in 1.4
    data = {'url': page.url(request, querystr, escape=0)}
    data.update(request.cfg.chart_options)
    result = ('<img src="%(url)s" width="%(width)d" height="%(height)d"'
              ' alt="useragents chart">') % data

    return result


def draw(pagename, request):
    import shutil, cStringIO, operator
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText

    style = Chart.GDC_3DPIE

    # get data
    colors = ['red', 'mediumblue', 'yellow', 'deeppink', 'aquamarine', 'purple', 'beige',
              'blue', 'forestgreen', 'orange', 'cyan', 'fuchsia', 'lime']
    colors = ([Color(c) for c in colors])

    # get results from cache
    cache = caching.CacheEntry(request, 'charts', 'useragents')
    if cache.exists():
        try:
            cache_date, data = eval(cache.content())
        except:
            cache_date, data = 0, {}
    else:
        cache_date, data = 0, {}
    
    logfile = eventlog.EventLog(request)
    logfile.set_filter(['VIEWPAGE', 'SAVEPAGE'])
    new_date = logfile.date()
    for event in logfile.reverse():
        if event[0] <= cache_date:
            break
        ua = event[2].get('HTTP_USER_AGENT')
        if ua:
            pos = ua.find(" (compatible; ")
            if pos >= 0:
                ua = ua[pos:].split(';')[1].strip()
            else:
                ua = ua.split()[0]
            #ua = ua.replace(';', '\n')
            data[ua] = data.get(ua, 0) + 1

    # write results to cache
    cache.update("(%r, %r)" % (new_date, data))
            
    data = [(cnt, ua) for ua, cnt in data.items()]
    data.sort()
    data.reverse()
    maxdata = len(colors) - 1
    if len(data) > maxdata:
        others = [x[0] for x in data[maxdata:]]
        data = data[:maxdata] + [(reduce(operator.add, others, 0), _('Others').encode('iso-8859-1', 'replace'))] # gdchart can't do utf-8

    # shift front to end if others is very small
    if data[-1][0] * 10 < data[0][0]:
        data = data[1:] + data[0:1]

    labels = [x[1] for x in data]
    data = [x[0] for x in data]

    # give us a chance to develop this
    if _debug:
        return "<p>data = %s</p>" % \
            '<br>'.join(map(wikiutil.escape, map(repr, [labels, data])))

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    c.addData(data)

    title = ''
    if request.cfg.sitename: title = "%s: " % request.cfg.sitename
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
        title = title.encode('iso-8859-1', 'replace')) # gdchart can't do utf-8
    labels = [label.encode('iso-8859-1', 'replace') for label in labels]
    c.draw(style,
        (request.cfg.chart_options['width'], request.cfg.chart_options['height']),
        image, labels)

    # send HTTP headers
    headers = [
        "Content-Type: image/gif",
        "Content-Length: %d" % len(image.getvalue()),
    ]
    request.http_headers(headers)

    # copy the image
    image.reset()
    shutil.copyfileobj(image, request, 8192)
    raise MoinMoinNoFooter


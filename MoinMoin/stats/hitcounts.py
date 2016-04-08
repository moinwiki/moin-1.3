"""
    MoinMoin - Hitcount Statistics

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro creates a hitcount chart from the data in "event.log".

    $Id: hitcounts.py,v 1.5 2002/02/02 12:18:48 jhermann Exp $
"""

_debug = 0

import string
from MoinMoin import config
from MoinMoin.Page import Page
from MoinMoin.i18n import _


def linkto(pagename, params=''):
    if not config.chart_options:
        return _('<div class="message"><b>Charts are not available!</b></div>')

    if _debug:
        return draw(pagename, {})

    page = Page(pagename)
    result = []
    if params: params = '&' + params
    data = {
        'url': page.url("action=chart&type=hitcounts" + params),
    }
    data.update(config.chart_options)
    result.append('<img src="%(url)s" border="0" '
        'width="%(width)d" height="%(height)d">' % data)

    return string.join(result, '')


def draw(pagename, form):
    import cgi, sys, shutil, cStringIO
    from MoinMoin import config, webapi, eventlog, user
    from MoinMoin.stats.chart import Chart, ChartData, Color

    # check params
    filterpage = None
    if form and form.has_key('page'):
        filterpage = form['page'].value

    # prepare data
    days = []
    views = []
    edits = []
    ratchet_day = None
    ratchet_time = None
    data = eventlog.logger.read(['VIEWPAGE', 'SAVEPAGE'])
    for event in data:
        #print ">>>", cgi.escape(repr(event)), "<br>"
        if filterpage and event[2]['pagename'] != filterpage:
            continue
        time_tuple = user.current.getTime(event[0])
        day = tuple(time_tuple[0:3])
        if day != ratchet_day:
            # new day
            # !!! this is not really correct, if we have days
            # without data, we have to add more 0 values
            while ratchet_time:
                ratchet_time += 86400
                rday = user.current.getTime(ratchet_time)
                if rday > day: break
                days.append(user.current.getFormattedDate(ratchet_time))
                views.append(0)
                edits.append(0)
            days.append(user.current.getFormattedDate(event[0]))
            views.append(0)
            edits.append(0)
            ratchet_day = day
            ratchet_time = event[0]
        if event[1] == 'VIEWPAGE':
            views[-1] = views[-1] + 1
        elif event[1] == 'SAVEPAGE':
            edits[-1] = edits[-1] + 1

    # give us a chance to develop this
    if _debug:
        return "labels = %s<br>views = %s<br>edits = %s<br>" % \
            tuple(map(cgi.escape, map(repr, [days, views, edits])))

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    c.addData(ChartData(views, color='green'))
    c.addData(ChartData(edits, color='red'))
    chart_title = ''
    if config.sitename: chart_title = "%s: " % config.sitename
    chart_title = chart_title + _('Page hits and edits')
    if filterpage: chart_title = _("%(chart_title)s for %(filterpage)s") % locals()
    c.option(
        annotation = (len(days)-1, Color('black'), _("green=view\nred=edit")),
        title = chart_title,
        xtitle = _('date'),
        ytitle = _('# of hits'),
        title_font = c.GDC_GIANT,
        #thumblabel = 'THUMB', thumbnail = 1, thumbval = 10,
        #ytitle_color = Color('green'),
        #yaxis2 = 1,
        #ytitle2 = '# of edits',
        #ytitle2_color = Color('red'),
        #ylabel2_color = Color('black'),
        #interpolations = 0,
        threed_depth = 1.0,
        requested_yinterval = 1.0,
        stack_type = c.GDC_STACK_BESIDE
    )
    c.draw(c.GDC_LINE,
        (config.chart_options['width'], config.chart_options['height']),
        image, days)

    # send HTTP headers
    headers = [
        "Content-Type: image/gif",
        "Content-Length: %d" % len(image.getvalue()),
    ]
    webapi.http_headers(headers)

    # copy the image
    image.reset()
    shutil.copyfileobj(image, sys.stdout, 8192)
    sys.exit(0)


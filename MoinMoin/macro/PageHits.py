"""
    per page hit statistics

    @copyright: 2004 Thomas Waldmann
    @license: GNU GPL, see COPYING for details

"""

from MoinMoin import caching
from MoinMoin.Page import Page
from MoinMoin.logfile import eventlog

def execute(macro, args):
    request = macro.request
    cache = caching.CacheEntry(request, 'charts', 'pagehits')
    if cache.exists():
        try:
            cache_date, pagehits = eval(cache.content())
        except:
            cache_date, pagehits = 0, {}
    else:
        cache_date, pagehits = 0, {}

    event_log = eventlog.EventLog(request)
    event_log.set_filter(['VIEWPAGE'])
    new_date = event_log.date()
    
    for event in event_log.reverse():
        if event[0] <=  cache_date:
            break
        page = event[2].get('pagename','')
        if page in ['CVS',]: continue
        if page:
            pagehits[page] = pagehits.get(page,0) + 1

    # save to cache
    cache.update("(%r, %r)" % (new_date, pagehits))
    
    # get hits and sort them
    hits = []
    for pagename, hit in pagehits.items():
        if Page(request, pagename).exists() and request.user.may.read(pagename):
            hits.append((hit, pagename))
    hits.sort()
    hits.reverse()

    # format list
    result = []
    result.append(macro.formatter.number_list(1))
    for hit, pagename in hits:
        result.extend([
            macro.formatter.listitem(1),
            macro.formatter.code(1),
            ("%6d" % hit).replace(" ", "&nbsp;"), " ",
            macro.formatter.code(0),
            macro.formatter.pagelink(1, pagename, generated=1),
            macro.formatter.text(pagename),
            macro.formatter.pagelink(0, pagename),
            macro.formatter.listitem(0),
        ])
    result.append(macro.formatter.number_list(0))

    return ''.join(result)


"""
    MoinMoin - XML Parser

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: xslt.py,v 1.5 2001/03/30 21:06:52 jhermann Exp $
"""

# Imports
import cgi, string

from MoinMoin import caching, user, util, wikiutil


#############################################################################
### XML Parser
#############################################################################

class Parser:
    """
        Send XML file formatted via XSLT.
    """

    def __init__(self, raw):
        self.raw = raw

    def format(self, formatter, form):
        """ Send the text.
        """
        arena = "xslt"
        key   = wikiutil.quoteFilename(formatter.page.page_name)
        cache = caching.CacheEntry(arena, key)
        if not cache.needsUpdate(formatter.page._text_filename()):
            print cache.content()
            self._add_refresh(formatter, cache, arena, key)
            return

        import xml.sax
        import xml.xslt
        import xml.xslt.Processor

        from MoinMoin import xsltutil

        processor = xml.xslt.Processor.Processor()
        processor.setStylesheetReader(xsltutil.MoinStylesheetReader(self))
        msg = None
        try:
            result = processor.runString(self.raw)
        except xml.sax.SAXParseException, msg:
            etype = "SAX"
        except xml.sax.SAXException, msg:
            etype = "SAX"
        except xml.xslt.XsltException, msg:
            etype = "XSLT"
        except IOError, msg:
            etype = "I/O"

        if msg:
            text = cgi.escape(self.raw)
            text = string.expandtabs(text)
            text = string.replace(text, '\n', '<br>\n')
            text = string.replace(text, ' ', '&nbsp;')
            print "<b>%s: %s</b><p>" % (
                user.current.text('%(errortype)s processing error') % {'errortype': etype},
                msg,), text
        else:
            print result
            cache.update(result)
            self._add_refresh(formatter, cache, arena, key)

    def _add_refresh(self, formatter, cache, arena, key):
        refresh = wikiutil.link_tag(
            wikiutil.quoteWikiname(formatter.page.page_name) +
                "?action=refresh&arena=%s&key=%s" % (arena, key),
            user.current.text("RefreshCache")) + user.current.text(' for this page (cached %(date)s)') % {
                'date': user.current.getFormattedDateTime(cache.mtime()),} + '<br>'
        wikiutil.add2footer('RefreshCache', refresh)


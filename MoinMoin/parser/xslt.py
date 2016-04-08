"""
    MoinMoin - XML Parser

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: xslt.py,v 1.14 2002/05/10 11:39:01 jhermann Exp $
"""

# Imports
import cgi, string

from MoinMoin import caching, config, user, util, wikiutil
from MoinMoin.i18n import _


#############################################################################
### XML Parser
#############################################################################

class Parser:
    """
        Send XML file formatted via XSLT.
    """

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request

    def format(self, formatter, form):
        """ Send the text.
        """
        if not config.allow_xslt:
            from MoinMoin.parser import plain
            print formatter.sysmsg(_('XSLT option disabled!'))
            plain.Parser(self.raw, self.request).format(formatter, form)
            return

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

        from MoinMoin.wikixml import xsltutil

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
                _('%(errortype)s processing error') % {'errortype': etype},
                msg,), text
        else:
            print result
            cache.update(result)
            self._add_refresh(formatter, cache, arena, key)

    def _add_refresh(self, formatter, cache, arena, key):
        refresh = wikiutil.link_tag(
            wikiutil.quoteWikiname(formatter.page.page_name) +
                "?action=refresh&arena=%s&key=%s" % (arena, key),
            _("RefreshCache")) + _(' for this page (cached %(date)s)') % {
                'date': formatter.request.user.getFormattedDateTime(cache.mtime()),} + '<br>'
        self.request.add2footer('RefreshCache', refresh)


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - XML Parser

    This code works with 4Suite 1.0a1 or higher only!

    @copyright: 2001, 2003 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import StringIO
from MoinMoin import caching, config, wikiutil, Page

class Parser:
    """
        Send XML file formatted via XSLT.
    """

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.form = request.form
        self._ = request.getText


    def format(self, formatter):
        """ Send the text.
        """
        _ = self._
        if not self.request.cfg.allow_xslt:
            from MoinMoin.parser import plain
            self.request.write(formatter.sysmsg(1) +
                               formatter.text(_('XSLT option disabled!'))+
                               formatter.sysmsg(0))
            plain.Parser(self.raw, self.request).format(formatter)
            return

        arena = page
        key   = 'xslt'
        cache = caching.CacheEntry(self.request, arena, key)
        if not cache.needsUpdate(formatter.page._text_filename()):
            self.request.write(cache.content())
            self._add_refresh(formatter, cache, arena, key)
            return

        try:
            # assert we have 4Suite 1.x available
            from Ft.Xml import __version__ as ft_version
            assert ft_version.startswith('1.')
        except (ImportError, AssertionError):
            self.request.write(self.request.formatter.sysmsg(1) +
                               self.request.formatter.text(_('XSLT processing is not available!')) +
                               self.request.formatter.sysmsg(0))
        else:
            import xml.sax
            from Ft.Lib import Uri
            from Ft.Xml import InputSource
            from Ft.Xml.Xslt.Processor import Processor

            processor = Processor()
            msg = None
            try:
                base_uri = u'wiki://Self/'

                # patch 4Suite 1.0a1
                if ft_version == "1.0a":
                    class MoinResolver(Uri.SchemeRegistryResolver):
                        def normalize(self, uri, base):
                            from Ft.Lib import Uri

                            scheme = Uri._getScheme(uri)
                            if not scheme:
                                if base:
                                    scheme = Uri._getScheme(base)
                                if not scheme:
                                    return Uri.BaseUriResolver.normalize(self, uri, base)
                                else:
                                    uri = Uri.Absolutize(uri, base)
                                    if not uri:
                                        return base
                            return uri
                else:
                    MoinResolver = Uri.SchemeRegistryResolver

                wiki_resolver = MoinResolver()

                def _resolve_page(uri, base=None, Uri=Uri, base_uri=base_uri, resolver=wiki_resolver):
                    """ Check whether uri is a valid pagename.
                    """
                    if uri.startswith(base_uri):
                        page = Page.Page(uri[len(base_uri):].encode(config.charset))
                        if page.exists():
                            return StringIO.StringIO(page.get_raw_body())
                        else:
                            raise Uri.UriException(Uri.UriException.RESOURCE_ERROR, uri,
                                'Page does not exist')
                    return Uri.BaseUriResolver.resolve(resolver, uri, base)

                wiki_resolver.handlers = {
                    'wiki': _resolve_page,
                }


                out_file = StringIO.StringIO()
                input_factory = InputSource.InputSourceFactory(
                    resolver=wiki_resolver
                )
                page_uri = u"%s%s" % (base_uri, unicode(formatter.page.page_name, config.charset))

                processor.run(
                    input_factory.fromString(self.raw, uri=page_uri),
                    outputStream=out_file)

                result = out_file.getvalue()
            except xml.sax.SAXParseException, msg:
                etype = "SAX"
            except xml.sax.SAXException, msg:
                etype = "SAX"
            #!!! add error handling for 4Suite exceptions
            #except xml.xslt.XsltException, msg:
            #    etype = "XSLT"
            except IOError, msg:
                etype = "I/O"

            if msg:
                text = wikiutil.escape(self.raw)
                text = text.expandtabs()
                text = text.replace('\n', '<br>\n')
                text = text.replace(' ', '&nbsp;')
                self.request.write("<strong>%s: %s</strong><p>" % (
                    _('%(errortype)s processing error') % {'errortype': etype},
                    msg,) + text)
            else:
                self.request.write(result)
                cache.update(result)
                self._add_refresh(formatter, cache, arena, key)

    def _add_refresh(self, formatter, cache, arena, key):
        _ = self._
        refresh = wikiutil.link_tag(
            formatter.request,
            wikiutil.quoteWikinameURL(formatter.page.page_name) + "?action=refresh&arena=%s&key=%s" % (arena, key),
            _("RefreshCache")
        ) + ' ' + _('for this page (cached %(date)s)') % {
            'date': formatter.request.user.getFormattedDateTime(cache.mtime()),
        } + '<br>'
        self.request.add2footer('RefreshCache', refresh)



#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dump a MoinMoin wiki to static pages

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

__version__ = "20040329"

# use this if your moin installation is not in sys.path:
import sys
sys.path.insert(0, '../..') # path to MoinMoin

logo_html = '<img src="moinmoin.png">'

url_prefix = "."
HTML_SUFFIX = ".html"

page_template = u'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=%(charset)s">
<title>%(pagename)s</title>
<link rel="stylesheet" type="text/css" media="all" charset="utf-8" href="%(theme)s/css/common.css">
<link rel="stylesheet" type="text/css" media="screen" charset="utf-8" href="%(theme)s/css/screen.css">
<link rel="stylesheet" type="text/css" media="print" charset="utf-8" href="%(theme)s/css/print.css">
</head>
<body>
<table>
<tr>
<td>
%(logo_html)s
</td>
<td>
%(navibar_html)s
</td>
</tr>
</table>
<hr>
%(pagehtml)s
<hr>
%(timestamp)s
</body>
</html>
'''

import os, time, StringIO, codecs, shutil
from MoinMoin import config, wikiutil, Page
from MoinMoin.scripts import _util
from MoinMoin.request import RequestCLI

class MoinDump(_util.Script):
    def __init__(self):
        _util.Script.__init__(self, __name__, "[options] <target-directory>")

        # --config=DIR            
        self.parser.add_option(
            "--config", metavar="DIR", dest="configdir",
            help="Path to wikiconfig.py (or its directory)"
        )

        # --wiki=URL             
        self.parser.add_option(
            "--wiki", metavar="WIKIURL", dest="wiki_url",
            help="URL of wiki to dump (e.g. moinmaster.wikiwikiweb.de)"
        )
        
        # --page=NAME             
        self.parser.add_option(
            "--page", metavar="NAME", dest="page",
            help="Dump a single page (with possibly broken links)"
        )

    def mainloop(self):
        """ moin-dump's main code. """

        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        # Prepare output directory
        outputdir = self.args[0]
        outputdir = os.path.abspath(outputdir)
        if not os.path.isdir(outputdir):
            try:
                os.mkdir(outputdir)
                _util.log("Created output directory '%s'!" % outputdir)
            except OSError:
                _util.fatal("Cannot create output directory '%s'!" % outputdir)

        # Load the configuration
        configdir = self.options.configdir
        if configdir:
            if os.path.isfile(configdir): configdir = os.path.dirname(configdir)
            if not os.path.isdir(configdir):
                _util.fatal("Bad path given to --config parameter")
            configdir = os.path.abspath(configdir)
            sys.path[0:0] = [configdir]
            os.chdir(configdir)

        # Dump the wiki
        request = RequestCLI(self.options.wiki_url)
        request.form = request.args = request.setup_args()

        # fix url_prefix so we get relative paths in output html
        request.cfg.url_prefix = url_prefix

        if self.options.page:
            pages = [self.options.page]
        else:
            # Get all existing pages in the wiki
            pages = list(request.rootpage.getPageList(user=''))
        pages.sort()

        wikiutil.quoteWikinameURL = lambda pagename, qfn=wikiutil.quoteWikinameFS: (qfn(pagename) + HTML_SUFFIX)

        errfile = os.path.join(outputdir, 'error.log')
        errlog = open(errfile, 'w')
        errcnt = 0

        page_front_page = wikiutil.getSysPage(request, 'FrontPage').page_name
        page_title_index = wikiutil.getSysPage(request, 'TitleIndex').page_name
        page_word_index = wikiutil.getSysPage(request, 'WordIndex').page_name
        
        navibar_html = ''
        for p in [page_front_page, page_title_index, page_word_index]:
            navibar_html += '&nbsp;[<a href="%s">%s</a>]' % (wikiutil.quoteWikinameFS(p), wikiutil.escape(p))

        for pagename in pages:
            file = wikiutil.quoteWikinameURL(pagename) # we have the same name in URL and FS
            _util.log('Writing "%s"...' % file)
            try:
                pagehtml = ''
                page = Page.Page(request, pagename)
                try:
                    request.reset()
                    out = StringIO.StringIO()
                    request.redirect(out)
                    page.send_page(request, count_hit=0, content_only=1)
                    pagehtml = out.getvalue()
                    request.redirect()
                except:
                    errcnt = errcnt + 1
                    print >>sys.stderr, "*** Caught exception while writing page!"
                    print >>errlog, "~" * 78
                    print >>errlog, file # page filename
                    import traceback
                    traceback.print_exc(None, errlog)
            finally:
                timestamp = time.strftime("%Y-%m-%d %H:%M")
                filepath = os.path.join(outputdir, file)
                fileout = codecs.open(filepath, 'w', config.charset)
                fileout.write(page_template % {
                    'charset': config.charset,
                    'pagename': pagename,
                    'pagehtml': pagehtml,
                    'logo_html': logo_html,
                    'navibar_html': navibar_html,
                    'timestamp': timestamp,
                    'theme': request.cfg.theme_default,
                })
                fileout.close()

        # copy FrontPage to "index.html"
        indexpage = page_front_page
        if self.options.page:
            indexpage = self.options.page
        shutil.copyfile(
            os.path.join(outputdir, wikiutil.quoteWikinameFS(indexpage) + HTML_SUFFIX),
            os.path.join(outputdir, 'index' + HTML_SUFFIX)
        )

        errlog.close()
        if errcnt:
            print >>sys.stderr, "*** %d error(s) occurred, see '%s'!" % (errcnt, errfile)

def run():
    MoinDump().run()

if __name__ == "__main__":
    run()


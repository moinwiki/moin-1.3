# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Dump a MoinMoin wiki to static pages

Copyright (c) 2002, 2003 by Jürgen Hermann <jh@web.de>
All rights reserved, see COPYING for details.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""
# $Id: moin_dump.py,v 1.11 2003/11/09 21:01:07 thomaswaldmann Exp $
__version__ = "$Revision: 1.11 $"[11:-2]

from MoinMoin.scripts import _util

#############################################################################
### Helpers
#############################################################################

HTML_SUFFIX = ".html"  # perhaps put this in config.py as html_suffix?


#############################################################################
### Main program
#############################################################################

class MoinDump(_util.Script):
    def __init__(self):
        _util.Script.__init__(self, __name__, "[options] <target-directory>")

        # --config=DIR            
        self.parser.add_option(
            "--config", metavar="DIR", dest="configdir",
            help="Path to moin_config.py (or its directory)"
        )

        # --page=NAME             
        self.parser.add_option(
            "--page", metavar="NAME", dest="page",
            help="Dump a single page (with possibly broken links)"
        )
        

    def mainloop(self):
        """ moin-dump's main code.
        """
        import os, sys

        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        #
        # Prepare output directory
        #
        outputdir = self.args[0]
        outputdir = os.path.abspath(outputdir)
        if not os.path.isdir(outputdir):
            try:
                os.mkdir(outputdir)
                _util.log("Created output directory '%s'!" % outputdir)
            except OSError:
                _util.fatal("Cannot create output directory '%s'!" % outputdir)

        #
        # Load the configuration
        #
        configdir = self.options.configdir
        if configdir:
            if os.path.isfile(configdir): configdir = os.path.dirname(configdir)
            if not os.path.isdir(configdir):
                _util.fatal("Bad path given to --config parameter")
            configdir = os.path.abspath(configdir)
            sys.path[0:0] = [configdir]
            os.chdir(configdir)

        from MoinMoin import config
        if config.default_config:
            _util.fatal("You have to be in the directory containing moin_config.py, "
                "or use the --config option!")

        # fix some values so we get relative paths in output html
        # XXX maybe this should be configurable
        config.url_prefix = "."
        config.css_url    = "./moinmoin.css"

        #
        # Dump the wiki
        #
        from MoinMoin import cgimain
        request = cgimain.createRequest()

        import cgi
        request.form = cgi.FieldStorage(environ = {'QUERY_STRING': 'action=print'})

        from MoinMoin import wikiutil, Page
        if self.options.page:
            pages = [self.options.page]
        else:
            pages = list(wikiutil.getPageList(config.text_dir))
        pages.sort()

        qfn_html = lambda pagename, qfn=wikiutil.quoteWikiname: qfn(pagename) + HTML_SUFFIX
        #wikiutil.quoteFilename = qfn_html
        wikiutil.quoteWikiname = qfn_html

        errfile = os.path.join(outputdir, 'error.log')
        errlog = open(errfile, 'w')
        errcnt = 0

        for pagename in pages:
            file = wikiutil.quoteFilename(pagename) + HTML_SUFFIX
            _util.log('Writing "%s"...' % file)
            filepath = os.path.join(outputdir, file)
            out = open(filepath, 'w')
            try:
                page = Page.Page(pagename)
                sys.stdout = out
                try:
                    page.send_page(request)
                except:
                    errcnt = errcnt + 1
                    print >>sys.stderr, "*** Caught exception while writing page!"
                    print >>errlog, "~" * 78
                    import traceback
                    traceback.print_exc(None, errlog)
                else:
                    page_title_index = wikiutil.getSysPage('TitleIndex').page_name
                    page_word_index = wikiutil.getSysPage('WordIndex').page_name

                    print '<hr>'
                    print '[<a href="%s">FrontPage</a>]' % (wikiutil.quoteWikiname(config.page_front_page))
                    print '[<a href="%s">%s</a>]' % (
                        wikiutil.quoteWikiname(page_title_index), cgi.escape(page_title_index))
                    print '[<a href="%s">%s</a>]' % (
                        wikiutil.quoteWikiname(page_word_index), cgi.escape(page_word_index))
                    print '</body>'
                    print '</html>'
            finally:
                out.close()
                sys.stdout = sys.__stdout__

        # copy FrontPage to "index.html"
        indexpage = config.page_front_page
        if self.options.page:
            indexpage = self.options.page
        import shutil
        shutil.copyfile(
            os.path.join(outputdir, wikiutil.quoteFilename(indexpage) + HTML_SUFFIX),
            os.path.join(outputdir, 'index' + HTML_SUFFIX)
        )

        errlog.close()
        if errcnt:
            print >>sys.stderr, "*** %d error(s) occurred, see '%s'!" % (errcnt, errfile)

def run():
    MoinDump().run()

if __name__ == "__main__":
    run()

"""





"""

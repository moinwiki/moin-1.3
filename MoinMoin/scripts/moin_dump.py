"""
MoinMoin - Dump a MoinMoin wiki to static pages

Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
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
# $Id: moin_dump.py,v 1.5 2002/04/18 18:36:02 jhermann Exp $
__version__ = "$Revision: 1.5 $"[11:-2]


#############################################################################
### Helpers
#############################################################################

HTML_SUFFIX = ".html"  # perhaps put this in config.py as html_suffix?


#############################################################################
### Main program
#############################################################################

def usage():
    """ Print usage information.
    """
    import sys
    sys.stderr.write("""
%(cmd)s v%(version)s, Copyright (c) 2002 by Jürgen Hermann <jh@web.de>

Usage: %(cmd)s [options] <target-directory>

Options:
    -q, --quiet             Be quiet (no informational messages)
    --help                  This help text
    --version               Version information
    --config                Path to moin_config.py (or its directory)

""" % {'cmd': __name__.split('.')[-1].replace('_', '-'), 'version': __version__})
    sys.exit(1)


def version():
    """ Print version information.
    """
    import sys
    from MoinMoin import version
    sys.stderr.write("%s (%s %s [%s])\n" %
        (__version__, version.project, version.release, version.revision))
    sys.exit(1)


def main():
    """ moin-dump's main code.
    """
    import getopt, os, sys

    #
    # Check parameters
    #
    try:
        optlist, args = getopt.getopt(sys.argv[1:],
            'q',
            ['help', 'quiet', 'version', 'config='])
    except:
        _util.fatal("Invalid parameters!", usage=1)

    #print optlist, args

    if _util.haveOptions(optlist, ["--version"]): version()
    if not (optlist or args) or _util.haveOptions(optlist, ["--help"]): usage()
    if len(args) < 1: usage()
    
    _util.flag_quiet = _util.haveOptions(optlist, ["-q", "--quiet"])

    #
    # Load the configuration
    #
    outputdir = args[0]
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
    configdir = _util.getOption(optlist, ["--config"])
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

    #
    # Dump the wiki
    #
    from MoinMoin import cgimain
    request = cgimain.createRequest()

    import cgi
    request.form = cgi.FieldStorage(environ = {'QUERY_STRING': 'action=print'})

    from MoinMoin import wikiutil, Page
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
                print '<hr>'
                print '[<a href="%s">FrontPage</a>]' % (wikiutil.quoteWikiname(config.page_front_page))
                print '[<a href="%s">TitleIndex</a>]' % (wikiutil.quoteWikiname(config.page_title_index))
                print '[<a href="%s">WordIndex</a>]' % (wikiutil.quoteWikiname(config.page_word_index))
                print '</body>'
                print '</html>'
        finally:
            out.close()
            sys.stdout = sys.__stdout__

    # copy FrontPage to "index.html"
    import shutil
    shutil.copyfile(
        os.path.join(outputdir, wikiutil.quoteFilename(config.page_front_page) + HTML_SUFFIX),
        os.path.join(outputdir, 'index' + HTML_SUFFIX)
    )

    errlog.close()
    if errcnt:
        print >>sys.stderr, "*** %d error(s) occurred, see '%s'!" % (errcnt, errfile)


def run():
    global _util
    from MoinMoin.scripts import _util
    _util.runMain(main)


if __name__ == "__main__": run()


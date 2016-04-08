"""
    MoinMoin - Teud Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This integrates the "Teud" documentation system into
    MoinMoin. Besides Teud, you need 4XSLT.

    Teud: http://purl.net/wiki/python/TeudProject
    4XSLT: http://4suite.org/

    $Id: TeudView.py,v 1.3 2001/10/22 23:08:34 jhermann Exp $
"""

_imperr = None
try:
    from teud import xmldoc, pydoc
except ImportError, _imperr:
    pass
try:
    from xml.xslt.Processor import Processor
except ImportError, _imperr:
    pass

import cgi, string
from MoinMoin import config


def execute(macro, args):
    if _imperr: return "Error in TeudView macro: " + str(_imperr)

    #dtdfile = xmldoc.getDTDPath()
    xslfile = xmldoc.getDataPath('webde.xsl')
    pagename = macro.formatter.page.page_name

    if macro.form.has_key('module'):
        modname = macro.form["module"].value
        try:
            object = pydoc.locate(modname)
        except pydoc.ErrorDuringImport, value:
            return "Error while loading module %s: %s" % (module, value)
        else:
            xmlstr = xmldoc.xml.document(object, encoding=config.charset)

        navigation = '<a href="%s">Index</a>' % pagename
        pathlen = string.count(modname, '.')
        if pathlen:
            navigation = navigation + ' | '
            modparts = string.split(modname, '.')
            for pathidx in range(pathlen):
                path = string.join(modparts[:pathidx+1], '.')
                navigation = navigation + '<a href="%s?module=%s">%s</a>' % (
                    pagename, path, modparts[pathidx])
                if pathidx < pathlen:
                    navigation = navigation + '.'
        navigation = navigation + '<hr size="1">'
    else:
        # generate index
        xmlstr = xmldoc.xml.document(None, encoding=config.charset)
        navigation = ''

    processor = Processor()
    processor.appendStylesheetFile(xslfile)
    try:
        result = processor.runString(xmlstr,
            topLevelParams = {
                'uri-prefix': pagename + "?module=",
                'uri-suffix': "",
            }
        )
    except:
        print cgi.escape(xmlstr)
        raise

    return navigation + result

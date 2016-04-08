"""
    MoinMoin - XSLT Utilities

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: xsltutil.py,v 1.1 2001/12/01 20:08:42 jhermann Exp $
"""
__version__ = "$Revision: 1.1 $"[11:-2]

# Imports
from xml.xslt.StylesheetReader import StylesheetReader
from MoinMoin import Page


#############################################################################
### Stylesheet Reader
#############################################################################

class MoinStylesheetReader(StylesheetReader):
    def __init__(self, parser, force8Bit=0):
        StylesheetReader.__init__(self, force8Bit)
        self.parser = parser

    def fromUri(self, uri, baseUri='', ownerDoc=None, stripElements=None):
        "Create a DOM from a URI"
        # check whether uri is a valid pagename
        page = Page.Page(uri)
        if page.exists():
            return StylesheetReader.fromString(self, page.get_raw_body(),
                baseUri, ownerDoc, stripElements)
        else:
            return StylesheetReader.fromUri(self, uri,
                baseUri, ownerDoc, stripElements)


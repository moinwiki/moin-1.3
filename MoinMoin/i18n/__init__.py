"""
    MoinMoin - Internationalization

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.5 2001/05/04 16:14:51 jhermann Exp $
"""

# Imports
import os, string
from MoinMoin import util

# Globals
languages = {
    'en': ('English',    '"Jürgen Hermann" <jh@web.de>'),
    'de': ('Deutsch',    '"Jürgen Hermann" <jh@web.de>'),
    'sv': ('Svenska',    '"Christian Sunesson" <noss@rm-f.net>'),
    'fr': ('Français',   '"Lucas Bruand" <Lucas.Bruand@ecl2002.ec-lyon.fr>'),
    'nl': ('Nederlands', '"Shae Erisson" <shae@webwitches.com>'),
    'fi': ('Suomi',      '"Shae Erisson" <shae@webwitches.com>'),
}


def _smartrepr(str):
    """Create multi-line string repr if necessary"""
    rep = repr(str)
    if string.count(rep, r'\012'):
        rep = rep[0] * 2 + string.replace(rep, r'\012', '\n') + rep[0] * 2

    return rep


def loadLanguage(lang):
    """Load text dictionary for a specific language"""
    return util.importName("MoinMoin.i18n." + lang, "text")


def saveLanguage(lang, textdict):
    """Save a changed text dictionary for a specific language"""
    filename = os.path.join(os.path.dirname(__file__), lang + '.py')
    file = open(filename, 'wt')
    file.write("# Text translations for %s (%s) maintained by %s\n" % (
        lang, languages[lang][0], languages[lang][1]))
    file.write("text = {\n")
    keys = textdict.keys()
    keys.sort()
    for key in keys:
        file.write("%s:\n%s,\n\n" % (_smartrepr(key), _smartrepr(textdict[key])))
    file.write("}\n")
    file.close()


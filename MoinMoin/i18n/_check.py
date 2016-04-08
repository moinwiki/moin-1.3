"""
    MoinMoin - List untranslated texts

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: _check.py,v 1.4 2001/12/14 18:42:19 jhermann Exp $
"""

# Imports
import getopt, sys
from MoinMoin import i18n
from MoinMoin.scripts import _util

def main():
    # check arguments
    optlist, args = getopt.getopt(sys.argv[1:],
        's',
        ['summary'])

    #print optlist, args
    summary = _util.haveOptions(optlist, ["-s", "--summary"])

    # delete english from list of languages that need to be checked
    languages = i18n.languages
    for lang in ['en']:
        del languages[lang]

    # check command line args
    if len(args) >= 1:
        if not languages.has_key(args[0]):
            print "*** Unsupported language", args[0]
            sys.exit(1)
        languages = {args[0]: languages[args[0]]}

    totalcount = len(i18n.loadLanguage("de"))
    print "The following texts out of %d total appear untranslated..." % totalcount

    # check all languages
    for lang in languages.keys():
        langset = i18n.loadLanguage(lang)

        count = 0
        if not summary: print
        print languages[lang][0] + "...", 
        if not summary: print

        keys = langset.keys()
        keys.sort()
        for text in keys:
            if text == langset[text]:
                count = count + 1
                if not summary:
                    print "    " + repr(text)

        if summary: print "\t%4d %3d%%" % (count, 100.0 * count / totalcount)

if __name__ == "__main__":
    main()


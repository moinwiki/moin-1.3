"""
    MoinMoin - List untranslated texts

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: _check.py,v 1.3 2001/04/04 22:06:56 jhermann Exp $
"""

# Imports
import sys
from MoinMoin import i18n

def main():
    # delete english from list of languages that need to be checked
    languages = i18n.languages
    for lang in ['en']:
        del languages[lang]

    # check command line args
    if len(sys.argv) > 1:
        if not languages.has_key(sys.argv[1]):
            print "*** Unsupported language", sys.argv[1]
            sys.exit(1)
        languages = {sys.argv[1]: languages[sys.argv[1]]}

    print "The following texts out of %d total appear untranslated..." % (
        len(i18n.loadLanguage("de")),)

    # check all languages
    for lang in languages.keys():
        langset = i18n.loadLanguage(lang)

        print
        print languages[lang][0] + "..."

        keys = langset.keys()
        keys.sort()
        for text in keys:
            if text == langset[text]:
                print "    " + repr(text)


if __name__ == "__main__":
    main()


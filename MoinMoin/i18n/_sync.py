# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Synchronize new texts into slaves from the master set

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: _sync.py,v 1.10 2003/11/09 21:00:58 thomaswaldmann Exp $
"""

# Imports
import getopt, sys
from MoinMoin import i18n


def haveOptions(optlist, options):
    """ Check whether one of the options in "options" is in the list of
        options ("optlist") created from the command line
    """
    return filter(lambda flag, o=options: flag[0] in o, optlist) != []


def synchronize(slave, master):
    """ Synchronize new texts from master to slave.

        Return number of changes made.
    """
    changes = 0

    # transfer all new keys to slave
    for key in master.keys():
        if not slave.has_key(key):
            changes = changes + 1
            slave[key] = key

    return changes


def main():
    # check arguments
    try:
        optlist, args = getopt.getopt(sys.argv[1:],
            'f',
            ['force'])
    except getopt.error, e:
        print "ERROR:", e
        print
        print "usage: sync [-f/--force] [<language(s)>]"
        sys.exit(1)

    #print optlist, args
    force = haveOptions(optlist, ["-f", "--force"])

    # delete english and master set from list of languages that need to be synch'ed
    if args:
        languages = {}
        for lang in args:
            if i18n.languages.has_key(lang):
                languages[lang] = i18n.languages[lang]
            else:
                print "ERROR: Unknown language %r" % lang
                sys.exit(1)
    else:
        languages = i18n.languages
    for lang in ['en', i18n.master_language]:
        if languages.has_key(lang):
            del languages[lang]

    # load the master set
    masterset = i18n.loadLanguage(i18n.master_language)

    # synch all languages
    for lang in languages.keys():
        langset = i18n.loadLanguage(lang)
        if langset is None: langset = {}

        changes = synchronize(langset, masterset)
        if changes or force:
            if 1 or languages[lang][i18n.ENCODING] in i18n.western_charsets:
                print "Adding %d new texts to '%s.py'..." % (changes, lang)
                i18n.saveLanguage(lang, langset)
            else:
                print "Skipping '%s.py' due to encoding '%s'..." % (lang, languages[lang][i18n.ENCODING])


if __name__ == "__main__":
    main()


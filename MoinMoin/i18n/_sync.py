"""
    MoinMoin - Synchronize new texts into slaves from the master set

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: _sync.py,v 1.6 2001/12/01 15:36:10 jhermann Exp $
"""

# Imports
import getopt, sys
from MoinMoin import i18n
from MoinMoin.scripts import _util


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
    optlist, args = getopt.getopt(sys.argv[1:],
        'f',
        ['force'])

    #print optlist, args
    force = _util.haveOptions(optlist, ["-f", "--force"])

    # delete english and master set from list of languages that need to be synch'ed
    languages = i18n.languages
    for lang in ['en', i18n.master_language]:
        del languages[lang]

    # load the master set
    masterset = i18n.loadLanguage(i18n.master_language)

    # synch all languages
    for lang in languages.keys():
        langset = i18n.loadLanguage(lang)
        if langset is None: langset = {}

        changes = synchronize(langset, masterset)
        if changes or force:
            if 1 or languages[lang][1] in i18n.western_charsets:
                print "Adding %d new texts to '%s.py'..." % (changes, lang)
                i18n.saveLanguage(lang, langset)
            else:
                print "Skipping '%s.py' due to encoding '%s'..." % (lang, languages[lang][1])


if __name__ == "__main__":
    main()


"""
    MoinMoin - Synchronize new texts into slaves from the master set

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: _sync.py,v 1.3 2001/05/31 01:02:08 jhermann Exp $
"""

# Imports
from MoinMoin import i18n

# Config
master = 'de'


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
    # delete english and master set from list of languages that need to be synch'ed
    languages = i18n.languages
    for lang in ['en', master]:
        del languages[lang]

    # load the master set
    masterset = i18n.loadLanguage(master)

    # synch all languages
    for lang in languages.keys():
        langset = i18n.loadLanguage(lang)
        if langset is None: langset = {}

        changes = synchronize(langset, masterset)
        if changes:
            print "Adding %d new texts to '%s.py'..." % (changes, lang)
            i18n.saveLanguage(lang, langset)


if __name__ == "__main__":
    main()


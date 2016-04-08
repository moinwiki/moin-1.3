"""  
    MoinMoin - Spelling Action
     
    Copyright (c) 2001 by Richard Jones <richard@bizarsoftware.com.au>  
    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>  
    All rights reserved, see COPYING for details.  

    Word adding based on code by Christian Bird <chris.bird@lineo.com> 

    This action checks for spelling errors in a page using one or several
    word lists.

    MoinMoin looks for dictionary files in the directory "dict" within the
    MoinMoin package directory. To load the default UNIX word files, you
    have to manually create symbolic links to those files (usually
    '/usr/dict/words' or '/usr/share/dict/words').

    Additionally, all words on the page "LocalSpellingWords" are added to
    the list of valid words, if that page exists.

    $Id: SpellCheck.py,v 1.18 2002/02/13 21:13:52 jhermann Exp $  
"""

# Imports
import cgi, os, re, string, sys
from MoinMoin import config, user, util, wikiutil
from MoinMoin.Page import Page
from MoinMoin.cgimain import request
from MoinMoin.i18n import _


# Functions
def _getWordsFiles():
    """Check a list of possible word files"""
    candidates = []

    # load a list of possible word files
    localdict = os.path.join(config.moinmoin_dir, 'dict')
    if os.path.isdir(localdict):
        candidates.extend(map(
            lambda f, d=localdict: os.path.join(d, f), os.listdir(localdict)))

    # validate candidate list (leave out directories!)
    wordsfiles = []
    for file in candidates:
        if os.path.isfile(file) and os.access(file, os.F_OK | os.R_OK):
            wordsfiles.append(file)

    # return validated file list
    return wordsfiles


def _loadWordsFile(dict, filename):
    request.clock.start('spellread')
    file = open(filename, 'rt')
    try:
        while 1:
            lines = file.readlines(32768)
            if not lines: break
            for line in lines:
                words = string.split(line)
                for word in words: dict[word] = ''
    finally:
        file.close()
    request.clock.stop('spellread')


def _loadDict():
    """ Load words from words files or cached dict """
    # check for "dbhash" module
    try:
        import dbhash
    except ImportError:
        dbhash = None

    # load the words
    cachename = os.path.join(config.data_dir, 'dict.cache')
    if dbhash and os.path.exists(cachename):
        wordsdict = dbhash.open(cachename, "r")
    else:
        request.clock.start('dict.cache')
        wordsfiles = _getWordsFiles()
        if dbhash:
            wordsdict = dbhash.open(cachename, 'n', 0666 & config.umask)
        else:
            wordsdict = {}

        for wordsfile in wordsfiles:
            _loadWordsFile(wordsdict, wordsfile)

        if dbhash: wordsdict.sync()
        request.clock.stop('dict.cache')

    return wordsdict


def _addLocalWords(form):
    # get the page contents
    lsw_page = Page(config.page_local_spelling_words)
    words = lsw_page.get_raw_body()

    # get the new words as a string
    from types import *
    newwords = form['newwords']
    if type(newwords) is not ListType:
        newwords = [newwords]
    newwords = string.join(map(lambda w: w.value, newwords), ' ')

    # add the words to the page and save it
    if words and words[-1] != '\n':
        words = words + '\n'
    lsw_page.save_text(words + '\n' + newwords, '0')


def checkSpelling(page, form, own_form=1):
    """ Do spell checking, return a tuple with the result.
    """
    # first check to see if we we're called with a "newwords" parameter
    if form.has_key('button_newwords'): _addLocalWords(form)

    # load words
    wordsdict = _loadDict()

    localwords = {}
    lsw_page = Page(config.page_local_spelling_words)
    if lsw_page.exists(): _loadWordsFile(localwords, lsw_page._text_filename())

    # init status vars & load page
    request.clock.start('spellcheck')
    badwords = {}
    text = page.get_raw_body()

    # checker regex and matching substitute function
    word_re = re.compile(r'(^|\W)([%s]?[%s]+)(?=(\W|$))' % (
        config.upperletters, config.lowerletters))

    def checkword(match, wordsdict=wordsdict, badwords=badwords,
            localwords=localwords, num_re=re.compile(r'^\d+$')):
        word = match.group(2)
        if len(word) == 1:
            return ""
        if not (wordsdict.has_key(word) or
                wordsdict.has_key(string.lower(word)) or
                localwords.has_key(word) or
                localwords.has_key(string.lower(word)) ):
            if not num_re.match(word):
                badwords[word] = 1
        return ""

    # do the checking
    for line in string.split(text, '\n'):
        if line == '' or line[0] == '#': continue
        word_re.sub(checkword, line)

    if badwords:
        badwords = badwords.keys()
        badwords.sort()

        # for Python 1.5, leave out the lookbehind check (includes the
        # letter or whitespace before the word in the highlight, which
        # makes it a bit uglier)
        badwords_re = r'(^|(?<!\w))(%s)(?!\w)'
        if sys.version < "2":
            badwords_re = r'(^|\W)(%s)(?!\w)'
        badwords_re = badwords_re % (string.join(map(re.escape, badwords), "|"),)
        badwords_re = re.compile(badwords_re)

        lsw_msg = ''
        if localwords:
            lsw_msg = _(' (including %(localwords)d %(pagelink)s)') % {
                'localwords': len(localwords), 'pagelink': lsw_page.link_to()}
        msg = "<b>" + _('The following %(badwords)d words could not be found in the dictionary of %(totalwords)d words%(localwords)s and are highlighted below:') % {
            'badwords': len(badwords),
            'totalwords': len(wordsdict)+len(localwords),
            'localwords': lsw_msg} + "</b><br>"

        # figure out what this action is called
        action_name = os.path.splitext(os.path.basename(__file__))[0]

        # add a form containing the bad words
        if own_form:
            msg = msg + (
                '<form method="POST" action="%s">'
                '<input type="hidden" name="action" value="%s">'
                % (wikiutil.quoteWikiname(page.page_name), action_name,))
        checkbox = '<input type="checkbox" name="newwords" value="%(word)s">%(word)s&nbsp;&nbsp;'
        msg = msg + (
            string.join(map(lambda w, cb=checkbox: cb % {'word': cgi.escape(w),}, badwords)) +
            '<p><input type="submit" name="button_newwords" value="%s">' %
                _('Add checked words to dictionary')
        )
        if own_form:
            msg = msg + '</form>'
    else:
        badwords_re = None
        msg = _("<b>No spelling errors found!</b>")

    request.clock.stop('spellcheck')

    return badwords, badwords_re, msg


def execute(pagename, form):
    page = Page(pagename)
    badwords, badwords_re, msg = checkSpelling(page, form)

    if badwords:
        page.send_page(form, msg=msg, hilite_re=badwords_re)
    else:
        page.send_page(form, msg=msg)


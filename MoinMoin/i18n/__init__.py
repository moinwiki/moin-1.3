"""
    MoinMoin - Internationalization

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This subpackage controls the access to the language modules
    contained in it. Each language is in a module with a dictionary
    storing the original texts as keys and their translation in the
    values. Other supporting modules start with an underscore.

    $Id: __init__.py,v 1.21 2002/03/07 11:17:23 jhermann Exp $
"""

# Imports
import os, string
from MoinMoin import config

# Globals
western_charsets = ['usascii', 'iso-8859-1']
master_language = 'de'

# "pt" is really "pt-br", so if someone wants to adapt that to "pt", you're welcome
languages = {
    'de': ('Deutsch',    'iso-8859-1',  '"Jürgen Hermann" <jh@web.de>'),
    'en': ('English',    'iso-8859-1',  '"Jürgen Hermann" <jh@web.de>'),
    'fi': ('Suomi',      'iso-8859-1',  '***vacant***'),
    'fr': ('Français',   'iso-8859-1',  '"Lucas Bruand" <Lucas.Bruand@ecl2002.ec-lyon.fr>'),
    'it': ('Italian',    'iso-8859-1',  'Lele Gaifax <lele@seldati.it>'),
    'ja': ('Japanese',   'euc-jp',      '"Jyunji Kondo" <j-kondo@pst.fujitsu.com>'),
    'ko': ('Korean',     'euc-kr',      '"Hye-Shik Chang" <perky@fallin.lv>'),
    'nl': ('Nederlands', 'iso-8859-1',  '***vacant***'),
    'pt': ('Português',  'iso-8859-1',  'Jorge Godoy <godoy@conectiva.com>'),
    'sv': ('Svenska',    'iso-8859-1',  '"Christian Sunesson" <noss@rm-f.net>'),
    'zh': ('Chinese',    'gb2312',      '"Changzhe Han" <hancz@brovic.com>'),
}

_text_lang = None
_text_cache = None


def _smartrepr(str):
    """Create multi-line string repr if necessary"""
    # check what quote to use
    quote = "'"
    if string.count(str, quote):
        quote = '"'

    # we don't need fast, so do it char by char
    def charrepr(ch, quote=quote):
        if ord(ch) < 32:
            ch = repr(ch)[1:-1]
        elif ch == quote or ch == "\\":
            ch = "\\" + ch
        return ch

    rep = quote + string.join(map(charrepr, str), '') + quote

    # make multiline if it contains line breaks
    if string.count(rep, r'\012'):
        rep = rep[0] * 2 + string.replace(rep, r'\012', '\n') + rep[0] * 2
    elif string.count(rep, r'\n'):
        rep = rep[0] * 2 + string.replace(rep, r'\n', '\n') + rep[0] * 2

    return rep


def adaptCharset(lang):
    # possibly adapt to different charset
    if languages.has_key(lang) and \
            config.charset in western_charsets and \
            languages[lang][1] not in western_charsets:
        config.html_head = string.replace(config.html_head,
            ";charset=%s" % config.charset,
            ";charset=%s" % languages[lang][1])
        config.charset = languages[lang][1]


def loadLanguage(lang):
    """Load text dictionary for a specific language"""
    from MoinMoin import util
    texts = util.importName("MoinMoin.i18n." + lang, "text") 

    return texts


def saveLanguage(lang, textdict):
    """Save a changed text dictionary for a specific language"""
    filename = os.path.join(os.path.dirname(__file__), lang + '.py')
    file = open(filename, 'wt')
    file.write("# Text translations for %s (%s)\n"
               "# Maintained by: %s\n"
               "# Encoding: %s\n" % (
        lang, languages[lang][0], languages[lang][2], languages[lang][1]))
    file.write("text = {\n")
    keys = textdict.keys()
    keys.sort()
    for key in keys:
        file.write("%s:\n%s,\n\n" % (_smartrepr(key), _smartrepr(textdict[key])))
    file.write("}\n")
    file.close()


def getLang():
    """Get a user's language (from CGI environment)"""
    global _text_lang
    if _text_lang: return _text_lang

    accepted = os.environ.get('HTTP_ACCEPT_LANGUAGE')
    if accepted:
        accepted = string.split(accepted, ',')
        accepted = map(lambda x: string.split(x, ';')[0], accepted)

        fallback = []
        for lang in accepted:
            fallback.append(lang)
            if string.count(lang, '-'):
                baselang = string.split(lang, '-')[0]
                fallback.append(baselang)
        accepted = fallback

        for lang in accepted:
            # do we have that language available?
            if languages.has_key(lang):
                # does the wiki's charset and that of the lang fit?
                # !!! note that it'd be nice if we could recode the
                # strings, but that requires Python 2.0, and some thought
                if languages[lang][1] == config.charset:
                    _text_lang = lang
                    break

    # make sure there is a language set
    if not _text_lang:
        _text_lang = 'en'

    return _text_lang


def getText(str):
    """Load a text in the user's language"""
    # quick handling for english texts
    lang = getLang()
    if lang == "en": return str

    # load texts if needed
    global _text_cache
    if not _text_cache:
        _text_cache = loadLanguage(lang)
        if not _text_cache:
            return str

    # check for text additions for the master language,
    # if configured (only active in development setups)
    if config.check_i18n and lang == master_language \
            and not _text_cache.has_key(str):
        _text_cache[str] = str
        saveLanguage(lang, _text_cache)

    # return the matching entry in the mapping table
    return _text_cache.get(str, str)


# define gettext-like "_" function 
_ = getText


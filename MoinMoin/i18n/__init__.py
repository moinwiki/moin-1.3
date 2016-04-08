# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Internationalization

    Copyright (c) 2001, 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This subpackage controls the access to the language modules
    contained in it. Each language is in a module with a dictionary
    storing the original texts as keys and their translation in the
    values. Other supporting modules start with an underscore.

    $Id: __init__.py,v 1.38 2003/11/09 21:00:57 thomaswaldmann Exp $
"""

# Imports
import os, string
from MoinMoin import config

# Globals
western_charsets = ['usascii', 'iso-8859-1']
master_language = 'de'

# "pt" is really "pt-br", so if someone wants to adapt that to "pt", you're welcome
NAME, ENCODING, DIRECTION, MAINTAINER = range(0,4)
languages = {
    'da': ('Dansk',      'iso-8859-1', 0, '"Jonas Smedegaard" <dr@jones.dk>'),
    'de': ('Deutsch',    'iso-8859-1', 0, '"J�rgen Hermann" <jh@web.de>'),
    'en': ('English',    'iso-8859-1', 0, '"J�rgen Hermann" <jh@web.de>'),
    'es': ('Spanish',    'iso-8859-1', 0, '"Jaime Robles" <jaime@robles.nu>'),
    'fi': ('Suomi',      'iso-8859-1', 0, '***vacant***'),
    'fr': ('Fran�ais',   'iso-8859-1', 0, '"Lucas Bruand" <Lucas.Bruand@ecl2002.ec-lyon.fr>'),
    'he': ('Hebrew',     'utf-8',      1, 'Nir Soffer <nirs@freeshell.org>'),
    'hr': ('Hrvatski',   'iso-8859-2', 0, 'Davor Cengija <dcengija@yahoo.com>'),
    'it': ('Italian',    'iso-8859-1', 0, 'Lele Gaifax <lele@seldati.it>'),
    'ja': ('Japanese',   'euc-jp',     0, '"Jyunji Kondo" <j-kondo@pst.fujitsu.com>'),
    'ko': ('Korean',     'utf-8',      0, '"Hye-Shik Chang" <perky@fallin.lv>'),
    'nl': ('Nederlands', 'iso-8859-1', 0, '"Bart Koppers" <bart@opencare.net>'),
    'pt': ('Portugu�s',  'iso-8859-1', 0, 'Jorge Godoy <godoy@conectiva.com>'),
    'sv': ('Svenska',    'iso-8859-1', 0, '"Christian Sunesson" <noss@rm-f.net>'),
    'zh': ('Chinese',    'gb2312',     0, '"Changzhe Han" <hancz@brovic.com>'),
    'zh-tw': ('Chinese/Taiwan', 'big5', 0, '"Chen Jian-ding" <dwight@ccns.ncku.edu.tw>'),
}

_text_lang = None

# This is a global for a reason, in persistent environments all languages
# in use will be cached; note you have to restart if you update language data
# in such environments.
_text_cache = {}


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
            languages[lang][ENCODING] not in western_charsets:
        config.html_head = string.replace(config.html_head,
            ";charset=%s" % config.charset,
            ";charset=%s" % languages[lang][ENCODING])
        config.charset = languages[lang][ENCODING]


def loadLanguage(lang):
    """Load text dictionary for a specific language"""
    from MoinMoin.util import pysupport
    texts = pysupport.importName("MoinMoin.i18n." + lang.replace('-', '_'), "text") 

    return texts


def saveLanguage(lang, textdict):
    """Save a changed text dictionary for a specific language"""
    filename = os.path.join(os.path.dirname(__file__), lang.replace('-', '_') + '.py')
    file = open(filename, 'wt')
    file.write("# Text translations for %s (%s)\n"
               "# Maintained by: %s\n"
               "# Encoding: %s\n"
               "# Direction: %s\n" % (
        lang, languages[lang][NAME], languages[lang][MAINTAINER],
        languages[lang][ENCODING], getDirection(None, lang),
    ))
    file.write("text = {\n")
    keys = textdict.keys()
    keys.sort()
    for key in keys:
        file.write("%s:\n%s,\n\n" % (_smartrepr(key), _smartrepr(textdict[key])))
    file.write("}\n")
    file.close()


def getLang():
    """Get a user's language (from preferences or CGI environment)"""
    from MoinMoin import user
    if user.current.language: return user.current.language

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
                if languages[lang][ENCODING] == config.charset:
                    _text_lang = lang
                    break

    # make sure there is a language set
    if not _text_lang:
        _text_lang = config.default_lang or 'en'

    return _text_lang


def getDirection(request, lang=None):
    """ Get text direction for a language, either 'ltr' or 'rtl'.
    """
    if not lang: lang = getLang()
    return ('ltr', 'rtl')[languages[lang][DIRECTION]]


def getText(str, lang=None, check_i18n=1):
    """Load a text in the user's language, or the given one"""
    if not lang: lang = getLang()

    # quick handling for english texts
    if lang == "en": return str

    # load texts if needed
    global _text_cache
    if not _text_cache.has_key(lang):
        texts = loadLanguage(lang)
        if not texts:
            # return english text in case of problems
            return str
        _text_cache[lang] = texts

    # check for text additions for the master language,
    # if configured (only active in development setups)
    if config.check_i18n and check_i18n and lang == master_language \
            and not _text_cache[lang].has_key(str):
        _text_cache[lang][str] = str
        try:
            saveLanguage(lang, _text_cache[lang])
        except IOError:
            # ignore write errors
            pass

    # get the matching entry in the mapping table
    result = _text_cache[lang].get(str, None)
    encoding = languages[lang][ENCODING]

    # untranslated string?
    if result is None:
        result = str
        encoding = 'ASCII'

    # is the translated text a unicode string?
    if isinstance(result, type(u'')):
        try:
            return result.encode(config.charset, 'replace')
        except (ValueError, UnicodeError):
            return str

    # is the translated text already in the main encoding?
    if encoding == config.charset:
        return result

    # else, try to recode into that encoding
    try:
        return unicode(result, encoding).encode(config.charset, 'replace')
    except (ValueError, UnicodeError):
        return str


# define gettext-like "_" function 
_ = getText


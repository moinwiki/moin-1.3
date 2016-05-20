"""
    site-wide configuration defaults (NOT per single wiki!)
"""

import re

# Threads flag - if you write a moin server that use threads, import
# config in the server and set this flag to True.
use_threads = False

# Charset - we support only 'utf-8'. While older encodings might work,
# we don't have the resources to test them, and there is no real
# benefit for the user.
# IMPORTANT: use only lowercase 'utf-8'!
charset = 'utf-8'
##charset = 'iso-8859-1'

# Invalid characters - invisible characters that should not be in page
# names. Prevent user confusion and wiki abuse, e.g u'\u202aFrontPage'.
page_invalid_chars_regex = re.compile(
    ur"""
    \u0000 | # NULL

    # Bidi control characters
    \u202A | # LRE
    \u202B | # RLE
    \u202C | # PDF
    \u202D | # LRM
    \u202E   # RLM
    """,
    re.UNICODE | re.VERBOSE
    )

# Other stuff
umask = 0770
allow_subpages = 1
url_schemas = []

smileys = {
    "X-(":  (15, 15, 0, "angry.png"),
    ":D":   (15, 15, 0, "biggrin.png"),
    "<:(":  (15, 15, 0, "frown.png"),
    ":o":   (15, 15, 0, "redface.png"),
    ":(":   (15, 15, 0, "sad.png"),
    ":)":   (15, 15, 0, "smile.png"),
    "B)":   (15, 15, 0, "smile2.png"),
    ":))":  (15, 15, 0, "smile3.png"),
    ";)":   (15, 15, 0, "smile4.png"),
    "/!\\": (15, 15, 0, "alert.png"),
    "<!>":  (15, 15, 0, "attention.png"),
    "(!)":  (15, 15, 0, "idea.png"),

    # copied 2001-11-16 from http://pikie.darktech.org/cgi/pikie.py?EmotIcon
    ":-?":  (15, 15, 0, "tongue.png"),
    ":\\":  (15, 15, 0, "ohwell.png"),
    ">:>":  (15, 15, 0, "devil.png"),
    "|)":   (15, 15, 0, "tired.png"),
    
    # some folks use noses in their emoticons
    ":-(":  (15, 15, 0, "sad.png"),
    ":-)":  (15, 15, 0, "smile.png"),
    "B-)":  (15, 15, 0, "smile2.png"),
    ":-))": (15, 15, 0, "smile3.png"),
    ";-)":  (15, 15, 0, "smile4.png"),
    "|-)":  (15, 15, 0, "tired.png"),
    
    # version 1.0
    "(./)":  (20, 15, 0, "checkmark.png"),
    "{OK}":  (14, 12, 0, "thumbs-up.png"),
    "{X}":   (16, 16, 0, "icon-error.png"),
    "{i}":   (16, 16, 0, "icon-info.png"),
    "{1}":   (15, 13, 0, "prio1.png"),
    "{2}":   (15, 13, 0, "prio2.png"),
    "{3}":   (15, 13, 0, "prio3.png"),

    # version 1.1 (flags)
    # flags for the languages in MoinMoin.i18n
    "{da}":  (18, 12, 1, "flag-da.png"),
    "{de}":  (18, 12, 1, "flag-de.png"),
    "{en}":  (24, 12, 0, "flag-en.png"),
    "{es}":  (18, 12, 0, "flag-es.png"),
    "{fi}":  (18, 12, 1, "flag-fi.png"),
    "{fr}":  (18, 12, 1, "flag-fr.png"),
    "{it}":  (18, 12, 1, "flag-it.png"),
    "{ja}":  (18, 12, 1, "flag-ja.png"),
    "{ko}":  (18, 12, 1, "flag-ko.png"),
    "{nl}":  (18, 12, 1, "flag-nl.png"),
    "{pt}":  (18, 12, 0, "flag-pt.png"),
    "{sv}":  (18, 12, 0, "flag-sv.png"),
    "{us}":  (20, 12, 0, "flag-us.png"),
    "{zh}":  (18, 12, 0, "flag-zh.png"),
}

# unicode: set the char types (upper, lower, digits, spaces)
from MoinMoin.util.chartypes import _chartypes
for key, val in _chartypes.items():
    if not vars().has_key(key):
        vars()[key] = val



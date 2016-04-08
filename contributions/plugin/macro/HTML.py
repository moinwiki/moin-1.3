"""
    HTML macro

    by Christian Bird <chris.bird@lineo.com>

    Outputs the html code contained within parens.

    [[HTML(<b>bold</b>)]]
    [[HTML(<font size=20>big</font>)]

    Please pay attention!
    =====================
    Making this macro available makes your wiki unsafe for its users,
    because anybody being able to use it, can add arbitrary html to
    a page, exploiting all sorts of bugs present in today's web browsers.

    So better NOT use this macro or at least not on publicly editable
    wikis.
"""

def execute(macro, args):
    return args or " "


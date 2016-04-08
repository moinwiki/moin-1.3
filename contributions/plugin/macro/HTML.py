"""
    HTML macro

    by Christian Bird <chris.bird@lineo.com>

    Outputs the html code contained within parens.

    [[HTML(<b>bold</b>)]]
    [[HTML(<font size=20>big</font>)]

"""

def execute(macro, args):
    return args or " "


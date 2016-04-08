"""
    MoinMoin - Include macro

    Copyright (c) 2000, 2001 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro includes the formatted content of the given page, following
    recursive includes if encountered. Cycles are detected!

    Usage:
        [[Include(pagename,heading,level)]]

        pagename    Name of the page to include
        heading     Text for the generated heading (optional)
        level       Level (1..5) of the generated heading (optional)

    Examples:
        [[Include(FooBar)]]  -- include the text of FooBar in the current paragraph.
        [[Include(FooBar, )]] -- add a H1 of 'Foo Bar' followed by the text
        [[Include(FooBar, , 2]] -- add a H2 of 'Foo Bar'
        [[Include(FooBar, 'All about Foo Bar', 2]] -- add a H2 of 'All about Foo Bar'

    $Id: Include.py,v 1.6 2002/02/13 21:13:53 jhermann Exp $
"""

import sys, string, re, cStringIO
from MoinMoin import user
from MoinMoin.Page import Page
from MoinMoin.i18n import _

_arg_heading = r'(?P<heading>,)\s*(|(?P<hquote>[\'"])(?P<htext>.+?)(?P=hquote))'
_arg_level = r',\s*(?P<level>\d+)'
_args_re_pattern = r'^(?P<name>[^,]+)(%s(%s)?)?$' % (_arg_heading, _arg_level)

def execute(macro, text, args_re=re.compile(_args_re_pattern)):
    ret = ''

    # parse and check arguments
    args = args_re.match(text)
    if not args:
        return ('<p><strong class="error">%s</strong></p>' % _('Invalid include arguments "%s"!')) % (text,)

    # get the page
    print_mode = macro.form.has_key('action') and macro.form['action'].value == "print"
    inc_name = args.group('name')
    this_page = macro.formatter.page
    if not hasattr(this_page, '_macroInclude_pagelist'):
        this_page._macroInclude_pagelist = {}
    if this_page._macroInclude_pagelist.has_key(inc_name):
        ret = ret + '<p><strong class="error">Recursive include of "%s" forbidden</strong></p>' % (inc_name,)
    inc_page = Page(inc_name, formatter=macro.formatter.__class__())
    inc_page._macroInclude_pagelist = this_page._macroInclude_pagelist

    # do headings
    level = None
    if args.group('heading'):
        heading = args.group('htext') or inc_page.split_title()
        level = 1
        if args.group('level'):
            level = int(args.group('level'))
        if print_mode:
            ret = ret + macro.formatter.heading(level, heading)
        else:
            ret = ret + inc_page.link_to(macro.formatter.heading(level, heading))

    # set or increment include marker
    this_page._macroInclude_pagelist[inc_name] = \
        this_page._macroInclude_pagelist.get(inc_name, 0) + 1

    # output the included page
    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    inc_page.send_page(macro.form, content_only=1)
    ret = ret + sys.stdout.getvalue()
    sys.stdout = stdout

    # decrement or remove include marker
    if this_page._macroInclude_pagelist[inc_name] > 1:
        this_page._macroInclude_pagelist[inc_name] = \
            this_page._macroInclude_pagelist[inc_name] - 1
    else:
        del this_page._macroInclude_pagelist[inc_name]

    # if no heading and not in print mode, then output a helper link
    if not (level or print_mode):
        ret = ret + inc_page.link_to(_('<small>[goto %s]</small>') % (inc_name,))

    # return include text
    return ret


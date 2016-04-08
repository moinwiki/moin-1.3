# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Include macro

    Copyright (c) 2000, 2001, 2002, 2003 by Jürgen Hermann <jh@web.de>
    Copyright (c) 2000, 2001 by Richard Jones <richard@bizarsoftware.com.au>
    All rights reserved, see COPYING for details.

    This macro includes the formatted content of the given page(s). See

        http://purl.net/wiki/moinmaster/HelpOnMacros/Include

    for detailed docs.
    
    $Id: Include.py,v 1.25 2003/11/09 21:01:02 thomaswaldmann Exp $
"""

import sys, re, cStringIO
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page

_sysmsg = '<p><strong class="%s">%s</strong></p>'
_arg_heading = r'(?P<heading>,)\s*(|(?P<hquote>[\'"])(?P<htext>.+?)(?P=hquote))'
_arg_level = r',\s*(?P<level>\d+)'
_arg_from = r'(,\s*from=(?P<fquote>[\'"])(?P<from>.+?)(?P=fquote))?'
_arg_to = r'(,\s*to=(?P<tquote>[\'"])(?P<to>.+?)(?P=tquote))?'
_arg_sort = r'(,\s*sort=(?P<sort>(ascending|descending)))?'
_arg_items = r'(,\s*items=(?P<items>\d+))?'
# CNC:2003-10-09
_arg_jumpitems = r'(,\s*jumpitems=(?P<jumpitems>\d+))?'
_arg_titlesonly = r'(,\s*(?P<titlesonly>titlesonly))?'
_args_re_pattern = r'^(?P<name>[^,]+)(%s(%s)?%s%s%s%s%s%s)?$' % (
    _arg_heading, _arg_level, _arg_from, _arg_to, _arg_sort, _arg_items,
    _arg_jumpitems, _arg_titlesonly)

# CNC:2003-10-09
TITLERE = re.compile("^(?P<heading>\s*(?P<hmarker>=+)\s.*\s(?P=hmarker))$", 
                     re.M)
def extract_titles(body):
    titles = []
    for title, _ in TITLERE.findall(body):
        h = title.strip()
        level = 1
        while h[level:level+1] == '=': level = level+1
        depth = min(5,level)
        title_text = h[level:-level].strip()
        titles.append((title_text, level))
    return titles

def execute(macro, text, args_re=re.compile(_args_re_pattern)):
    _ = macro.request.getText

    # return immediately if getting links for the current page
    if macro.request.mode_getpagelinks:
        return ''

    # parse and check arguments
    args = args_re.match(text)
    if not args:
        return (_sysmsg % ('error', _('Invalid include arguments "%s"!')) % (text,))

    # prepare including page
    result = []
    print_mode = macro.form.has_key('action') and macro.form['action'].value == "print"
    this_page = macro.formatter.page
    if not hasattr(this_page, '_macroInclude_pagelist'):
        this_page._macroInclude_pagelist = {}

    # get list of pages to include
    inc_name = wikiutil.AbsPageName(macro.request, this_page.page_name, args.group('name'))
    pagelist = [inc_name]
    if inc_name.startswith("^"):
        try:
            inc_match = re.compile(inc_name)
        except re.error:
            pass # treat as plain page name
        else:
            pagelist = wikiutil.getPageList(config.text_dir)
            pagelist = filter(inc_match.match, pagelist)

    # sort and limit page list
    pagelist.sort()
    sort_dir = args.group('sort')
    if sort_dir == 'descending':
        pagelist.reverse()
    max_items = args.group('items')
    if max_items:
        pagelist = pagelist[:int(max_items)]

    # CNC:2003-10-09
    jumpitems = 0
    if args.group("jumpitems"):
        jumpitems = int(args.group("jumpitems"))
    titlesonly = args.group('titlesonly')

    # iterate over pages
    for inc_name in pagelist:
        # CNC:2003-05-30
        if not macro.request.user.may.read(inc_name):
            continue
        if this_page._macroInclude_pagelist.has_key(inc_name):
            result.append('<p><strong class="error">Recursive include of "%s" forbidden</strong></p>' % (inc_name,))
            continue
        # CNC:2003-05-30
        if jumpitems:
            jumpitems -= 1
            continue
        inc_page = Page(inc_name, formatter=macro.formatter.__class__(macro.request))
        inc_page._macroInclude_pagelist = this_page._macroInclude_pagelist

        # check for "from" and "to" arguments (allowing partial includes)
        body = inc_page.get_raw_body() + '\n'
        from_pos = 0
        to_pos = -1
        from_re = args.group('from')
        if from_re:
            try:
                from_match = re.compile(from_re, re.M).search(body)
            except re.error, e:
                ##result.append("*** fe=%s ***" % e)
                from_match = re.compile(re.escape(from_re), re.M).search(body)
            if from_match:
                from_pos = from_match.end()
            else:
                result.append(_sysmsg % ('warning', 'Include: ' + _('Nothing found for "%s"!')) % from_re)
        to_re = args.group('to')
        if to_re:
            try:
                to_match = re.compile(to_re, re.M).search(body, from_pos)
            except re.error:
                to_match = re.compile(re.escape(to_re), re.M).search(body, from_pos)
            if to_match:
                to_pos = to_match.start()
            else:
                result.append(_sysmsg % ('warning', 'Include: ' + _('Nothing found for "%s"!')) % to_re)

        # CNC:2003-10-09
        if titlesonly:
            newbody = []
            levelstack = []
            for title, level in extract_titles(body[from_pos:to_pos]):
                if levelstack:
                    if level > levelstack[-1]:
                        result.append(macro.formatter.bullet_list(1))
                        levelstack.append(level)
                    else:
                        while levelstack and level < levelstack[-1]:
                            result.append(macro.formatter.bullet_list(0))
                            levelstack.pop()
                        if not levelstack or level != levelstack[-1]:
                            result.append(macro.formatter.bullet_list(1))
                            levelstack.append(level)
                else:
                    result.append(macro.formatter.bullet_list(1))
                    levelstack.append(level)
                result.append(macro.formatter.listitem(1))
                result.append(inc_page.link_to(title))
                result.append(macro.formatter.listitem(0))
            while levelstack:
                result.append(macro.formatter.bullet_list(0))
                levelstack.pop()
            continue

        if from_pos or to_pos != -1:
            inc_page.set_raw_body(body[from_pos:to_pos])
        ##result.append("*** f=%s t=%s ***" % (from_re, to_re))
        ##result.append("*** f=%d t=%d ***" % (from_pos, to_pos))

        # edit icon
        edit_icon = inc_page.link_to(
            macro.formatter.image(border=0, hspace=2,
                src="%s/img/moin-edit.gif" % (config.url_prefix,)),
            css_class="include-edit-link",
            querystr={'action': 'edit', 'backto': this_page.page_name})

        # do headings
        level = None
        if args.group('htext'):
            heading = args.group('htext') or inc_page.split_title()
            level = 1
            if args.group('level'):
                level = int(args.group('level'))
            if print_mode:
                result.append(macro.formatter.heading(level, heading))
            else:
                result.append(macro.formatter.heading(level,
                    inc_page.link_to(heading, css_class="include-heading-link"),
                    icons=edit_icon.replace('<img ', '<img align="right" ')
                                   .replace('&amp;', '&')))

        # set or increment include marker
        this_page._macroInclude_pagelist[inc_name] = \
            this_page._macroInclude_pagelist.get(inc_name, 0) + 1

        # output the included page
        stdout = sys.stdout
        sys.stdout = cStringIO.StringIO()
        try:
            inc_page.send_page(macro.request, content_only=1)
            result.append(sys.stdout.getvalue())
        finally:
            sys.stdout = stdout

        # decrement or remove include marker
        if this_page._macroInclude_pagelist[inc_name] > 1:
            this_page._macroInclude_pagelist[inc_name] = \
                this_page._macroInclude_pagelist[inc_name] - 1
        else:
            del this_page._macroInclude_pagelist[inc_name]

        # if no heading and not in print mode, then output a helper link
        if not (level or print_mode):
            result.extend([
                '<div class="include-link">',
                inc_page.link_to('[%s]' % (inc_name,), css_class="include-page-link"),
                edit_icon,
                '</div>',
            ])

    # return include text
    return ''.join(result)

# vim:ts=4:sw=4:et

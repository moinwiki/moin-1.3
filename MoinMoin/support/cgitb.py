# -*- coding: iso-8859-1 -*-
#
# This module was written by Ka-Ping Yee, <ping@lfw.org>.
# 
# $Id: cgitb.py,v 1.9 2003/11/09 21:01:12 thomaswaldmann Exp $

# TODO: as soon as we require python 2.2, use a copy of the newer cgitb
# included there and update it with the local changes (see XXX).

__doc__ = """
Extended CGI traceback handler by Ka-Ping Yee, <ping@lfw.org>.
"""

import sys, os, types, string, keyword, linecache, tokenize, inspect, pydoc
from MoinMoin import version

def breaker():
    return ('<body bgcolor="#f0f0ff">' +
            '<font color="#f0f0ff" size="-5"> > </font> ' +
            '</table>' * 5)

def html(context=5):
    etype, evalue, etb = sys.exc_info()
    if type(etype) is types.ClassType:
        etype = etype.__name__

    # XXX stuff added locally:
    try:
        osinfo = " ".join(os.uname()) # only on UNIX
    except: # TODO: which error does this raise on Win/Mac?
        osinfo = "Platform: %s (%s)" % (sys.platform, os.name)
    versinfo = "<b>Please include this information in your bug reports!:</b><br>" + \
               "Python %s - %s<br>" % (sys.version, sys.executable) + \
               osinfo + '<br>' + \
               'MoinMoin Release %s [Revision %s]' % (version.release, version.revision)
    head = pydoc.html.heading(
        '<font size=+1><strong>%s</strong>: %s</font>'%(str(etype), str(evalue)),
        '#ffffff', '#aa55cc', versinfo)
    # XXX end of local changes

    head = head + ('<p>A problem occurred while running a Python script. '
                   'Here is the sequence of function calls leading up to '
                   'the error, with the most recent (innermost) call first. '
                   'The exception attributes are:')

    indent = '<tt><small>%s</small>&nbsp;</tt>' % ('&nbsp;' * 5)
    traceback = []
    for frame, file, lnum, func, lines, index in inspect.getinnerframes(etb, context):
        if file is None:
            link = '&lt;file is None - probably inside <tt>eval</tt> or <tt>exec</tt>&gt;'
        else:
            file = os.path.abspath(file)
            link = '<a href="file:%s">%s</a>' % (file, pydoc.html.escape(file))
        args, varargs, varkw, locals = inspect.getargvalues(frame)
        if func == '?':
            call = ''
        else:
            call = 'in <strong>%s</strong>' % func + inspect.formatargvalues(
                    args, varargs, varkw, locals,
                    formatvalue=lambda value: '=' + pydoc.html.repr(value))

        level = '''
<table width="100%%" bgcolor="#d8bbff" cellspacing=0 cellpadding=2 border=0>
<tr><td>%s %s</td></tr></table>''' % (link, call)

        if file is None:
            traceback.append('<p>' + level)
            continue

        # do a fil inspection
        names = []
        def tokeneater(type, token, start, end, line, names=names):
            if type == tokenize.NAME and token not in keyword.kwlist:
                if token not in names:
                    names.append(token)
            if type == tokenize.NEWLINE: raise IndexError
        def linereader(file=file, lnum=[lnum]):
            line = linecache.getline(file, lnum[0])
            lnum[0] = lnum[0] + 1
            return line

        try:
            tokenize.tokenize(linereader, tokeneater)
        except IndexError: pass
        lvals = []
        for name in names:
            if name in frame.f_code.co_varnames:
                if locals.has_key(name):
                    value = pydoc.html.repr(locals[name])
                else:
                    value = '<em>undefined</em>'
                name = '<strong>%s</strong>' % name
            else:
                if frame.f_globals.has_key(name):
                    value = pydoc.html.repr(frame.f_globals[name])
                else:
                    value = '<em>undefined</em>'
                name = '<em>global</em> <strong>%s</strong>' % name
            lvals.append('%s&nbsp;= %s' % (name, value))
        if lvals:
            lvals = string.join(lvals, ', ')
            lvals = indent + '''
<small><font color="#909090">%s</font></small><br>''' % lvals
        else:
            lvals = ''

        excerpt = []
        i = lnum - index
        for line in lines:
            number = '&nbsp;' * (5-len(str(i))) + str(i)
            number = '<small><font color="#909090">%s</font></small>' % number
            line = '<tt>%s&nbsp;%s</tt>' % (number, pydoc.html.preformat(line))
            if i == lnum:
                line = '''
<table width="100%%" bgcolor="#ffccee" cellspacing=0 cellpadding=0 border=0>
<tr><td>%s</td></tr></table>''' % line
            excerpt.append('\n' + line)
            if i == lnum:
                excerpt.append(lvals)
            i = i + 1
        traceback.append('<p>' + level + string.join(excerpt, '\n'))

    traceback.reverse()

    exception = '<p><strong>%s</strong>: %s' % (str(etype), str(evalue))
    attribs = []
    if type(evalue) is types.InstanceType:
        for name in dir(evalue):
            value = pydoc.html.repr(getattr(evalue, name))
            attribs.append('<br>%s%s&nbsp;= %s' % (indent, name, value))

    return head + string.join(attribs) + string.join(traceback) + '<p>&nbsp;</p>'

def handler():
    print breaker()
    print html()


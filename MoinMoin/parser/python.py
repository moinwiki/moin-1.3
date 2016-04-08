"""
    MoinMoin - Python Source Parser

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: python.py,v 1.9 2002/03/04 19:12:57 jhermann Exp $
"""

# Imports
import cgi, string, sys, cStringIO
import keyword, token, tokenize


#############################################################################
### Python Source Parser (does Hilighting)
#############################################################################

_KEYWORD = token.NT_OFFSET + 1
_TEXT    = token.NT_OFFSET + 2

_colors = {
    token.NUMBER:       '#0080C0',
    token.OP:           '#0000C0',
    token.STRING:       '#004080',
    tokenize.COMMENT:   '#008000',
    token.NAME:         '#000000',
    token.ERRORTOKEN:   '#FF8080',
    _KEYWORD:           '#C00000',
    _TEXT:              '#000000',
}


class CountedOutput:
    """ Add line counts and possibly info texts to output
    """

    def __init__(self, out, lineinfo):
        self.out = out
        self.lineinfo = lineinfo
        self.line = 0
        self.infocounter = 0
        self.maxinfo = 0

        if lineinfo:
            import operator
            self.maxinfo = reduce(operator.add, map(len, lineinfo.values()), 0)

    def line_no(self):
        if self.lineinfo:
            for info in self.lineinfo.get(self.line, []):
                self.infocounter += 1
                self.out.write('<a name="info%d"></a>'
                    '<b><font color="%s">' % (self.infocounter, '#FF0000'))
                if self.infocounter == 1:
                    self.out.write('   ')
                else:
                    self.out.write('<a href="#info%d">&lt;&lt;</a> ' % (self.infocounter-1))
                if self.infocounter == self.maxinfo:
                    self.out.write('   ')
                else:
                    self.out.write('<a href="#info%d">&gt;&gt;</a> ' % (self.infocounter+1))
                self.out.write('#%d: %s</font></b>\n' % (self.infocounter, info))
        self.out.write('<font color="%s">%5d </font>' % (_colors[_TEXT], self.line))

    def write(self, data):
        if not self.line:
            self.line = 1
            self.line_no()

        parts = data.split('\n')
        if len(parts) > 1:
            self.out.write(parts[0])
            for part in parts[1:]:
                self.line += 1
                self.out.write('\n')
                self.line_no()
                self.out.write(part)
        else:
            self.out.write(data)


class Parser:
    """ Send colored python source.
    """

    def __init__(self, raw, lineinfo={}, **kw):
        """ Store the source text.
        """
        self.raw = string.rstrip(string.expandtabs(raw))
        self.rawout = kw.get('out', sys.stdout)
        self.out = CountedOutput(self.rawout, lineinfo)

    def format(self, formatter, form):
        """ Parse and send the colored source.
        """
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        while 1:
            pos = string.find(self.raw, '\n', pos) + 1
            if not pos: break
            self.lines.append(pos)
        self.lines.append(len(self.raw))

        # parse the source and write it
        self.pos = 0
        text = cStringIO.StringIO(self.raw)
        self.rawout.write('<pre><font face="Lucida,Courier New">')
        try:
            tokenize.tokenize(text.readline, self)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            self.rawout.write("<h3>ERROR: %s</h3>%s\n" % (
                msg, self.raw[self.lines[line]:]))
        self.rawout.write('</font></pre>')

    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        """ Token handler.
        """
        if 0: print "type", toktype, token.tok_name[toktype], "text", toktext, \
                    "start", srow,scol, "end", erow,ecol, "<br>"

        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.out.write('\n')
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            self.out.write(self.raw[oldpos:newpos])

        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return

        # map token type to a color group
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        color = _colors.get(toktype, _colors[_TEXT])

        style = ''
        if toktype == token.ERRORTOKEN:
            style = ' style="border: solid 1.5pt #FF0000;"'

        # send text
        self.out.write('<font color="%s"%s>' % (color, style))
        self.out.write(cgi.escape(toktext))
        self.out.write('</font>')


if __name__ == "__main__":
    import os, sys
    print "Formatting..."

    # open own source
    source = open('python.py').read()

    # write colorized version to "python.html"
    Parser(source, out = open('python.html', 'wt')).format(None, None)

    # load HTML page into browser
    if os.name == "nt":
        os.system("explorer python.html")
    else:
        os.system("netscape python.html &")


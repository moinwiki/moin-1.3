#! /usr/bin/env python

"""
    MoinMoin - Main CGI Module

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: moin.cgi,v 1.13 2000/07/28 23:03:28 jhermann Exp $
"""
__version__ = '$Revision: 1.13 $'[11:-2];

# Imports
import cgi, sys, string, os, re, errno, time, stat, socket
from cgi import log
from os import path, environ
from socket import gethostbyaddr
from time import localtime, strftime
from cStringIO import StringIO

startclock = time.clock()
sys.stderr = open('/tmp/moinmoin.log', 'at')

def emit_header():
    print "Content-type: text/html"
    print


# Regular expression defining a WikiWord (but this definition
# is also assumed in other places.
word_re_str = r"\b([A-Z][a-z]+){2,}\b"
word_anchored_re = re.compile('^' + word_re_str + '$')
command_re_str = "(search|edit|fullsearch|titlesearch)\=(.*)"

# Editlog -----------------------------------------------------------

# Functions to keep track of when people have changed pages, so we can
# do the recent changes page and so on.
# The editlog is stored with one record per line, as tab-separated
# words: page_name, host, time

# TODO: Check values written in are reasonable

def editlog_add(page_name, host):
    editlog = open(editlog_name, 'a+')
    try: 
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_EX)
        editlog.seek(0, 2)                  # to end
        editlog.write(string.join((page_name, host, `time.time()`), "\t") + "\n")
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


def editlog_raw_lines():
    editlog = open(editlog_name, 'rt')
    try:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_SH)
        return editlog.readlines()
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


    


# Formatting stuff --------------------------------------------------


def get_scriptname():
    return environ.get('SCRIPT_NAME', '')


def send_title(text, link=None, msg=None):
    print "<head><title>%s</title>" % text
    if css_url:
        print '<link rel="stylesheet" type="text/css" href="%s">' % css_url
    print "</head>"
    print '<body><table><tr><td>'
    if logo_string:
        print link_tag(front_page, logo_string)
    print '</td><td valign="middle" class="headline"><font size="+3">&nbsp;<b>'
    if link:
        print '<a href="%s">%s</a>' % (link, text)
    else:
        print text
    print '</b></font></td></tr></table>'
    if navi_bar:
        print navi_bar % {'scriptname': get_scriptname()}
    if msg: print "<br>", msg
    print '<hr>'



def link_tag(params, text=None, ss_class=None):
    if text is None:
        text = params                   # default
    if ss_class:
        classattr = 'class="%s" ' % ss_class
    else:
        classattr = ''
    return '<a %s href="%s/%s">%s</a>' % (classattr, get_scriptname(),
                                         params, text)


# Search ---------------------------------------------------

def do_fullsearch(needle):
    send_title('Full text search for "%s"' % (needle))

    needle_re = re.compile(needle, re.IGNORECASE)
    hits = []
    all_pages = page_list()
    for page_name in all_pages:
        body = Page(page_name).get_raw_body()
        count = len(needle_re.findall(body))
        if count:
            hits.append((count, page_name))

    # The default comparison for tuples compares elements in order,
    # so this sorts by number of hits
    hits.sort()
    hits.reverse()

    print "<UL>"
    for (count, page_name) in hits:
        print '<LI>' + Page(page_name).link_to()
        print ' . . . . ' + `count`
        print ['match', 'matches'][count <> 1]
    print "</UL>"

    print_search_stats(len(hits), len(all_pages))


def do_titlesearch(needle):
    # TODO: check needle is legal -- but probably we can just accept any
    # RE

    send_title("Title search for \"" + needle + '"')
    
    needle_re = re.compile(needle, re.IGNORECASE)
    all_pages = page_list()
    hits = filter(needle_re.search, all_pages)

    print "<UL>"
    for filename in hits:
        print '<LI>' + Page(filename).link_to()
    print "</UL>"

    print_search_stats(len(hits), len(all_pages))


def print_search_stats(hits, searched):
    print "<p>%d hits " % hits
    print " out of %d pages searched." % searched


# Edit -----------------------------------------------------

def do_edit(pagename):
    Page(pagename).send_editor()


def do_savepage(pagename):
    global form
    pg = Page(pagename)
    pg.save_text(form['savetext'].value)
    msg = """<b>Thank you for your changes.  Your attention to
    detail is appreciated.</b>"""
    
    pg.send_page(msg=msg)


def make_index_key():
    s = '<p><center>'
    links = map(lambda ch: '<a href="#%s">%s</a>' % (ch, ch),
                string.uppercase)
    s = s + string.join(links, ' | ')
    s = s + '</center><p>'
    return s


def page_list():
    return filter(word_anchored_re.match, os.listdir(text_dir))


def print_footer(name, editable=1, mod_string=None):
    base = get_scriptname()
    print "<hr>"
    print '<a href="http://www.python.org/"><img align="right" vspace="10" src="%s/PythonPowered.gif" width="55" height="22" border="0" alt="PythonPowered"></a>' % (url_prefix,)

    if editable:
        print link_tag('?edit='+name, 'EditText')
        print "of this page"
        if mod_string:
            print "(last modified %s)" % mod_string
        print '<br>'
    print link_tag('FindPage?value='+name, 'FindPage')
    print " by browsing, searching, or an index"
    print '<!-- %s served this page in %.3f secs -->' % (socket.gethostname(), time.clock() - startclock)
    print '</body></html>'


# ----------------------------------------------------------
# Macros
def _macro_TitleSearch():
    return _macro_search("titlesearch")

def _macro_FullSearch():
    return _macro_search("fullsearch")

def _macro_search(type):
    if form.has_key('value'):
        default = form["value"].value
    else:
        default = ''
    return """<form method=get>
    <input name=%s size=30 value="%s"> 
    <input type=submit value="Go">
    </form>""" % (type, default)

def _macro_GoTo():
    return """<form method=get><input name=goto size=30>
    <input type=submit value="Go">
    </form>"""
    # isindex is deprecated, but it gives the right result here

def _macro_WordIndex():
    s = make_index_key()
    pages = list(page_list())
    map = {}
    word_re = re.compile('[A-Z][a-z]+')
    for name in pages:
        for word in word_re.findall(name):
            try:
                map[word].append(name)
            except KeyError:
                map[word] = [name]

    all_words = map.keys()
    all_words.sort()
    last_letter = None
    for word in all_words:
        letter = string.upper(word[0])
        if letter <> last_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            last_letter = letter
            
        s = s + '<b>%s</b><ul>' % word
        links = map[word]
        links.sort()
        last_page = None
        for name in links:
            if name == last_page: continue
            s = s + '<li>' + Page(name).link_to()
        s = s + '</ul>'
    return s


def _macro_TitleIndex():
    s = make_index_key()
    pages = list(page_list())
    pages.sort()
    current_letter = None
    for name in pages:
        letter = string.upper(name[0])
        if letter <> current_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            current_letter = letter
        else:
            s = s + '<br>'
        s = s + Page(name).link_to()
    return s


def _macro_RecentChanges():
    lines = editlog_raw_lines()
    lines.reverse()
    
    ratchet_day = None
    done_words = {}
    buf = StringIO()
    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    for line in lines:
        page_name, addr, ed_time = string.split(line, '\t')
        # year, month, day, DoW
        time_tuple = localtime(float(ed_time))
        day = tuple(time_tuple[0:3])
        if day <> ratchet_day:
            buf.write('<tr><td colspan=%d><br/><font size="+1"><b>%s</b></font></td></tr>\n'
                % (2+show_hosts, strftime(date_fmt, time_tuple)))
            ratchet_day = day

        if done_words.has_key(page_name):
            continue

        done_words[page_name] = 1
        buf.write('<tr><td>%s</td><td>&nbsp;' % (Page(page_name).link_to(),))
        if show_hosts:
            try:
                buf.write(gethostbyaddr(addr)[0])
            except:
                buf.write(addr)
            buf.write("</td><td>&nbsp;")
        if changed_time_fmt:
            buf.write(time.strftime(changed_time_fmt, time_tuple))
        buf.write('</td></tr>\n')
    buf.write('</table>')

    return buf.getvalue()



# ----------------------------------------------------------
class PageFormatter:
    """Object that turns Wiki markup into HTML.

    All formatting commands can be parsed one line at a time, though
    some state is carried over between lines.
    """
    def __init__(self, raw):
        self.raw = raw
        self.is_em = self.is_b = 0
        self.list_indents = []
        self.in_pre = 0


    def _emph_repl(self, word):
        if len(word) == 3:
            self.is_b = not self.is_b
            return ['</b>', '<b>'][self.is_b]
        else:
            self.is_em = not self.is_em
            return ['</em>', '<em>'][self.is_em]

    def _rule_repl(self, word):
        s = self._undent()
        if len(word) <= 4:
            s = s + "\n<hr>\n"
        else:
            s = s + "\n<hr size=%d>\n" % (len(word) - 2 )
        return s

    def _word_repl(self, word):
        return Page(word).link_to()


    def _url_repl(self, word):
        return '<a href="%s">%s</a>' % (word, word)


    def _email_repl(self, word):
        return '<a href="mailto:%s">%s</a>' % (word, word)


    def _ent_repl(self, s):
        return {'&': '&amp;',
                '<': '&lt;',
                '>': '&gt;'}[s]
    

    def _li_repl(self, match):
        if self.in_pre:
            return match
        else:
            return '<li>'


    def _pre_repl(self, word):
        if word == '{{{' and not self.in_pre:
            self.in_pre = 1
            return '<pre>'
        elif self.in_pre:
            self.in_pre = 0
            return '</pre>'
        else:
            return ''

    def _macro_repl(self, word):
        macro_name = word[2:-2]
        # TODO: Somehow get the default value into the search field
        return apply(globals()['_macro_' + macro_name], ())


    def _indent_level(self):
        return len(self.list_indents) and self.list_indents[-1]

    def _indent_to(self, new_level):
        s = ''
        while self._indent_level() > new_level:
            del(self.list_indents[-1])
            s = s + '</ul>\n'
        while self._indent_level() < new_level:
            self.list_indents.append(new_level)
            s = s + '<ul>\n'
        return s

    def _undent(self):
        res = '</ul>' * len(self.list_indents)
        self.list_indents = []
        return res


    def replace(self, match):
        for type, hit in match.groupdict().items():
            if hit:
                return apply(getattr(self, '_' + type + '_repl'), (hit,))
        else:
            raise "Can't handle match " + `match`
        

    def print_html(self):
        # For each line, we scan through looking for magic
        # strings, outputting verbatim any intervening text
        scan_re = re.compile(
            r"(?:(?P<emph>'{2,3})"
            + r"|(?P<ent>[<>&])"
            + r"|(?P<word>\b(?:[A-Z][a-z]+){2,}\b)"
            + r"|(?P<rule>-{4,})"
            + r"|(?P<url>(http|ftp|nntp|news|mailto)\:[^\s'\"]+\S)"
            + r"|(?P<email>[-\w._+]+\@[\w.-]+)"
            + r"|(?P<li>^\s+\*)"
            + r"|(?P<pre>(\{\{\{|\}\}\}))"
            + r"|(?P<macro>\[\[(TitleSearch|FullSearch|WordIndex"
                            + r"|TitleIndex|RecentChanges|GoTo)\]\])"
            + r")")
        blank_re = re.compile("^\s*$")
        bullet_re = re.compile("^\s+\*")
        indent_re = re.compile("^\s*")
        eol_re = re.compile(r'\r?\n')
        raw = string.expandtabs(self.raw)
        for line in eol_re.split(raw):
            if not self.in_pre:
                # XXX: Should we check these conditions in this order?
                if blank_re.match(line):
                    print '<p>'
                    continue
                indent = indent_re.match(line)
                print self._indent_to(len(indent.group(0)))
            print re.sub(scan_re, self.replace, line)
        if self.in_pre: print '</pre>'
        print self._undent()
        

# ----------------------------------------------------------
class Page:
    def __init__(self, page_name):
        self.page_name = page_name

    def split_title(self):
        # look for the end of words and the start of a new word,
        # and insert a space there
        return re.sub('([a-z])([A-Z])', r'\1 \2', self.page_name)


    def _text_filename(self):
        return path.join(text_dir, self.page_name)


    def _tmp_filename(self):
        return path.join(text_dir, ('#' + self.page_name + '.' + `os.getpid()` + '#'))


    def exists(self):
        try:
            os.stat(self._text_filename())
            return 1
        except OSError, er:
            if er.errno == errno.ENOENT:
                return 0
            else:
                raise er
        

    def link_to(self):
        word = self.page_name
        if self.exists():
            return link_tag(word)
        else:
            if nonexist_qm:
                return link_tag(word, '?', 'nonexistent') + word
            else:
                return link_tag(word, word, 'nonexistent')


    def get_raw_body(self):
        try:
            return open(self._text_filename(), 'rt').read()
        except IOError, er:
            if er.errno == errno.ENOENT:
                # just doesn't exist, use default
                return 'Describe %s here.' % self.page_name
            else:
                raise er
    

    def send_page(self, msg=None):
        link = get_scriptname() + '?fullsearch=' + self.page_name
        send_title(self.split_title(), link, msg)
        PageFormatter(self.get_raw_body()).print_html()
        print_footer(self.page_name, 1, self._last_modified())


    def _last_modified(self):
        if not self.exists():
            return None
        modtime = localtime(os.stat(self._text_filename())[stat.ST_MTIME])
        return strftime(datetime_fmt, modtime)


    def send_editor(self):
        send_title('Edit ' + self.split_title())
        print '<form method="post" action="%s">' % (get_scriptname())
        print '<input type=hidden name="savepage" value="%s">' % (self.page_name)
        raw_body = string.replace(self.get_raw_body(), '\r\n', '\n')
        print """<textarea wrap="virtual" name="savetext" rows="%d"
                 cols="80">%s</textarea>""" % (edit_rows, raw_body)
        print """<br><input type=submit value="Save">
                 <input type=reset value="Reset">
                 """
        print "<br>"
        print Page("UploadFile").link_to()
        print "<input type=file name=imagefile>"
        print "(not enabled yet)"
        print "</form>"
        print "<p>" + Page('EditingTips').link_to()
                 

    def _write_file(self, text):
        tmp_filename = self._tmp_filename()
        open(tmp_filename, 'wt').write(text)
        text = self._text_filename()
        if os.name == 'nt':
            # Bad Bill!  POSIX rename ought to replace. :-(
            try:
                os.remove(text)
            except OSError, er:
                if er.errno <> errno.ENOENT: raise er
        os.chmod(tmp_filename, 0666)
        os.rename(tmp_filename, text)


    def save_text(self, newtext):
        self._write_file(string.replace(newtext, "\r", ""))
        remote_name = environ.get('REMOTE_ADDR', '')
        editlog_add(self.page_name, remote_name)
        

emit_header()

# Load configuration
from moin_config import *

text_dir = path.join(data_dir, 'text')
editlog_name = path.join(data_dir, 'editlog')
cgi.logfile = path.join(data_dir, 'cgi_log')

try:
    form = cgi.FieldStorage()

    handlers = { 'fullsearch':  do_fullsearch,
                 'titlesearch': do_titlesearch,
                 'edit':        do_edit,
                 'savepage':    do_savepage }

    for cmd in handlers.keys():
        if form.has_key(cmd):
            apply(handlers[cmd], (form[cmd].value,))
            break
    else:
        path_info = environ.get('PATH_INFO', '')

        if form.has_key('goto'):
            query = form['goto'].value
        elif len(path_info) and path_info[0] == '/':
            query = path_info[1:] or front_page
        else:       
            query = environ.get('QUERY_STRING', '') or front_page

        word_match = re.match(word_re_str, query)
        if word_match:
            word = word_match.group(0)
            Page(word).send_page()
        else:
            print "<p>Can't work out query \"<pre>" + query + "</pre>\""

except:
    cgi.print_exception()

sys.stdout.flush()

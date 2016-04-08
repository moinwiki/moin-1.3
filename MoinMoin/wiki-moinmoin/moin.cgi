#! /usr/bin/env python

"""
    MoinMoin - Main CGI Module

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: moin.cgi,v 1.52 2000/08/26 23:16:45 jhermann Exp $
"""
__version__ = '$Revision: 1.52 $'[11:-2]


#############################################################################
### Prolog
#############################################################################

# Timing stuff
import time
class Clock:
    def __init__(self):
        self.timings = {'total': time.clock()}

    def start(self, timer):
        self.timings[timer] = time.clock()
    
    def stop(self, timer):
        self.timings[timer] = time.clock() - self.timings[timer]

    def value(self, timer):
        return "%.3f" % (self.timings[timer],)

    def dump(self, file):
        for timing in self.timings.items():
            file.write("%s = %.3f\n" % timing)

clock = Clock()

# Imports
clock.start('imports')
import cgi, sys, string, os, re, errno, socket, urllib
from os import path, environ
from socket import gethostbyaddr
clock.stop('imports')

# Load configuration
clock.start('config')
from moin_config import *
clock.stop('config')

# define directories
data_dir = path.normpath(data_dir)
text_dir = path.join(data_dir, 'text')
backup_dir = path.join(data_dir, 'backup')
editlog_name = path.join(data_dir, 'editlog')
cgi.logfile = path.join(data_dir, 'cgi_log')

# create log file for catching stderr output
sys.stderr = open(path.join(data_dir, 'err_log'), 'at')

# other globals
interwiki = None


#############################################################################
### Misc utilities
#############################################################################

# Quoting stuff, works reliable only for WikiNames
def quote_filename(filename):
    return string.replace(urllib.quote(filename), '%', '_')

def unquote_filename(filename):
    return urllib.unquote(string.replace(filename, '_', '%'))

# interwiki support
def resolve_wiki(wikiurl):
    """ return tuple of wikitag, wikiurl, wikitail """
    # load map (once)
    global interwiki
    if interwiki is None:
        interwiki = {}
        for line in open(path.join(data_dir, "intermap.txt"), "rt").readlines():
            try:
                wikitag, urlprefix, trash = string.split(
                    line + " " + get_scriptname() + "/InterWiki", None, 2)
                interwiki[wikitag] = urlprefix
            except:
                pass
        ##import pprint; print '<pre>'; pprint.pprint(interwiki); print '</pre>'
        
    # split wiki url (!!! use a regex here!)
    try:
        wikitag, tail = string.split(wikiurl, "/", 1)
    except:
        try:
            wikitag, tail = string.split(wikiurl, ":", 1)
        except:
            wikitag = None

    # return resolved url
    if wikitag and interwiki.has_key(wikitag):
        return (wikitag, interwiki[wikitag], tail)
    else:
        return ("BadWikiTag", get_scriptname(), "/InterWiki")

# popen (use win32 version if available)
popen = os.popen
if os.name == "nt":
    try:
        import win32pipe
        popen = win32pipe.popen
    except:
        pass

# Regular expression defining a WikiWord (but this definition
# is also assumed in other places).
word_re_str = r"([%s][%s]+){2,}" % (upperletters, lowerletters)
word_anchored_re = re.compile('^' + word_re_str + '$')


#############################################################################
### Edit log
#############################################################################
#!!! refactor to PageEditor class

# Functions to keep track of when people have changed pages, so we can
# do the recent changes page and so on.
# The editlog is stored with one record per line, as tab-separated
# words: page_name, host, time, hostname

# TODO: Check values written in are reasonable

def editlog_add(page_name, host):
    try:
        hostname = gethostbyaddr(host)[0]
    except:
        hostname = host

    editlog = open(editlog_name, 'a+')
    try: 
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_EX)
        editlog.seek(0, 2)                  # to end
        editlog.write(string.join((page_name, host, `time.time()`, hostname), "\t") + "\n")
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


#############################################################################
### Formatting stuff
#############################################################################

def get_scriptname():
    return environ.get('SCRIPT_NAME', '')


def send_title(text, **keywords):
    """
        **text** -- title text
        **keywords** --
            **link**: URL for the title
            **msg**: additional message (after saving)
            pagename='PageName'
            print_mode=1 (or 0)
    """
    print "<head><title>%s</title>" % text
    if css_url:
        print '<link rel="stylesheet" type="text/css" href="%s">' % css_url
    print "</head>"
    print '<body>'
    sys.stdout.flush()

    if keywords.has_key('print_mode') and keywords['print_mode']:
        print '<h1>%s</h1><hr>\n' % (text,)
        return

    print '<table><tr><td>'

    if logo_string:
        print link_tag(urllib.quote_plus(front_page), logo_string)
    print '</td><td valign="middle" class="headline"><font size="+3">&nbsp;<b>'
    if keywords.get('link'):
        print '<a href="%s">%s</a>' % (keywords['link'], text)
    else:
        print text
    print '</b></font></td></tr></table>'
    if navi_bar:
        if page_icons and keywords.has_key('pagename'):
            print page_icons % {
                'scriptname': get_scriptname(),
                'url': url_prefix,
                'pagename': urllib.quote(keywords['pagename'])}
        print navi_bar % {'scriptname': get_scriptname()}
    if keywords.get('msg'):
        print "<br>", keywords['msg']
        print '<p><a href="?action=show">Clear message</a>'
    print '<hr>'



def link_tag(params, text=None, css_class=None):
    if text is None:
        text = params                   # default
    if css_class:
        classattr = 'class="%s" ' % css_class
    else:
        classattr = ''
    return ('<a %s href="%s/%s">%s</a>'
        % (classattr, get_scriptname(), params, text))


#############################################################################
### Search
#############################################################################

def do_fullsearch(pagename):
    if form.has_key('value'):
        needle = form["value"].value
    else:
        needle = ''

    send_title('Full text search for "%s"' % (needle,))

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


def do_titlesearch(pagename):
    # TODO: check needle is legal -- but probably we can just accept any RE

    if form.has_key('value'):
        needle = form["value"].value
    else:
        needle = ''

    send_title('Title search for "%s"' % (needle,))
    
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


#############################################################################
### Misc Helpers (!!!refactor this to cohesive units)
#############################################################################

def get_backup_list(pagename):
    """ Get a filename list of older versions of the page, sorted by date
        in descending order (last change first).
    """
    if path.isdir(backup_dir):
        backup_re = re.compile(r'^%s\.\d+\.\d+$' % (quote_filename(pagename),))
        oldversions = filter(backup_re.match, os.listdir(backup_dir))
        oldversions.sort()
        oldversions.reverse()
    else:
        oldversions = None

    return oldversions

def do_diff(pagename):
    """ Handle "action=diff", checking for a "date=backupdate" parameter """
    # send page title
    send_title('Diff for "%s"' % (pagename,), pagename=pagename)

    # get a list of old revisions, and back out if none are available
    try:
        oldpage = quote_filename(pagename) + "." + path.basename(form['date'].value)
    except:
        oldversions = get_backup_list(pagename)
        if not oldversions:
            print "<b>No older revisions available!</b>"
            print_footer(pagename, showpage=1)
            return
        oldpage = oldversions[0]

    # build the diff command and execute it
    cmd = "diff -u %(backup)s %(page)s" % {
        "page": path.join(text_dir, quote_filename(pagename)),
        "backup": path.join(backup_dir, oldpage)
    }
    diff = popen(cmd, "r")
    lines = diff.readlines()
    rc = diff.close()
    ##print "cmd =", cmd, "<br>"
    ##print "rc =", rc, "<br>"

    # check for valid diff
    if not lines:
        print "<b>No differences found!</b>"
        print_footer(pagename, showpage=1)
        return

    # Show date info
    print '<b>Differences between version dated',
    if lines[0][0:3] == "---":
        print string.split(lines[0], ' ', 2)[2],
        del lines[0]
    print 'and',
    if lines[0][0:3] == "+++":
        print string.split(lines[0], ' ', 2)[2],
        del lines[0]
    print '</b>'
    print '<div class="diffold">Deletions are marked like this.</div>'
    print '<div class="diffnew">Additions are marked like this.</div>'

    # Show diff
    for line in lines:
        marker = line[0]
        line = cgi.escape(line[1:])
        stripped = string.lstrip(line)
        if len(line) - len(stripped):
            line = "&nbsp;" * (len(line) - len(stripped)) + stripped

        if marker == "@":
            print '<hr style="color:#FF3333">'
        elif marker == "\\":
            if stripped == "No newline at end of file\n": continue
            print '<div><font size="1" face="Verdana">%s&nbsp;</font></div>' % (line,)
        elif marker == "+":
            print '<div class="diffnew">%s&nbsp;</div>' % (line,)
        elif marker == "-":
            print '<div class="diffold">%s&nbsp;</div>' % (line,)
        else:
            print '<div>%s</div>' % (line,)

    print_footer(pagename, showpage=1)


def do_info(pagename):
    from stat import *

    send_title('Info for "%s"' % (pagename,), pagename=pagename)

    revisions = [path.join(text_dir, quote_filename(pagename))]

    oldversions = get_backup_list(pagename)
    if oldversions:
        for file in oldversions:
            revisions.append(path.join(backup_dir, file))

    print '<h2>Revision History</h2>\n'
    print '<table border="1" cellpadding="2" cellspacing="0">\n'
    print '<tr><th>#</th><th>Date</th><th>Size</th><th>Action</th></tr>\n'
    count = 1
    for file in revisions:
        st = os.stat(file)
        actions = ""
        if count > 1:
            actions = '%s&nbsp;<a href="%s/%s?action=recall&date=%s">view</a>' % (
                actions,
                get_scriptname(),
                urllib.quote_plus(pagename),
                path.basename(file)[len(quote_filename(pagename))+1:])
            actions = '%s&nbsp;<a href="%s/%s?action=diff&date=%s">diff</a>' % (
                actions,
                get_scriptname(),
                urllib.quote_plus(pagename),
                path.basename(file)[len(quote_filename(pagename))+1:])
        print '<tr><td align="right">%d</td><td>&nbsp;%s</td><td align="right">&nbsp;%d</td><td>&nbsp;%s</td></tr>\n' % (
            count,
            time.strftime(datetime_fmt, time.localtime(st[ST_MTIME])),
            st[ST_SIZE],
            actions)
        count = count + 1
        if count > 100: break
    print '</table>\n'
    
    print_footer(pagename, showpage=1)


def do_recall(pagename):
    Page(pagename, date=form['date'].value).send_page()


def do_show(pagename):
    Page(pagename).send_page()


def do_raw(pagename):
    print "Content-type: text/plain"
    print

    sys.stdout.write(Page(pagename).get_raw_body())


def do_print(pagename):
    Page(pagename).send_page(None, 1)


def do_edit(pagename):
    Page(pagename).send_editor()


def do_savepage(pagename):
    global form
    pg = Page(pagename)
    savetext = ""
    datestamp = ""
    try:
        savetext = form['savetext'].value
        datestamp = form['datestamp'].value
    except:
        pass
    msg = pg.save_text(savetext, datestamp)
    pg.send_page(msg=msg)


def make_index_key(index_letters):
    index_letters.sort()
    s = '<p><center>'
    links = map(lambda ch: '<a href="#%s">%s</a>' % (ch, ch),
                index_letters)
    s = s + string.join(links, ' | ')
    s = s + '</center><p>'
    return s


def page_list():
    return filter(word_anchored_re.match, map(unquote_filename, os.listdir(text_dir)))


def print_footer(pagename, mod_string=None, **keywords):
    """ Print the page footer.

        **pagename** -- WikiName of the page
        **mod_string** -- "last modified" date
        **keywords**:
            **editable** -- true, when page is editable (default: true)
            **showpage** -- true, when link back to page is wanted (default: false)
    """
    base = get_scriptname()
    print "<hr>"
    print '<a href="http://www.python.org/"><img align="right" vspace="10" src="%s/PythonPowered.gif" width="55" height="22" border="0" alt="PythonPowered"></a>' % (url_prefix,)

    if keywords.get('showpage', 0):
        print link_tag(urllib.quote_plus(pagename), "ShowText")
        print 'of this page<br>'
    if keywords.get('editable', 1):
        print link_tag(urllib.quote_plus(pagename)+'?action=edit', 'EditText')
        print "of this page"
        if mod_string:
            print "(last modified %s)" % mod_string
        print '<br>'
    print link_tag('FindPage?value='+urllib.quote_plus(pagename), 'FindPage')
    print " by browsing, searching, or an index<br>"

    if show_version: print '<p><font size="1" face="Verdana">MoinMoin %s, Copyright © 2000 by Jürgen Hermann</font></p>' % (__version__,)


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

def _macro_TitleSearch():
    return _macro_search("titlesearch")

def _macro_FullSearch():
    return _macro_search("fullsearch")

def _macro_search(type):
    if form.has_key('value'):
        default = form["value"].value
    else:
        default = ''
    return """<form method="get">
    <input type="hidden" name="action" value="%s"> 
    <input name="value" size="30" value="%s"> 
    <input type="submit" value="Go">
    </form>""" % (type, default)

def _macro_GoTo():
    return """<form method="get"><input name="goto" size="30">
    <input type="submit" value="Go">
    </form>"""

def _macro_WordIndex():
    index_letters = []
    s = ''
    pages = list(page_list())
    map = {}
    word_re = re.compile('[%s][%s]+' % (upperletters, lowerletters))
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
        letter = word[0]
        if letter <> last_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            last_letter = letter
        if letter not in index_letters:
            index_letters.append(letter)
            
        s = s + '<b>%s</b><ul>' % word
        links = map[word]
        links.sort()
        last_page = None
        for name in links:
            if name == last_page: continue
            s = s + '<li>' + Page(name).link_to()
        s = s + '</ul>\n'
    return make_index_key(index_letters) + s


def _macro_TitleIndex():
    index_letters = []
    s = ''
    pages = list(page_list())
    pages.sort()
    current_letter = None
    for name in pages:
        letter = name[0]
        if letter not in index_letters:
            index_letters.append(letter)
        if letter <> current_letter:
            s = s + '<a name="%s"><h3>%s</h3></a>' % (letter, letter)
            current_letter = letter
        else:
            s = s + '<br>'
        s = s + Page(name).link_to() + '\n'
    return make_index_key(index_letters) + s


def _macro_RecentChanges():
    from cStringIO import StringIO

    lines = editlog_raw_lines()
    lines.reverse()

    tnow = time.time()
    daycount = 0
    ratchet_day = None
    done_words = {}
    buf = StringIO()
    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    for line in lines:
        try:
            page_name, addr, ed_time, hostname = string.split(line, '\t')
        except:
            page_name, addr, ed_time = string.split(line, '\t')
            hostname = addr

        if done_words.has_key(page_name):
            continue

        # year, month, day, DoW
        time_tuple = time.localtime(float(ed_time))
        day = tuple(time_tuple[0:3])
        if day <> ratchet_day:
            daycount = daycount + 1
            if daycount > 14: break

            buf.write('<tr><td colspan=%d><br/><font size="+1"><b>%s</b></font></td></tr>\n'
                % (2+show_hosts, time.strftime(date_fmt, time_tuple)))
            ratchet_day = day

        done_words[page_name] = 1
        buf.write('<tr><td>&nbsp;&nbsp;[%s]&nbsp;</td><td>%s</td><td>&nbsp;' % (
            link_tag(urllib.quote_plus(page_name) + "?action=diff", "diff"),
            Page(page_name).link_to(),))

        if changed_time_fmt:
            tdiff = int(tnow - float(ed_time)) / 60
            if tdiff < 1440:
                buf.write("[%dh&nbsp;%dm&nbsp;ago]" % (tdiff/60, tdiff%60))
            else:
                buf.write(time.strftime(changed_time_fmt, time_tuple))
            buf.write("&nbsp;</td><td>&nbsp;")

        if show_hosts:
            buf.write(hostname)

        buf.write('</td></tr>\n')

    buf.write('</table>')

    return buf.getvalue()


def _macro_InterWiki():
    from cStringIO import StringIO
    dummy = resolve_wiki('')

    buf = StringIO()
    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    list = interwiki.items()
    list.sort()
    for tag, url in list:
            buf.write('<tr><td><tt><a href="%sRecentChanges">%s</a>&nbsp;&nbsp;</tt></td>' % (url, tag))
            buf.write('<td><tt><a href="%s">%s</a></tt></td>' % (url, url))
            buf.write('</tr>\n')
    buf.write('</table>')

    return buf.getvalue()


#############################################################################
### PageFormatter - Handles WikiMarkup
#############################################################################

class PageFormatter:
    """
        Object that turns Wiki markup into HTML.

        All formatting commands can be parsed one line at a time, though
        some state is carried over between lines.

        Methods named like _*_repl() are responsible to handle the named regex
        patterns defined in print_html().
    """

    formatting_rules = r"""(?:(?P<emph_ibb>'''''(?=[^']+'''))
(?P<emph>'{2,3})
(?P<ent>[<>&])
(?P<interwiki>[A-Z][a-zA-Z]+\:[^\s'\"]+)
(?P<word>(?:[%(u)s][%(l)s]+){2,})
(?P<rule>-{4,})
(?P<url_bracket>\[(%(url)s)\:[^\s\]]+(\s[^\]]+)?\])
(?P<url>(%(url)s)\:[^\s'\"]+)
(?P<email>[-\w._+]+\@[\w.-]+)
(?P<li>^\s+\*)
(?P<ol>^\s+\d\.\s)
(?P<pre>(\{\{\{|\}\}\}))
(?P<macro>\[\[(TitleSearch|FullSearch|WordIndex|TitleIndex|RecentChanges|GoTo|InterWiki)\]\]))"""  % {
        'url': 'http|https|ftp|nntp|news|mailto|wiki',
        'u': upperletters,
        'l': lowerletters}

    def __init__(self, raw):
        self.raw = raw
        self.is_em = self.is_b = 0
        self.in_pre = 0

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []

        #members = vars(PageFormatter)
        #replmatch = re.compile("^_(.*)_repl")
        #replfuncs = map(lambda x: x.group(1),
        #    filter(None, map(replmatch.match, members.keys() )))
        #self.repl_dispatch = [{}, {}]
        #for f in replfuncs:
        #     self.repl_dispatch[0][f] = members['_'+f+'_repl']
        #     #self.repl_dispatch[1][f] = members['_pre_repl']


    def interwiki(self, url_and_text):
        if len(url_and_text) == 1:
            url = url_and_text[0]
            text = None
        else:
            url, text = url_and_text

        url = url[5:]
        if text is None:
            try: # !!! use a regex here, or even better make a split_interwiki()
                tag, tail = string.split(url, "/", 1)
                text = tail
            except:
                try:
                    tag, tail = string.split(url, ":", 1)
                    text = tail
                except:
                    text = url
                    url = ""

        wikitag, wikiurl, wikitail = resolve_wiki(url)

        return '<a href="%s"><img src="%s/img/moin-inter.gif" width="16" height="16" hspace="2" border="%d" alt="[%s]"></a><a href="%s%s">%s</a>' % (
            wikiurl, url_prefix, wikitag == "BadWikiTag", wikitag, wikiurl, wikitail, text)

    def _emph_repl(self, word):
        """Handle emphasis, i.e. '' and '''."""
        if len(word) == 3:
            self.is_b = not self.is_b
            return ['</b>', '<b>'][self.is_b]
        else:
            self.is_em = not self.is_em
            return ['</em>', '<em>'][self.is_em]

    def _emph_ibb_repl(self, word):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        return ['</em>', '<em>'][self.is_em] + ['</b>', '<b>'][self.is_b]

    def _rule_repl(self, word):
        """Handle sequences of dashes."""
        s = self._undent()
        if len(word) <= 4:
            s = s + "\n<hr>\n"
        else:
            s = s + "\n<hr size=%d>\n" % (len(word) - 2 )
        return s

    def _word_repl(self, word):
        """Handle WikiNames."""
        return Page(word).link_to()


    def _interwiki_repl(self, word):
        """Handle InterWiki links."""
        return self.interwiki(["wiki:" + word])


    def _url_repl(self, word):
        """Handle literal URLs including inline images."""
        if word[:5] == "wiki:": return self.interwiki([word])
        extpos = string.rfind(word, ".")
        if extpos > 0 and word[extpos:] in ['.gif', '.jpg', '.png']:
            return '<img src="%s" border="0">' % (word,)
        else:
            return '<a href="%s">%s</a>' % (word, word)


    def _url_bracket_repl(self, word):
        """Handle bracketed URLs."""
        words = string.split(word[1:-1], None, 1)
        if len(words) == 1: words = words * 2
        scheme = string.split(words[0], ":", 1)[0]

        if scheme == "wiki": return self.interwiki(words)

        icon = ("www", 11, 11)
        if scheme == "mailto": icon = ("email", 14, 10)
        if scheme == "news": icon = ("news", 10, 11)
        if scheme == "ftp": icon = ("ftp", 11, 11)
        #!!! use a map?
        # http|https|ftp|nntp|news|mailto|wiki

        return '<a class="external" href="%s"><img src="%s/img/moin-%s.gif" width="%d" height="%d" border="0" hspace="4" alt="[%s]">%s</a>' % (
            words[0], url_prefix, icon[0], icon[1], icon[2], string.upper(icon[0]), words[1])


    def _email_repl(self, word):
        """Handle email addresses (without a leading mailto:)."""
        return '<a href="mailto:%s">%s</a>' % (word, word)


    def _ent_repl(self, s):
        """Handle SGML entities."""
        return {'&': '&amp;',
                '<': '&lt;',
                '>': '&gt;'}[s]
    

    def _li_repl(self, match):
        """Handle bullet lists."""
        return '<li>'


    def _ol_repl(self, match):
        """Handle numbered lists."""
        return '<li>'


    def _pre_repl(self, word):
        """Handle code displays."""
        if word == '{{{' and not self.in_pre:
            self.in_pre = 1
            return '<pre class="code">'
        elif self.in_pre:
            self.in_pre = 0
            return '</pre>'
        else:
            return ''

    def _macro_repl(self, word):
        """Handle macros ([[macroname]])."""
        macro_name = word[2:-2]
        # TODO: Somehow get the default value into the search field
        return apply(globals()['_macro_' + macro_name], ())


    def _indent_level(self):
        """Return current char-wise indent level."""
        return len(self.list_indents) and self.list_indents[-1]

    def _indent_to(self, new_level, list_type):
        """Close and open lists."""
        str = ''

        # Close lists while char-wise indent is greater than the current one
        while self._indent_level() > new_level:
            str = '%s</%s>\n' % (str, self.list_types[-1])
            del(self.list_indents[-1])
            del(self.list_types[-1])

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)
            str = '%s<%s>\n' % (str, list_type)

        return str

    def _undent(self):
        """Close all open lists."""
        result = string.join(map(lambda t: '</%s>' % (t,), self.list_types), '\n')
        self.list_indents = []
        self.list_types = []
        return result


    def replace(self, match):
        #hit = filter(lambda g: g[1], match.groupdict().items())
        for type, hit in match.groupdict().items():
            if hit:
                if self.in_pre and type not in ['pre', 'ent']:
                    return hit
                else:
                    #return self.repl_dispatch[self.in_pre][type](self, hit)
                    return apply(getattr(self, '_' + type + '_repl'), (hit,))
        else:
            raise ("Can't handle match " + `match`
                + "\n" + repr(match.groupdict())
                + "\n" + repr(match.groups()) )
        

    def print_html(self):
        # For each line, we scan through looking for magic
        # strings, outputting verbatim any intervening text
        scan_re = re.compile(string.replace(PageFormatter.formatting_rules, '\n', '|'))
        number_re = re.compile("^\s+\d\.\s")
        indent_re = re.compile("^\s*")
        eol_re = re.compile(r'\r?\n')
        raw = string.expandtabs(self.raw)
        for line in eol_re.split(raw):
            if not self.in_pre:
                if not string.strip(line):
                    print '<p>'
                    continue
                indent = indent_re.match(line)
                indlen = len(indent.group(0))
                indtype = "ul"
                if indlen and number_re.match(line):
                    indtype = "ol"
                print self._indent_to(indlen, indtype)
            print re.sub(scan_re, self.replace, line)
        if self.in_pre: print '</pre>'
        print self._undent()
        

#############################################################################
### Page - Manage a page associated with a WikiName
#############################################################################
class Page:
    def __init__(self, page_name, **keywords):
        """ Load page object.

            **page_name** -- WikiName of the page
            **keywords** -- date: date of older revision
        """
        self.page_name = page_name
        self.prev_date = keywords.get('date')


    def split_title(self):
        # look for the end of words and the start of a new word,
        # and insert a space there
        return re.sub('([%s])([%s])' % (lowerletters, upperletters), r'\1 \2', self.page_name)


    def _text_filename(self):
        if self.prev_date:
            return path.join(backup_dir, quote_filename(self.page_name) + "." + self.prev_date)
        else:
            return path.join(text_dir, quote_filename(self.page_name))


    def _tmp_filename(self):
        return path.join(text_dir, ('#' + quote_filename(self.page_name) + '.' + `os.getpid()` + '#'))


    def exists(self):
        return path.exists(self._text_filename())


    def link_to(self):
        word = self.page_name
        if self.exists():
            return link_tag(urllib.quote_plus(word), word)
        else:
            if nonexist_qm:
                return link_tag(urllib.quote_plus(word), '?', 'nonexistent') + word
            else:
                return link_tag(urllib.quote_plus(word), word, 'nonexistent')


    def get_raw_body(self):
        try:
            return open(self._text_filename(), 'rt').read()
        except IOError, er:
            if er.errno == errno.ENOENT:
                # just doesn't exist, use default
                return 'Describe %s here.' % self.page_name
            else:
                raise er
    

    def send_page(self, msg=None, print_mode=0):
        clock.start('send_page')
        link = '%s/%s?action=fullsearch&value=%s' % (
            get_scriptname(),
            urllib.quote_plus(self.page_name),
            urllib.quote_plus(self.page_name))
        title = self.split_title()
        if self.prev_date:
            if msg is None: msg = ""
            msg = "<b>Version as of %s</b><br>%s" % (time.strftime(datetime_fmt, time.localtime(float(self.prev_date))), msg)
        send_title(title, link=link, msg=msg, pagename=self.page_name, print_mode=print_mode)
        PageFormatter(self.get_raw_body()).print_html()
        if not print_mode: print_footer(self.page_name, self._last_modified())
        clock.stop('send_page')


    def _last_modified(self):
        if not self.exists():
            return None
        modtime = time.localtime(path.getmtime(self._text_filename()))
        return time.strftime(datetime_fmt, modtime)


    def send_editor(self):
        if self.prev_date:
            print '<b>Cannot edit old revisions</b>'
            return

        # send header stuff
        send_title('Edit ' + self.split_title(), pagename=self.page_name)
        print '<a href="%s?action=edit&rows=10&cols=60">Reduce editor size</a>' % (self.page_name,)
        print "|", Page('EditingTips').link_to()

        # send form
        global form
        try:
            text_rows = int(form['rows'].value)
        except:
            text_rows = edit_rows
        try:
            text_cols = int(form['cols'].value)
        except:
            text_cols = 80

        print '<form method="post" action="%s/%s">' % (get_scriptname(), urllib.quote_plus(self.page_name))
        print '<input type="hidden" name="action" value="savepage">' 
        if path.isfile(self._text_filename()):
            mtime = path.getmtime(self._text_filename())
        else:
            mtime = 0
        print '<input type="hidden" name="datestamp" value="%d">' % (mtime,)
        raw_body = string.replace(self.get_raw_body(), '\r\n', '\n')
        print ('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, raw_body))
        print '<div style="margin-top:6pt;"><input type="submit" value="Save Changes">'
        ##<input type=reset value="Reset">"""
        print "<br>"
        ##print Page("UploadFile").link_to()
        ##print "<input type=file name=imagefile>"
        ##print "(not enabled yet)"
        print "</div></form>"

    def _write_file(self, text):
        # save to tmpfile
        tmp_filename = self._tmp_filename()
        open(tmp_filename, 'wt').write(text)
        text = self._text_filename()

        if path.isdir(backup_dir) and path.isfile(text):
            os.rename(text, path.join(backup_dir, quote_filename(self.page_name) + '.' + `time.time()`))
        else:
            if os.name == 'nt':
                # Bad Bill!  POSIX rename ought to replace. :-(
                try:
                    os.remove(text)
                except OSError, er:
                    if er.errno <> errno.ENOENT: raise er

        # replace old page by tmpfile
        os.chmod(tmp_filename, 0666)
        os.rename(tmp_filename, text)


    def save_text(self, newtext, datestamp):
        msg = ""
        if not newtext:
            msg = """<b>You cannot save empty pages.</b>"""
        elif datestamp == '0':
            pass
        elif datestamp != str(os.path.getmtime(self._text_filename())):
            msg = """<b>Sorry, someone else saved the page while you edited it.
<p>Please do the following: Use the back button of your browser, and cut&paste
your changes from there. Then go forward to here, and click EditText again.
Now re-add your changes to the current page contents.
<p><em>Do not just replace
the content editbox with your version of the page, because that would
delete the changes of the other person, which is excessively rude!</em></b>
"""

        if not msg:
            msg = """<b>Thank you for your changes.
Your attention to detail is appreciated.</b>"""

            self._write_file(string.replace(newtext, "\r", ""))
            remote_name = environ.get('REMOTE_ADDR', '')
            editlog_add(self.page_name, remote_name)

        return msg        


#############################################################################
### Main code
#############################################################################

# parse request data
try:
    form = cgi.FieldStorage()
    path_info = environ.get('PATH_INFO', '')

    action = None
    if form.has_key('action'):
        action = form['action'].value

    pagename = None
    if len(path_info) and path_info[0] == '/':
        pagename = path_info[1:] or front_page
except:
    print "Content-type: text/html"
    print
    cgi.print_exception()
    sys.exit(0)

# dispatch actions with special http headers
if action == 'raw':
    do_raw(pagename)
    sys.exit(0)

# send http headers
print "Content-type: text/html"
#print "Pragma: no-cache"
#print "Cache-control: no-cache"
#!!! Better set expiry to some 10 mins or so for normal pages?
print

try:
    # handle request
    handlers = { 'fullsearch':  do_fullsearch,
                 'titlesearch': do_titlesearch,
                 'edit':        do_edit,
                 'diff':        do_diff,
                 'info':        do_info,
                 'recall':      do_recall,
                 'show':        do_show,
                 'print':       do_print,
                 'savepage':    do_savepage }

    if action:
        if pagename:
            if handlers.has_key(action):
                apply(handlers[action], (pagename,))
            else:
                print "<p>Unknown action"
        else:
            print "<p>No pagename given"
    else:
        if form.has_key('goto'):
            query = form['goto'].value
        elif pagename:
            query = pagename
        else:       
            query = environ.get('QUERY_STRING', '') or front_page

        word_match = re.match(word_re_str, query)
        if word_match:
            word = word_match.group(0)
            Page(word).send_page()
        else:
            print "<p>Can't work out query \"<pre>" + query + "</pre>\""

    # generate page footer
    clock.stop('total')

    if show_timings:
        print '<pre><font size="1" face="Verdana">',
        clock.dump(sys.stdout)
        print '</font></pre>'

    print '<!-- MoinMoin %s on %s served this page in %s secs -->' % (
        __version__, socket.gethostname(), clock.value('total'))
    print '</body></html>'

except:
    cgi.print_exception()

sys.stdout.flush()

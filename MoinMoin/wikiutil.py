"""
    MoinMoin - Wiki Utility Functions

    Copyright (c) 2000-2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikiutil.py,v 1.27 2001/03/30 21:06:52 jhermann Exp $
"""

# Imports
import os, re, string, sys, urllib
from MoinMoin import config, user, version, webapi


#############################################################################
### Smileys
#############################################################################

smileys = {
    "X-(":  (15, 15, "angry.gif"),
    ":D":   (15, 15, "biggrin.gif"),
    "<:(":  (15, 15, "frown.gif"),
    ":o":   (15, 15, "redface.gif"),
    ":(":   (15, 15, "sad.gif"),
    ":)":   (15, 15, "smile.gif"),
    "B)":   (15, 15, "smile2.gif"),
    ":))":  (15, 15, "smile3.gif"),
    ";)":   (15, 15, "smile4.gif"),
    "/!\\": (15, 15, "alert.gif"),
    "<!>":  (15, 15, "attention.gif"),
    "(!)":  (15, 15, "idea.gif")
}


def getSmiley(text):
    w, h, img = smileys[text]
    return '<img hspace="6" width="%d" height="%d" src="%s/img/%s">' % (
        w, h, config.url_prefix, img)


#############################################################################
### Quoting
#############################################################################

def quoteFilename(filename):
    safe = string.letters + string.digits
    res = list(filename)
    for i in range(len(res)):
        c = res[i]
        if c not in safe:
            res[i] = '_%02x' % ord(c)
    return string.joinfields(res, '')


def unquoteFilename(filename):
    return urllib.unquote(string.replace(filename, '_', '%'))


quoteWikiname = quoteFilename
unquoteWikiname = unquoteFilename


#############################################################################
### InterWiki
#############################################################################

_interwiki_list = None

def split_wiki(wikiurl):
    """ return tuple of wikitag, wikitail"""
    # !!! use a regex here!
    try:
        wikitag, tail = string.split(wikiurl, ":", 1)
    except ValueError:
        try:
            wikitag, tail = string.split(wikiurl, "/", 1)
        except ValueError:
            wikitag = None
            tail = None

    return (wikitag, tail)

def resolve_wiki(wikiurl):
    """ return tuple of wikitag, wikiurl, wikitail """
    # load map (once)
    global _interwiki_list
    if _interwiki_list is None:
        _interwiki_list = {}
        for line in open(os.path.join(config.data_dir, "intermap.txt"), "rt").readlines():
            try:
                wikitag, urlprefix, trash = string.split(
                    line + " " + webapi.getScriptname() + "/InterWiki", None, 2)
                _interwiki_list[wikitag] = urlprefix
            except ValueError:
                pass
        ##import pprint; print '<pre>'; pprint.pprint(_interwiki_list); print '</pre>'
        
    # split wiki url
    wikitag, tail = split_wiki(wikiurl)

    # return resolved url
    if wikitag and _interwiki_list.has_key(wikitag):
        return (wikitag, _interwiki_list[wikitag], urllib.quote(tail))
    else:
        return ("BadWikiTag", webapi.getScriptname(), "/InterWiki")


#############################################################################
### Page storage helpers
#############################################################################

def getPageList(text_dir):
    """ List all pages, except for "CVS" directories,
        hidden files (leading '.') and temp files (leading '#')
    """
    pages = os.listdir(text_dir)
    result = []
    for file in pages:
        if file[0] in ['.', '#'] or file in ['CVS']: continue
        result.append(file)
    return map(unquoteFilename, result)


def getPageDict(text_dir):
    """ Return a dictionary of page objects for all pages,
        with the page name as the key.
    """
    from MoinMoin.Page import Page
    pages = {}
    pagenames = getPageList(text_dir)
    for name in pagenames:
        pages[name] = Page(name)
    return pages    


def getBackupList(backup_dir, pagename=None):
    """ Get a filename list of older versions of the page, sorted by date
        in descending order (last change first).

        If pagename = None, all backup versions are returned.
    """
    if os.path.isdir(backup_dir):
        if pagename:
            pagename = quoteFilename(pagename)
        else:
            pagename = ".*?"
        backup_re = re.compile(r'^%s\.\d+(\.\d+)?$' % (pagename,))
        oldversions = filter(backup_re.match, os.listdir(backup_dir))
        oldversions.sort()
        oldversions.reverse()
    else:
        oldversions = None

    return oldversions


#############################################################################
### Searching
#############################################################################

def searchPages(needle, **kw):
    """ Search the text of all pages for "needle", and return a tuple of
        (number of pages, hits).

        literal = 0: try to treat "needle" as a regex, case-insensitive
        literal = 1: "needle" is definitely NOT a regex and searched case-sensitive
    """
    from MoinMoin.Page import Page

    try:
        needle_re = re.compile(needle, re.IGNORECASE)
    except re.error:
        needle_re = re.compile(re.escape(needle), re.IGNORECASE)

    hits = []
    literal = kw.get('literal', 0)
    all_pages = getPageList(config.text_dir)
    for page_name in all_pages:
        body = Page(page_name).get_raw_body()
        if literal:
            count = string.count(body, needle)
        else:
            count = len(needle_re.findall(body))
        if count:
            hits.append((count, page_name))

    # The default comparison for tuples compares elements in order,
    # so this sorts by number of hits
    hits.sort()
    hits.reverse()

    return (len(all_pages), hits)


#############################################################################
### Misc
#############################################################################

def isUnicodeName(name):
    """Try to determine if the quoted wikiname is a special, pure unicode name"""
    # escape name if not escaped
    text = name
    if not string.count(name, '_'):
        text = quoteWikiname(name)

    # check if every character is escaped
    return len(string.replace(text,'_','')) == len(text) * 2/3


def isPicture(url):
    """Check for picture URLs"""
    extpos = string.rfind(url, ".")
    return extpos > 0 and string.lower(url[extpos:]) in ['.gif', '.jpg', '.jpeg', '.png']


def link_tag(params, text=None, css_class=None):
    if text is None:
        text = params                   # default
    if css_class:
        classattr = ' class="%s"' % css_class
    else:
        classattr = ''
    return ('<a%s href="%s/%s">%s</a>'
        % (classattr, webapi.getScriptname(), params, text))


def send_title(text, **keywords):
    """
        **text** -- title text
        **keywords** --
            **link**: URL for the title
            **msg**: additional message (after saving)
            pagename='PageName'
            print_mode=1 (or 0)
    """
    # print the HTML <HEAD> element and start the <BODY>
    user_head = config.html_head
    if os.environ.get('QUERY_STRING', '') or os.environ.get('REQUEST_METHOD', '') == 'POST':
        user_head = user_head + config.html_head_queries
    print "<head>%s<title>%s</title>" % (user_head, text)
    css_url = user.current.valid and user.current.css_url or config.css_url
    if css_url and string.lower(css_url) != "none":
        print '<link rel="stylesheet" type="text/css" href="%s">' % (css_url,)
    print "</head>"
    print '<body>'
    sys.stdout.flush()

    # if in print mode, emit the title and return immediately
    if keywords.has_key('print_mode') and keywords['print_mode']:
        print '<h1>%s</h1><hr>\n' % (text,)
        return

    # print the page header (logo, title)
    print '<table width="100%"><tr><td>'

    if config.logo_string:
        print link_tag(quoteWikiname(config.front_page), config.logo_string)
    print '</td><td width="99%" valign="middle" class="headline"><font size="+3">&nbsp;<b>'
    if keywords.get('link'):
        print '<a title="%s" href="%s">%s</a>' % (
            user.current.text('Click here to do a full-text search for this title'), keywords['link'], text)
    else:
        print text
    print '</b></font></td>'

    # print the user's name
    print '<td valign="bottom" align="left"><font face="Verdana" size="1">%s<br>&nbsp;</font></td>' % (
        link_tag(quoteWikiname(config.page_user_prefs),
            (config.page_user_prefs, user.current.name)[user.current.valid]),)

    print '</tr></table>'

    # print the navigation bar (if configured)
    if config.navi_bar:
        if config.page_icons and keywords.has_key('pagename'):
            print config.page_icons % {
                'scriptname': webapi.getScriptname(),
                'url': config.url_prefix,
                'pagename': quoteWikiname(keywords['pagename'])}
        print config.navi_bar % {'scriptname': webapi.getScriptname()}

    # print a message if one is given
    if keywords.get('msg', ''):
        print "<br>", keywords['msg']
        print '<p><a href="%(scriptname)s/%(pagename)s?action=show">%(linktext)s</a>'% {
            'linktext': user.current.text('Clear message'),
            'scriptname': webapi.getScriptname(),
            'pagename': quoteWikiname(keywords['pagename'])}

    # print the rule above the wiki page
    print '<hr>'
    sys.stdout.flush()


_footer_fragments = {}

def add2footer(key, htmlcode):
    """ Add a named HTML fragment to the footer, after the default links
    """
    _footer_fragments[key] = htmlcode


def send_footer(pagename, mod_string=None, **keywords):
    """ Print the page footer.

        **pagename** -- WikiName of the page
        **mod_string** -- "last modified" date
        **keywords**:
            **editable** -- true, when page is editable (default: true)
            **showpage** -- true, when link back to page is wanted (default: false)
    """
    base = webapi.getScriptname()
    print "<hr>"
    if config.page_footer1: print config.page_footer1

    if keywords.get('showpage', 0):
        print link_tag(quoteWikiname(pagename), user.current.text("ShowText"))
        print user.current.text('of this page'), '<br>'
    if keywords.get('editable', 1):
        print link_tag(quoteWikiname(pagename)+'?action=edit', user.current.text('EditText'))
        print user.current.text('of this page')
        if mod_string:
            print user.current.text("(last modified %s)") % mod_string
        print '<br>'
    print link_tag('FindPage?value='+urllib.quote_plus(pagename, ''), user.current.text('FindPage'))
    print user.current.text(" by browsing, searching, or an index<br>")

    # output HTML code added by the page formatters
    if _footer_fragments:
        print string.join(_footer_fragments.values(), '')

    # list user actions that start with an uppercase letter
    from MoinMoin.action import extension_actions
    extension_actions.sort()
    first = 1
    for action in extension_actions:
        if action[0] != string.upper(action[0]): continue
        print (', ', user.current.text('Or try one of these actions: '))[first]
        sys.stdout.write(link_tag(
            '%s?action=%s' % (quoteWikiname(pagename), action), action))
        first = 0
    if not first: print "<br>"

    # end of footer
    if config.show_version:
        print '<p><font size="1" face="Verdana">MoinMoin %s, Copyright © 2000-2001 by Jürgen Hermann</font></p>' % (version.revision,)

    if config.page_footer2: print config.page_footer2


"""
    MoinMoin - Wiki Utility Functions

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikiutil.py,v 1.8 2000/11/25 17:39:33 jhermann Exp $
"""

# Imports
import os, re, string, sys, time, urllib
from MoinMoin import config, user, util, version


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
    except:
        try:
            wikitag, tail = string.split(wikiurl, "/", 1)
        except:
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
                    line + " " + util.getScriptname() + "/InterWiki", None, 2)
                _interwiki_list[wikitag] = urlprefix
            except:
                pass
        ##import pprint; print '<pre>'; pprint.pprint(_interwiki_list); print '</pre>'
        
    # split wiki url
    wikitag, tail = split_wiki(wikiurl)

    # return resolved url
    if wikitag and _interwiki_list.has_key(wikitag):
        return (wikitag, _interwiki_list[wikitag], urllib.quote(tail))
    else:
        return ("BadWikiTag", util.getScriptname(), "/InterWiki")


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


def getBackupList(backup_dir, pagename):
    """ Get a filename list of older versions of the page, sorted by date
        in descending order (last change first).
    """
    if os.path.isdir(backup_dir):
        backup_re = re.compile(r'^%s\.\d+\.\d+$' % (quoteFilename(pagename),))
        oldversions = filter(backup_re.match, os.listdir(backup_dir))
        oldversions.sort()
        oldversions.reverse()
    else:
        oldversions = None

    return oldversions


#############################################################################
### Edit Logging
#############################################################################
#!!! refactor to PageEditor class?

# Functions to keep track of when people have changed pages, so we can
# do the recent changes page and so on.
# The editlog is stored with one record per line, as tab-separated
# words: page_name, host, time, hostname

# TODO: Check values written in are reasonable

def editlog_add(page_name, host):
    from MoinMoin import user

    try:
        from socket import gethostbyaddr
        hostname = gethostbyaddr(host)[0]
    except:
        hostname = host

    editlog = open(config.editlog_name, 'a+')
    try: 
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_EX)
        editlog.seek(0, 2)                  # to end
        editlog.write(string.join((quoteFilename(page_name), host, `time.time()`, hostname, user.User().id), "\t") + "\n")
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


def editlog_raw_lines():
    editlog = open(config.editlog_name, 'rt')
    try:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_SH)
        return editlog.readlines()
    finally:
        # fcntl.flock(editlog.fileno(), fcntl.LOCK_UN)
        editlog.close()


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
        % (classattr, util.getScriptname(), params, text))


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
    print "<head>%s<title>%s</title>" % (config.html_head, text)
    if config.css_url:
        print '<link rel="stylesheet" type="text/css" href="%s">' % (config.css_url,)
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
        print '<a href="%s">%s</a>' % (keywords['link'], text)
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
                'scriptname': util.getScriptname(),
                'url': config.url_prefix,
                'pagename': quoteWikiname(keywords['pagename'])}
        print config.navi_bar % {'scriptname': util.getScriptname()}

    # print a message if one is given
    if keywords.get('msg', ''):
        print "<br>", keywords['msg']
        print '<p><a href="%(scriptname)s/%(pagename)s?action=show">Clear message</a>'% {
            'scriptname': util.getScriptname(),
            'pagename': quoteWikiname(keywords['pagename'])}

    # print the rule above the wiki page
    print '<hr>'


def send_footer(pagename, mod_string=None, **keywords):
    """ Print the page footer.

        **pagename** -- WikiName of the page
        **mod_string** -- "last modified" date
        **keywords**:
            **editable** -- true, when page is editable (default: true)
            **showpage** -- true, when link back to page is wanted (default: false)
    """
    base = util.getScriptname()
    print "<hr>"
    if config.page_footer1: print config.page_footer1

    if keywords.get('showpage', 0):
        print link_tag(quoteWikiname(pagename), "ShowText")
        print 'of this page<br>'
    if keywords.get('editable', 1):
        print link_tag(quoteWikiname(pagename)+'?action=edit', 'EditText')
        print "of this page"
        if mod_string:
            print "(last modified %s)" % mod_string
        print '<br>'
    print link_tag('FindPage?value='+urllib.quote_plus(pagename, ''), 'FindPage')
    print " by browsing, searching, or an index<br>"

    if config.show_version:
        print '<p><font size="1" face="Verdana">MoinMoin %s, Copyright © 2000 by Jürgen Hermann</font></p>' % (version.revision,)

    if config.page_footer2: print config.page_footer2


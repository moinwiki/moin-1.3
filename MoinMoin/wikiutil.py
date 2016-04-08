"""
    MoinMoin - Wiki Utility Functions

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikiutil.py,v 1.84 2002/03/09 15:55:22 jhermann Exp $
"""

# Imports
import os, re, string, sys, urllib
from MoinMoin import config, user, util, version, webapi
from MoinMoin.i18n import _, getText


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
    "(!)":  (15, 15, "idea.gif"),

    # copied 2001-11-16 from http://pikie.darktech.org/cgi/pikie.py?EmotIcon
    ":-?":  (15, 15, "tongue.gif"),
    ":\\":  (15, 15, "ohwell.gif"),
    ">:>":  (15, 15, "devil.gif"),
    "%)":   (15, 15, "eyes.gif"),
    "@)":   (15, 15, "eek.gif"),
    "|)":   (15, 15, "tired.gif"),
    ";))":  (15, 15, "lol.gif"),
}


def getSmiley(text, formatter):
    if user.current.show_emoticons:
        w, h, img = smileys[string.strip(text)]
        return formatter.image(
            src="%s/img/%s" % (config.url_prefix, img),
            alt=text, hspace=6, width=w, height=h)
    else:
        return formatter.text(text)


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
    # load map (once, and only on demand)
    global _interwiki_list
    if _interwiki_list is None:
        _interwiki_list = {}
        lines = []
        
        # order is important here, the local intermap file takes
        # precedence over the shared one, and is thus read AFTER
        # the shared one
        for filename in [config.shared_intermap, 
                os.path.join(config.data_dir, "intermap.txt")]:
            if filename and os.path.isfile(filename):
                f = open(filename, "r")
                lines.extend(f.readlines())
                f.close()

        for line in lines:
            if not line or line[0] == '#': continue
            try:
                wikitag, urlprefix, trash = string.split(
                    line + " " + webapi.getScriptname() + "/InterWiki", None, 2)
            except ValueError:
                pass
            else:
                _interwiki_list[wikitag] = urlprefix

        del lines

        # add own wiki as "Self" and by its configured name
        _interwiki_list['Self'] = webapi.getScriptname() + '/'
        if config.interwikiname:
            _interwiki_list[config.interwikiname] = webapi.getScriptname() + '/'

    # split wiki url
    wikitag, tail = split_wiki(wikiurl)

    # return resolved url
    if wikitag and _interwiki_list.has_key(wikitag):
        return (wikitag, _interwiki_list[wikitag], tail)
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
        oldversions = []
        for file in os.listdir(backup_dir):
            if not backup_re.match(file): continue
            data = string.split(file, '.', 1)
            oldversions.append(((data[0], float(data[1])), file))
        oldversions.sort()
        oldversions.reverse()

        #!!!2.0 oldversions = [x[1] for x in oldversions]
        oldversions = map(lambda x: x[1], oldversions)
    else:
        oldversions = []

    return oldversions


def getSysPage(pagename):
    """ Get a system page according to user settings and available
        translations.
    """
    from MoinMoin.Page import Page

    i18n_name = getText(pagename)
    if i18n_name != pagename:
        i18n_page = Page(i18n_name)
        if i18n_page.exists():
            return i18n_page
    return Page(pagename)


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

def parseAttributes(attrstring, endtoken=None, extension=None):
    """ Parse a list of attributes and return a dict plus a possible
        error message.

        If extension is passed, it has to be a callable that returns
        None when it was not interested into the token, '' when all was OK
        and it did eat the token, and any other string to return an error
        message.
    """
    import cgi, shlex, cStringIO

    parser = shlex.shlex(cStringIO.StringIO(attrstring))
    parser.commenters = ''
    msg = None
    attrs = {}

    while not msg:
        key = parser.get_token()
        if not key: break
        if endtoken and key == endtoken: break

        # call extension function with the current token, the parser, and the dict
        if extension:
            msg = extension(key, parser, attrs)
            if msg == '': continue
            if msg: break

        eq = parser.get_token()
        if eq != "=":
            msg = _('Expected "=" to follow "%(token)s"') % {'token': key}
            break

        val = parser.get_token()
        if not val:
            msg = _('Expected a value for key "%(token)s"') % {'token': key}
            break

        key = cgi.escape(key) # make sure nobody cheats

        # safely escape and quote value
        if val[0] in ["'", '"']:
            val = cgi.escape(val)
        else:
            val = '"%s"' % cgi.escape(val, 1)

        attrs[string.lower(key)] = val

    return attrs, msg or ''


def taintfilename(basename):
    """ Make a filename that is supposed to be a plain name secure, i.e.
        remove any possible path components that compromise our system.
    """
    # replace unsafe path components
    basename = string.replace(basename, os.pardir, '_')
    basename = string.replace(basename, ':', '_')
    basename = string.replace(basename, '/', '_')
    basename = string.replace(basename, '\\', '_')
    return basename


def mapURL(url):
    """ Map URLs according to 'config.url_mappings'.
    """
    # check whether we have to map URLs
    if config.url_mappings:
        # check URL for the configured prefixes
        for prefix in config.url_mappings.keys():
            if url.startswith(prefix):
                # substitute prefix with replacement value
                return config.url_mappings[prefix] + url[len(prefix):]

    # return unchanged url
    return url


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


def isTemplatePage(pagename):
    """Is this a template page?"""
    return pagename[-len(config.page_template_ending):] == config.page_template_ending


def isFormPage(pagename):
    """Is this a form page?"""
    return pagename[-len(config.page_form_ending):] == config.page_form_ending


def link_tag(params, text=None, css_class=None, formatter=None, **kw):
    if text is None:
        text = params # default
    if formatter:
        return apply(formatter.url,
            ("%s/%s" % (webapi.getScriptname(), params), text, css_class), kw)
    if css_class:
        classattr = ' class="%s"' % css_class
    else:
        classattr = ''
    return ('<a%s href="%s/%s">%s</a>'
        % (classattr, webapi.getScriptname(), params, text))


def pagediff(pagename, oldpage, **kw):
    # build the diff command and execute it
    backup_file = os.path.join(config.backup_dir, oldpage)
    page_file = os.path.join(config.text_dir, quoteFilename(pagename))
    options = '-u'
    if kw.get('ignorews', 0): options = options + ' -b'
    cmd = "%(diff)s %(options)s %(backup)s %(page)s" % {
        "diff": config.external_diff,
        "options": options,
        "backup": backup_file,
        "page": page_file,
    }
    diff = util.popen(cmd, "r")
    lines = diff.readlines()
    rc = diff.close()
    ##print "cmd =", cmd, "<br>"
    ##print "rc =", rc, "<br>"

    return page_file, backup_file, lines


def send_title(text, **keywords):
    """
        **text** -- title text
        **keywords** --
            **link**: URL for the title
            **msg**: additional message (after saving)
            pagename='PageName'
            print_mode=1 (or 0)
            allow_doubleclick=1 (or 0)
    """
    import cgi
    from MoinMoin.Page import Page

    # get name of system pages
    page_help_contents = getSysPage('HelpContents').page_name
    page_title_index = getSysPage('TitleIndex').page_name
    page_word_index = getSysPage('WordIndex').page_name
    page_user_prefs = getSysPage('UserPreferences').page_name
    page_edit_tips = getSysPage('HelpOnFormatting').page_name

    # print the HTML <HEAD> element
    user_head = config.html_head
    if os.environ.get('QUERY_STRING', '') or os.environ.get('REQUEST_METHOD', '') == 'POST':
        user_head = user_head + config.html_head_queries
    print "<html><head>%s<title>%s - %s</title>" % (user_head, cgi.escape(text), config.sitename)

    # add keywords from page title
    if keywords.has_key('pagename'):
        words = Page(keywords['pagename']).split_title(force=1)
        print '<meta name="KEYWORDS" content="%s">' % (
            cgi.escape(string.replace(words, ' ', ', '), 1))

    # link to CSS stylesheet
    css_url = user.current.valid and user.current.css_url or config.css_url
    if css_url and string.lower(css_url) != "none":
        print '<link rel="stylesheet" type="text/css" href="%s">' % (css_url,)

    # Links
    print '<link rel="Start" href="%s">' % quoteWikiname(config.page_front_page)
    if keywords.has_key('pagename'):
        print '<link rel="Alternate" media="print" title="Print" href="%s?action=print">' % (
            quoteWikiname(keywords['pagename']),)
    print '<link rel="Index" href="%s">' % quoteWikiname(page_title_index)
    print '<link rel="Glossary" href="%s">' % quoteWikiname(page_word_index)
    print '<link rel="Help" href="%s">' % quoteWikiname(page_edit_tips)

    print "</head>"
    sys.stdout.flush()

    # start the <BODY>
    bodyattr = ''
    if keywords.get('allow_doubleclick', 0) and not keywords.get('print_mode', 0) \
            and keywords.has_key('pagename') and user.current.may.edit \
            and user.current.edit_on_doubleclick:
        bodyattr = bodyattr + ''' ondblclick="location.href='%s'"''' % (
            Page(keywords['pagename']).url("action=edit"))
    bodyattr = bodyattr + ''' onload="window.defaultStatus='%s'"''' % (
        string.replace(string.replace(config.sitename, '"', "'"), "'", "&apos;"))
    print '<body%s><a name="top"></a>' % bodyattr

    # if in print mode, emit the title and return immediately
    if keywords.get('print_mode', 0):
        print '<h1>%s</h1><hr>\n' % (cgi.escape(text),)
        return

    # print custom html code before system title
    if config.title1: print config.title1

    # print the page header (logo, title)
    print '<table width="100%"><tr><td>'

    if config.logo_string:
        print link_tag(quoteWikiname(config.page_front_page), config.logo_string)
    print '</td><td width="99%" valign="middle" class="headline"><font size="+3">&nbsp;<b>'
    if keywords.get('link'):
        print '<a title="%s" href="%s">%s</a>' % (
            _('Click here to do a full-text search for this title'), keywords['link'],
            cgi.escape(text))
    else:
        print cgi.escape(text)
    print '</b></font></td>'

    # print the user's name
    print '<td valign="bottom" align="left" nowrap>'
    print '<font face="Verdana" size="1">%s<br>&nbsp;</font>' % (
        link_tag(quoteWikiname(page_user_prefs),
            (page_user_prefs, user.current.name)[user.current.valid]),)
    print '</td></tr></table>'

    # print the icon toolbar (if configured)
    if config.page_icons and user.current.show_toolbar and keywords.has_key('pagename'):
        pagename = keywords['pagename']
        if user.current.valid and Page(user.current.name).exists():
            icon = config.page_icons_home % {'url': config.url_prefix}
            print link_tag(quoteWikiname(user.current.name), text=icon)
        iconbar = config.page_icons % {
            'scriptname': webapi.getScriptname(),
            'url': config.url_prefix,
            'pagename': quoteWikiname(pagename),
            'page_help_contents': page_help_contents,
            'page_find_page': getSysPage('FindPage').page_name,
        }
        if not user.current.isSubscribedTo([pagename]):
            iconbar = string.replace(iconbar, "moin-email.gif", "moin-email-x.gif")
        print iconbar
        if config.allow_subpages:
            pos = string.rfind(pagename, '/')
            if pos >= 0:
                parentpage = pagename[:pos]
                if Page(parentpage).exists():
                    icon = config.page_icons_up % {'url': config.url_prefix}
                    print link_tag(quoteWikiname(parentpage), text=icon)

    # print the navigation bar (if configured)
    if config.navi_bar:
        print (
            '<table cellpadding=0 cellspacing=3 border=0 style="background-color:#C8C8C8;text-decoration:none">'
            '<tr><td valign=top align=center bgcolor="#E8E8E8">'
            '<font face="Arial,Helvetica" size="-1">&nbsp;<b>%(sitename)s</b>&nbsp;'
            '</font></td>') % {'sitename': config.sitename,}

        for pagename in config.navi_bar:
            pagename = getSysPage(pagename).page_name
            print (
                '<td valign=top align=center bgcolor="#E8E8E8">'
                '<font face="Arial,Helvetica" size="-1">'
                '&nbsp;<a style="text-decoration:none" href="%(scriptname)s/%(pagelink)s">%(pagename)s</a>&nbsp;'
                '</font></td>') % {
            'scriptname': webapi.getScriptname(),
            'pagelink': quoteWikiname(pagename),
            'pagename': pagename,
        }

        print '</tr></table>'

    # print a message if one is given
    if keywords.get('msg', ''):
        print '<div class="message">'
        print keywords['msg']
        print '<p><a href="%(scriptname)s/%(pagename)s?action=show">%(linktext)s</a>'% {
            'linktext': _('Clear message'),
            'scriptname': webapi.getScriptname(),
            'pagename': quoteWikiname(keywords['pagename'])}
        print '</div>'

    # print custom html code after system title (normally "<hr>")
    if config.title2: print config.title2

    # emit it
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
            **print_mode** -- true, when page is displayed in print mode
    """
    import cgi

    print '<a name="bottom"></a>'
    if config.page_footer1: print config.page_footer1

    print """
<table border="0" cellspacing="0" cellpadding="0">
<form method="POST" action="%s">
<tr><td>
<input type="hidden" name="action" value="inlinesearch">
""" % cgi.escape(pagename, 1)

    if keywords.get('showpage', 0):
        print link_tag(quoteWikiname(pagename), _("ShowText"))
        print _('of this page'), '<br>'
    if keywords.get('editable', 1) and user.current.may.edit:
        print link_tag(quoteWikiname(pagename)+'?action=edit', _('EditText'))
        print _('of this page')
        if mod_string:
            print _("(last modified %s)") % mod_string
        print '<br>'

    form = keywords.get('form', None)
    searchfield = (
        '<input style="font-family:Verdana; font-size:9pt;"'
        ' type="text" name="text_%%(type)s" value="%%(value)s"'
        ' size="15" maxlength="50">'
        '<input type="image" src="%s/img/moin-search.gif"'
        ' name="button_%%(type)s" '
        ' alt="[?]" hspace="3" width="12" height="12" border="0">'
        ) % config.url_prefix
    titlesearch = searchfield % {
        'type': 'title',
        'value': cgi.escape(form and form.getvalue('text_title', '') or '', 1),
    }
    textsearch = searchfield %  {
        'type': 'full',
        'value': cgi.escape(form and form.getvalue('text_full', '') or '', 1),
    }

    print link_tag(getSysPage('FindPage').page_name+'?value='+urllib.quote_plus(pagename, ''), _('FindPage'))
    print _(" by browsing, title search %(titlesearch)s, "
        "text search %(textsearch)s or an index<br>") % locals()

    # output HTML code added by the page formatters
    if _footer_fragments:
        print string.join(_footer_fragments.values(), '')

    # list user actions that start with an uppercase letter
    if keywords.get('showactions', 1):
        from MoinMoin.wikiaction import getPlugins
        from MoinMoin.action import extension_actions
        dummy, actions = getPlugins()
        actions.extend(extension_actions)
        actions.sort()
        first = 1
        for action in actions:
            if action[0] != string.upper(action[0]): continue
            print (', ', _('Or try one of these actions: '))[first]
            sys.stdout.write(link_tag(
                '%s?action=%s' % (quoteWikiname(pagename), action), action))
            first = 0
        if not first: print "<br>"

    # end of footer
    if config.show_version and not keywords.get('print_mode', 0):
        print '<p><font size="1" face="Verdana">MoinMoin %s, Copyright © 2000, 2001, 2002 by Jürgen Hermann</font></p>' % (version.revision,)

    print """
</td></tr>
</form>
</table>
"""

    if config.page_footer2: print config.page_footer2


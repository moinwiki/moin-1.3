# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Utility Functions

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikiutil.py,v 1.158 2003/11/09 21:00:52 thomaswaldmann Exp $
"""

# Imports
import os, re, string, sys, urllib
from MoinMoin import config, util, version, webapi
from MoinMoin.util import filesys


# list of pages that should be trated as system pages
SYSTEM_PAGES = [
    config.page_front_page,
    'RecentChanges',
    'TitleIndex',
    'WordIndex',
    'SiteNavigation',
    'HelpContents',
    'UserPreferences',
    'HelpOnFormatting',
    'FindPage',
    'AbandonedPages',
    'OrphanedPages',
    'PageSize',
    'RandomPage',
    'WantedPages',
]

# constants for page names
PARENT_PREFIX = "../" # changing this might work, but it's not tested
CHILD_PREFIX = "/" # changing this will not really work

# Caching for precompiled page type regex
_TEMPLATE_RE = None
_FORM_RE = None
_CATEGORY_RE = None


#############################################################################
### Smileys
#############################################################################

def getSmiley(text, formatter):
    if formatter.request.user.show_emoticons:
        w, h, b, img = config.smileys[string.strip(text)]
        href = img
        if not href.startswith('/'):
            href = "%s/img/%s" % (config.url_prefix, img)
        return formatter.image(
            src=href, alt=text, hspace=6, width=w, height=h, border=b)
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
    return ''.join(res)


def unquoteFilename(filename):
    return urllib.unquote(filename.replace('_', '%'))


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


def join_wiki(wikiurl, wikitail):
    """ add a page name to an interwiki url
    """
    if string.find(wikiurl, '$PAGE') == -1:
        return wikiurl + wikitail
    else:
        return string.replace(wikiurl, '$PAGE', wikitail)


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
        intermap_files = config.shared_intermap
        if not isinstance(intermap_files, type([])):
            intermap_files = [intermap_files]
        intermap_files.append(os.path.join(config.data_dir, "intermap.txt"))

        for filename in intermap_files:
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
### Page types (based on page names)
#############################################################################

def isSystemPage(pagename):
    """Is this a system page?"""
    #!!!: Possibly load list from "MoinMoinSystemPages"
    return pagename.startswith('HelpOn') or pagename.startswith('HelpFor') \
        or pagename.startswith('HilfeZu') \
        or isTemplatePage(pagename) or isFormPage(pagename)


def isTemplatePage(pagename):
    """Is this a template page?"""
    global _TEMPLATE_RE
    if _TEMPLATE_RE is None:
        _TEMPLATE_RE = re.compile(config.page_template_regex)
    return _TEMPLATE_RE.search(pagename) is not None


def isFormPage(pagename):
    """Is this a form page?"""
    global _FORM_RE
    if _FORM_RE is None:
        _FORM_RE = re.compile(config.page_form_regex)
    return _FORM_RE.search(pagename) is not None


def filterCategoryPages(pagelist):
    """ Return a copy of `pagelist` that only contains category pages.

        If you pass a list with a single pagename, either that is returned
        or an empty list, thus you can use this function like a `isCategoryPage`
        one.
    """
    global _CATEGORY_RE
    if _CATEGORY_RE is None:
        _CATEGORY_RE = re.compile(config.page_category_regex)
    return filter(_CATEGORY_RE.match, pagelist)


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
            data = file.split('.', 1)
            oldversions.append(((data[0], float(data[1])), file))
        oldversions.sort()
        oldversions.reverse()

        oldversions = [x[1] for x in oldversions]
    else:
        oldversions = []

    return oldversions


def getSysPage(pagename):
    """ Get a system page according to user settings and available
        translations.
    """
    from MoinMoin.Page import Page
    from MoinMoin.i18n import getText

    i18n_name = getText(pagename, check_i18n=0)
    if i18n_name != pagename:
        i18n_page = Page(i18n_name)
        if i18n_page.exists():
            return i18n_page
    return Page(pagename)


def getHomePage(request, username=None):
    """ Get a user's homepage, or return None for anon users and
        those who have not created a homepage.
    """
    # default to current user
    if username is None and request.user.valid:
        username = request.user.name

    # known user?
    if username:
        from MoinMoin.Page import Page

        # plain homepage?
        pg = Page(username)
        if pg.exists(): return pg

        # try without spaces
        pg = Page(''.join(username.split()))
        if pg.exists(): return pg

    return None


def getPagePath(pagename, *args, **kw):
    """ Get full path to a page-specific storage name. `args` can
        contain additional path components that are added to the base
        path.

        `check_create` ensures that the page storage area exists, excluding
        the additional path components (default is true).
    """
    pagename = quoteFilename(pagename)

    path = os.path.join(config.data_dir, "pages", pagename)
    if kw.get('check_create', 1) and not os.path.exists(path): 
        filesys.makeDirs(path)

    return os.path.join(*((path,) + args))


def AbsPageName(request, context, pagename):
    """ Return the absolute pagename for a (possibly) relative pagename.

        `context` is the name of the page this relative path appears on.
    """
    if config.allow_subpages:
        if pagename.startswith(PARENT_PREFIX):
            pagename = '/'.join(filter(None, context.split('/')[:-1] + [pagename[3:]]))
        elif pagename.startswith(CHILD_PREFIX):
            pagename = context + pagename

    return pagename


#############################################################################
### Searching
#############################################################################

def searchPages(needle, **kw):
    """ Search the text of all pages for "needle", and return a tuple of
        (number of pages, hits).

        `hits` is a list of tuples containing the number of hits on a page
        and the pagename. When context>0, a list of triples with the text of
        the hit and the text on each side of it is added; otherwise, the
        third element is None.

        literal = 0: try to treat "needle" as a regex
        literal = 1: "needle" is definitely NOT a regex
        case = 1: case-sensitive search
        context != 0: Provide `context` chars of text on each side of a hit
    """
    from MoinMoin.Page import Page

    literal = kw.get('literal', 0)
    context = int(kw.get('context', 0))
    ignorecase = int(kw.get('case', 0)) == 0 and re.IGNORECASE or 0

    if literal and context:
        needle_re = re.compile(re.escape(needle), ignorecase)
    elif literal:
        if ignorecase:
            needle = string.lower(needle)
    else:
        try:
            needle_re = re.compile(needle, ignorecase)
        except re.error:
            needle_re = re.compile(re.escape(needle), ignorecase)

    hits = []
    all_pages = getPageList(config.text_dir)
    for page_name in all_pages:
        body = Page(page_name).get_raw_body()
        if context:
            pos = 0
            fragments = []
            while 1:
                match = needle_re.search(body, pos)
                if not match: break
                pos = match.end()
                fragments.append((
                    body[match.start()-context:match.start()],
                    body[match.start():match.end()],
                    body[match.end():match.end()+context],
                ))
            if fragments:
                hits.append((len(fragments), page_name, fragments))
        else:
            if literal:
                if ignorecase:
                    body = string.lower(body)
                count = string.count(body, needle)
            else:
                count = len(needle_re.findall(body))
            if count:
                hits.append((count, page_name, None))

    # we sort:
    # 1. by descending number of hits
    # 2. by ascending name of page
    hits.sort(lambda x,y: cmp((y[0], x[1]), (x[0], y[1])))

    return (len(all_pages), hits)


#############################################################################
### Misc
#############################################################################

def parseAttributes(request, attrstring, endtoken=None, extension=None):
    """ Parse a list of attributes and return a dict plus a possible
        error message.

        If extension is passed, it has to be a callable that returns
        None when it was not interested into the token, '' when all was OK
        and it did eat the token, and any other string to return an error
        message.
    """
    import cgi, shlex, cStringIO

    _ = request.getText

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


def getUnicodeIndexGroup(name):
    """ Return a group letter for `name`, which must be a unicode string.

        Currently supported:
            - Hangul Syllables (U+AC00 - U+D7AF)
    """
    if u'\uAC00' <= name[0] <= u'\uD7AF': # Hangul Syllables
        return unichr(0xac00 + (int(ord(name[0]) - 0xac00) / 588) * 588)
    else:
        return None


def isUnicodeName(name):
    """Try to determine if the quoted wikiname is a special, pure unicode name"""
    # escape name if not escaped
    text = name
    if not string.count(name, '_'):
        text = quoteWikiname(name)

    # check if every character is escaped
    return len(string.replace(text,'_','')) == len(text) * 2/3


def isStrictWikiname(name, word_re=re.compile(r"^(?:[%(u)s][%(l)s]+){2,}$" % {'u':config.upperletters, 'l':config.lowerletters})):
    """Check whether this is NOT an extended name"""
    return word_re.match(name)


def isPicture(url):
    """Check for picture URLs"""
    extpos = string.rfind(url, ".")
    return extpos > 0 and string.lower(url[extpos:]) in ['.gif', '.jpg', '.jpeg', '.png']


def link_tag(params, text=None, formatter=None, **kw):
    """ Create a link.

        Keyword params:
            target - link target
            attrs - additional attrs (HTMLified string)
    """
    css_class = kw.get('css_class', None)
    if text is None:
        text = params # default
    if formatter:
        return formatter.url("%s/%s" % (webapi.getScriptname(), params), text, css_class, **kw)
    attrs = ''
    if kw.has_key('attrs'):
        attrs += ' ' + kw['attrs']
    if css_class:
        attrs += ' class="%s"' % css_class
    target = kw.get('target', None)
    if target:
        attrs += ' target="%s"' % target
    return ('<a%s href="%s/%s">%s</a>'
        % (attrs, webapi.getScriptname(), params, text))


def pagediff(pagename, oldpage, **kw):
    """ Call the "diff" command for `pagename` and `oldpage`.

        `ignorews=1` means to ignore pure-whitespace changes.

        Returns a tuple of diff return code, page file name,
        backup page file name, and a list of lines of diff output.
    """
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

    return rc, page_file, backup_file, lines


#############################################################################
### Page header / footer
#############################################################################

def emit_custom_html(request, html):
    """ Emit the HTML code in the string `html`, or if `html`
        is a callable, emit its return value.
    """
    if html:
        if callable(html): html = html(request)
        request.write(html)


def send_title(request, text, **keywords):
    """
        **text** -- title text
        **keywords** --
            link: URL for the title
            msg: additional message (after saving)
            pagename='PageName'
            print_mode=1 (or 0)
            allow_doubleclick=1 (or 0)
            html_head: additional <HEAD> code
            body_class: CSS style for BODY tag
            body_attr: additional BODY attributes
            body_onload: additional "onload" JavaScript code
    """
    import cgi
    from MoinMoin import i18n
    from MoinMoin.Page import Page

    _ = request.getText
    pagename = keywords.get('pagename', None)

    # get name of system pages
    page_front_page = getSysPage(config.page_front_page).page_name
    page_help_contents = getSysPage('HelpContents').page_name
    page_title_index = getSysPage('TitleIndex').page_name
    page_word_index = getSysPage('WordIndex').page_name
    page_user_prefs = getSysPage('UserPreferences').page_name
    page_edit_tips = getSysPage('HelpOnFormatting').page_name
    page_find_page = getSysPage('FindPage').page_name

    # parent page?
    parentpage = None
    if pagename and config.allow_subpages:
        pos = string.rfind(pagename, '/')
        if pos >= 0:
            parentpage = Page(pagename[:pos])

    # print the HTML <HEAD> element
    user_head = config.html_head
    if os.environ.get('QUERY_STRING', '') or os.environ.get('REQUEST_METHOD', '') == 'POST':
        user_head = user_head + config.html_head_queries
    request.write("<html><head>%s<title>%s - %s</title>%s" % (
        user_head, cgi.escape(text),
        cgi.escape(config.html_pagetitle or config.sitename),
        keywords.get('html_head', ''),
    ))

    # add keywords from page title
    if pagename:
        words = Page(pagename).split_title(force=1)
        print '<meta name="KEYWORDS" content="%s">' % (
            cgi.escape(string.replace(words, ' ', ', '), 1))

    # link to CSS stylesheet
    css_url = request.user.valid and request.user.css_url or config.css_url
    if css_url and string.lower(css_url) != "none":
        # send special css for certain media types
        if keywords.get('print_mode', 0) and request.form.has_key('media'):
            media = request.form['media'].value
            css_url = '%s/%s.css' % ('/'.join(css_url.split('/')[:-1]), media)
        print '<link rel="stylesheet" type="text/css" href="%s">' % (css_url,)

    # Links
    # !!! make this a user setting!
    print '<link rel="Start" href="%s/%s">' % (webapi.getScriptname(), quoteWikiname(page_front_page))
    if pagename:
        request.write('<link rel="Alternate" title="%s" href="%s/%s?action=raw">\n' % (
            _('Wiki Markup'), webapi.getScriptname(), quoteWikiname(pagename),))
        request.write('<link rel="Alternate" media="print" title="%s" href="%s/%s?action=print">\n' % (
            _('Print View'), webapi.getScriptname(), quoteWikiname(pagename),))

        # !!! currently disabled due to Mozilla link prefetching, see
        # http://www.mozilla.org/projects/netlib/Link_Prefetching_FAQ.html
        #~ all_pages = request.getPageList()
        #~ if all_pages:
        #~     try:
        #~         pos = all_pages.index(pagename)
        #~     except ValueError:
        #~         # this shopuld never happend in theory, but let's be sure
        #~         pass
        #~     else:
        #~         request.write('<link rel="First" href="%s/%s">\n' % (webapi.getScriptname(), quoteWikiname(all_pages[0]))
        #~         if pos > 0:
        #~             request.write('<link rel="Previous" href="%s/%s">\n' % (webapi.getScriptname(), quoteWikiname(all_pages[pos-1])))
        #~         if pos+1 < len(all_pages):
        #~             request.write('<link rel="Next" href="%s/%s">\n' % (webapi.getScriptname(), quoteWikiname(all_pages[pos+1])))
        #~         request.write('<link rel="Last" href="%s/%s">\n' % (webapi.getScriptname(), quoteWikiname(all_pages[-1])))

        if parentpage and parentpage.exists():
            print '<link rel="Up" href="%s">' % parentpage.url()

        from MoinMoin.action import AttachFile
        AttachFile.send_link_rel(request, pagename)

    print '<link rel="Search" href="%s/%s">' % (webapi.getScriptname(), quoteWikiname(page_find_page))
    print '<link rel="Index" href="%s/%s">' % (webapi.getScriptname(), quoteWikiname(page_title_index))
    print '<link rel="Glossary" href="%s/%s">' % (webapi.getScriptname(), quoteWikiname(page_word_index))
    print '<link rel="Help" href="%s/%s">' % (webapi.getScriptname(), quoteWikiname(page_edit_tips))

    print "</head>"
    sys.stdout.flush()

    # start the <BODY>
    bodyattr = ''
    body_onload = keywords.get('body_onload', '')
    if body_onload:
        body_onload = "; %s" % body_onload
    if keywords.has_key('body_attr'):
        bodyattr += ' ' + keywords['body_attr']
    if keywords.get('allow_doubleclick', 0) and not keywords.get('print_mode', 0) \
            and pagename and request.user.may.edit(pagename) \
            and request.user.edit_on_doubleclick:
        bodyattr += ''' ondblclick="location.href='%s'"''' % (
            Page(pagename).url("action=edit"))
    bodyattr += ''' onload="window.defaultStatus='%s'%s"''' % (
        config.sitename.replace('"', "'").replace("'", "&apos;"),
        body_onload,
    )
    body_class = keywords.get('body_class')
    if body_class:
        bodyattr += ' class="%s"' % body_class
    bodyattr += ' lang="%s" dir="%s"' % (
        config.default_lang, i18n.getDirection(config.default_lang))
    print '<body%s><a name="top"></a>' % bodyattr

    # if in print mode, emit the title and return immediately
    if keywords.get('print_mode', 0):
        ## print '<h1>%s</h1><hr>\n' % (cgi.escape(text),)
        return

    # print custom html code before system title
    emit_custom_html(request, config.title1)

    # print the page header (logo, title)
    print '<table width="100%"><tr><td>'

    if config.logo_string:
        print link_tag(quoteWikiname(page_front_page), config.logo_string)
    print '</td><td width="99%" valign="middle" class="headline">&nbsp;'
    if keywords.get('link'):
        print '<a title="%s" href="%s">%s</a>' % (
            _('Click here to do a full-text search for this title'), keywords['link'],
            cgi.escape(text))
    else:
        print cgi.escape(text)
    print '</td>'

    # print the user's name
    print '<td valign="bottom" align="left" nowrap>'
    print '<font face="Verdana" size="1">%s<br>&nbsp;</font>' % (
        link_tag(quoteWikiname(page_user_prefs),
            cgi.escape((page_user_prefs, request.user.name)[request.user.valid])),)
    print '</td></tr></table>'

    # print the icon toolbar (if configured)
    # !!! TODO: i18n for title=
    if config.page_icons and request.user.show_toolbar and pagename:
        homepage = getHomePage(request)
        if homepage:
            icon = config.page_icons_home % {'url': config.url_prefix}
            print link_tag(quoteWikiname(homepage.page_name), text=icon,
                           attrs='title="Homepage" alt="Homepage"')
        iconbar = config.page_icons % {
            'scriptname': webapi.getScriptname(),
            'url': config.url_prefix,
            'pagename': quoteWikiname(pagename),
            'page_help_contents': page_help_contents,
            'page_find_page': getSysPage('FindPage').page_name,
        }
        if not request.user.isSubscribedTo([pagename]):
            iconbar = string.replace(iconbar, "moin-email.gif", "moin-email-x.gif")
        print iconbar
        if parentpage and parentpage.exists():
            icon = config.page_icons_up % {'url': config.url_prefix}
            print link_tag(quoteWikiname(parentpage.page_name), text=icon,
                           attrs='title="Up" alt="Up"')

    # print the navigation bar (if configured)
    quicklinks = request.user.getQuickLinks()
    if config.navi_bar or quicklinks:
        print (
            '<table class="navibar" cellpadding=0 cellspacing=3 border=0>'
            '<tr><td class="navibar" valign=top align=center bgcolor="#E8E8E8">'
            '<font class="navibar" face="Arial,Helvetica" size="-1">&nbsp;<b>%(sitename)s</b>&nbsp;'
            '</font></td>') % {'sitename': config.sitename,}

        if not quicklinks:
            for navi_link in config.navi_bar:
                newwin = ''
                if navi_link.startswith('^'):
                    newwin = '^'
                    navi_link = navi_link[1:]
                if not navi_link.startswith('['):
                    # copy real links verbatim, try to map system pages else
                    navi_link = getSysPage(navi_link).page_name
                quicklinks.append(newwin + navi_link)

        for navi_link in quicklinks:
            target = ''
            if navi_link.startswith('[^'):
                target = '_blank'
                navi_link = '[' + navi_link[2:]
            elif navi_link.startswith('^'):
                target = '_blank'
                navi_link = navi_link[1:]

            if navi_link.startswith('[') and navi_link.endswith(']'):
                try:
                    link, navi_link = navi_link[1:-1].split(' ', 1)
                except ValueError, TypeError:
                    link = "#error"
                    navi_link = "Broken link: " + cgi.escape(navi_link)
                else:
                    # escape untrusted input!                   
                    link = cgi.escape(link, quote=1)
                    navi_link = cgi.escape(navi_link)
            else:
                link =  "%s/%s" % (webapi.getScriptname(), quoteWikiname(navi_link))

            if target:
                target = ' target="%s"' % target

            print (
                '<td class="navibar" valign=top align=center bgcolor="#E8E8E8">'
                '<font class="navibar" face="Arial,Helvetica" size="-1">'
                '&nbsp;<a%(target)s class="navibar" href="%(link)s">%(navi_link)s</a>&nbsp;'
                '</font></td>') % locals()

        print '</tr></table>'

    # print a message if one is given
    if keywords.get('msg', ''):
        print '<div class="message">'
        print keywords['msg']
        print '<p><a href="%(scriptname)s/%(pagename)s?action=show">%(linktext)s</a>'% {
            'linktext': _('Clear message'),
            'scriptname': webapi.getScriptname(),
            'pagename': quoteWikiname(pagename),
        }
        print '</div>'

    # print custom html code after system title (normally "<hr>")
    emit_custom_html(request, config.title2)

    # emit it
    sys.stdout.flush()


def send_footer(request, pagename, mod_string=None, **keywords):
    """ Print the page footer.

        **pagename** -- WikiName of the page
        **mod_string** -- "last modified" date
        **keywords**:
            **editable** -- true, when page is editable (default: true)
            **showpage** -- true, when link back to page is wanted (default: false)
            **print_mode** -- true, when page is displayed in print mode
    """
    import cgi
    from MoinMoin import i18n
    from MoinMoin.Page import Page

    _ = request.getText
    page = Page(pagename)

    print '<a name="bottom"></a>'
    emit_custom_html(request, config.page_footer1)

    print """
<table lang="%s" dir="%s" border="0" cellspacing="0" cellpadding="0" class="footer" width="100%%">
<form method="POST" action="%s/%s">
<tr><td>
<input type="hidden" name="action" value="inlinesearch">
<input type="hidden" name="context" value="40">
""" % (
    config.default_lang, i18n.getDirection(config.default_lang),
    webapi.getScriptname(), quoteWikiname(pagename))

    # ShowText link (on action pages)
    if keywords.get('showpage', 0):
        print link_tag(quoteWikiname(pagename), _("ShowText"))
        print _('of this page'), '<br>'

    # EditText link (or indication that page cannot be edited)
    if keywords.get('editable', 1):
        editable = request.user.may.edit(pagename) and page.isWritable()
        if editable:
            request.write(link_tag(quoteWikiname(pagename)+'?action=edit', _('EditText')),
                ' ', _('of this page'))
        else:
            request.write(_('Immutable page'))

        request.write(_('&nbsp;&nbsp; [current page size <b>%(size)d</b> bytes]')
             % {'size': page.size()}, '&nbsp;&nbsp; ', mod_string or '', '<br>')

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
    if request._footer_fragments:
        print string.join(request._footer_fragments.values(), '')

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
            request.write(link_tag(
                '%s?action=%s' % (quoteWikiname(pagename), action), action))
            first = 0
        if not first: print "<br>"

    # end of footer
    if config.show_version and not keywords.get('print_mode', 0):
        print '<p><font size="1" face="Verdana">MoinMoin %s, Copyright \xa9 2000, 2001, 2002, 2003 by Jürgen Hermann</font></p>' % (version.revision,)

    print """
</td></tr>
</form>
</table>
"""

    emit_custom_html(request, config.page_footer2)


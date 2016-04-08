# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Utility Functions

    @copyright: 2000 - 2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import os, re, urllib
from MoinMoin.support import difflib
from MoinMoin import config, util, version
from MoinMoin.util import filesys, pysupport

# constants for page names
PARENT_PREFIX = "../" # changing this might work, but it's not tested
CHILD_PREFIX = "/" # changing this will not really work

# Caching for precompiled page type regex
_TEMPLATE_RE = None
_FORM_RE = None
_CATEGORY_RE = None


def getSmiley(text, formatter):
    """
    Get a graphical smiley for a text smiley
    
    @param text: the text smiley
    @param formatter: the formatter to use
    @rtype: string
    @return: formatted output
    """
    req = formatter.request
    if req.user.show_emoticons:
        w, h, b, img = config.smileys[text.strip()]
        href = img
        if not href.startswith('/'):
            href = req.theme.img_url(img)
        return formatter.image(src=href, alt=text, width=w, height=h)
    else:
        return formatter.text(text)


#############################################################################
### Quoting
#############################################################################

def quoteFilename(filename):
    """
    Return a simple encoding of filename in plain ascii.
    
    @param filename: the original filename, maybe containing non-ascii chars
    @rtype: string
    @return: the quoted filename, all special chars encoded in _XX
    """
    safe = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    res = list(filename)
    for i in range(len(res)):
        c = res[i]
        if c not in safe:
            res[i] = '_%02x' % ord(c)
    return ''.join(res)


def unquoteFilename(filename):
    """
    Return decoded original filename when given an encoded filename.
    
    @param filename: encoded filename
    @rtype: string
    @return: decoded, original filename
    """
    return urllib.unquote(filename.replace('_', '%'))


quoteWikiname = quoteFilename
unquoteWikiname = unquoteFilename


def escape(s, quote=None):
    """
    Replace special characters '&', '<' and '>' by SGML entities.
    (taken from cgi.escape so we don't have to include that, even if we don't use cgi at all)
    
    @param s: string to escape
    @param quote: if given, transform '\"' to '&quot;'
    @rtype: string
    @return: escaped version of string
    """
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
    return s


#############################################################################
### InterWiki
#############################################################################

_interwiki_list = None

def split_wiki(wikiurl):
    """
    Split a wiki url.
    
    @param wikiurl: the url to split
    @rtype: tuple
    @return: (tag, tail)
    """
    # !!! use a regex here!
    try:
        wikitag, tail = wikiurl.split(":", 1)
    except ValueError:
        try:
            wikitag, tail = wikiurl.split("/", 1)
        except ValueError:
            wikitag = None
            tail = None

    return (wikitag, tail)


def join_wiki(wikiurl, wikitail):
    """
    Add a page name to an interwiki url.
    
    @param wikiurl: wiki url, maybe including a $PAGE placeholder
    @param wikitail: page name
    @rtype: string
    @return: generated URL of the page in the other wiki
    """
    if wikiurl.find('$PAGE') == -1:
        return wikiurl + wikitail
    else:
        return wikiurl.replace('$PAGE', wikitail)


def resolve_wiki(request, wikiurl):
    """
    Resolve an interwiki link.
    
    @param request: the request object
    @param wikiurl: the InterWiki:PageName link
    @rtype: tuple
    @return: (wikitag, wikiurl, wikitail)
    """
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
                line = "%s %s/InterWiki" % (line, request.getScriptname()) 
                wikitag, urlprefix, trash = line.split(None, 2)
            except ValueError:
                pass
            else:
                _interwiki_list[wikitag] = urlprefix

        del lines

        # add own wiki as "Self" and by its configured name
        _interwiki_list['Self'] = request.getScriptname() + '/'
        if config.interwikiname:
            _interwiki_list[config.interwikiname] = request.getScriptname() + '/'

    # split wiki url
    wikitag, tail = split_wiki(wikiurl)

    # return resolved url
    if wikitag and _interwiki_list.has_key(wikitag):
        return (wikitag, _interwiki_list[wikitag], tail, False)
    else:
        return (wikitag, request.getScriptname(), "/InterWiki", True)


#############################################################################
### Page types (based on page names)
#############################################################################

def isSystemPage(request, pagename):
    """
    Is this a system page? Uses AllSystemPagesGroup internally.
    
    @param request: the request object
    @param pagename: the page name
    @rtype: bool
    @return: true if page is a system page
    """
    return (request.dicts.has_member('SystemPagesGroup', pagename) or
        isTemplatePage(pagename) or isFormPage(pagename))


def isTemplatePage(pagename):
    """
    Is this a template page?
    
    @param pagename: the page name
    @rtype: bool
    @return: true if page is a template page
    """
    global _TEMPLATE_RE
    if _TEMPLATE_RE is None:
        _TEMPLATE_RE = re.compile(config.page_template_regex)
    return _TEMPLATE_RE.search(pagename) is not None


def isFormPage(pagename):
    """
    Is this a form page?
    
    @param pagename: the page name
    @rtype: bool
    @return: true if page is a form page
    """
    global _FORM_RE
    if _FORM_RE is None:
        _FORM_RE = re.compile(config.page_form_regex)
    return _FORM_RE.search(pagename) is not None


def filterCategoryPages(pagelist):
    """
    Return a copy of `pagelist` that only contains category pages.

    If you pass a list with a single pagename, either that is returned
    or an empty list, thus you can use this function like a `isCategoryPage`
    one.
       
    @param pagelist: a list of (one or some or all) pages
    @rtype: list
    @return: only the category pages of pagelist
    """
    global _CATEGORY_RE
    if _CATEGORY_RE is None:
        _CATEGORY_RE = re.compile(config.page_category_regex)
    return filter(_CATEGORY_RE.search, pagelist)


#############################################################################
### Page storage helpers
#############################################################################

def getPageList(text_dir):
    """
    List all pages, except for "CVS" directories,
    hidden files (leading '.') and temp files (leading '#')
    
    @param text_dir: path to "text" directory
    @rtype: list
    @return: all (unquoted) wiki page names
    """
    pages = os.listdir(text_dir)
    result = []
    for file in pages:
        if file[0] in ['.', '#'] or file in ['CVS']: continue
        result.append(file)
    return map(unquoteFilename, result)


def getPageDict(text_dir):
    """
    Return a dictionary of page objects for all pages,
    with the page name as the key.
       
    @param text_dir: path to "text" directory
    @rtype: dict
    @return: all pages {pagename: Page, ...}
    """
    from MoinMoin.Page import Page
    pages = {}
    pagenames = getPageList(text_dir)
    for name in pagenames:
        pages[name] = Page(name)
    return pages


def getBackupList(backup_dir, pagename=None):
    """
    Get a filename list of older versions of the page, sorted by date
    in descending order (last change first).

    @param backup_dir: the path of the "backup" directory
    @param pagename: the (unquoted) page name or None, when all backup
                     versions shall be returned
    @rtype: list
    @return: backup file names (quoted!)
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


def getSysPage(request, pagename):
    """
    Get a system page according to user settings and available translations.
    
    @param request: the request object
    @param pagename: the name of the page
    @rtype: string
    @return: the (possibly translated) name of that system page
    """
    from MoinMoin.Page import Page

    i18n_name = request.getText(pagename)
    if i18n_name != pagename:
        i18n_page = Page(i18n_name)
        if i18n_page.exists():
            return i18n_page
    return Page(pagename)


def getHomePage(request, username=None):
    """
    Get a user's homepage, or return None for anon users and
    those who have not created a homepage.
    
    @param request: the request object
    @param username: the user's name
    @rtype: Page
    @return: user's homepage object - or None
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
    """
    Get full path to a page-specific storage area. `args` can
    contain additional path components that are added to the base path.

    @param pagename: the page name
    @param args: additional path components
    @keyword check_create: ensures that the page storage area exists, excluding
                           the additional path components (default is true).
    @rtype: string
    @return: the full path to the storage area
    """
    pagename = quoteFilename(pagename)

    path = os.path.join(config.data_dir, "pages", pagename)
    if kw.get('check_create', 1) and not os.path.exists(path): 
        filesys.makeDirs(path)

    return os.path.join(*((path,) + args))


def AbsPageName(context, pagename):
    """
    Return the absolute pagename for a (possibly) relative pagename.

    @param context: name of the page where "pagename" appears on
    @param pagename: the (possibly relative) page name
    @rtype: string
    @return: the absolute page name
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
    """
    Search the text of all pages for "needle".

    @param needle: the expression we want to search for
    @keyword literal: 0: try to treat "needle" as a regex
                      1: "needle" is definitely NOT a regex
    @keyword case: 1: case-sensitive search
    @keyword context: if != 0: provide `context` chars of text on each side of a hit.
    @rtype: tuple
    @return: (number of pages, hits).
        `hits` is a list of tuples containing the number of hits on a page
        and the pagename. When context>0, a list of triples with the text of
        the hit and the text on each side of it is added; otherwise, the
        third element is None.
    """
    from MoinMoin.Page import Page

    literal = kw.get('literal', 0)
    context = int(kw.get('context', 0))
    ignorecase = int(kw.get('case', 0)) == 0 and re.IGNORECASE or 0

    if literal and context:
        needle_re = re.compile(re.escape(needle), ignorecase)
    elif literal:
        if ignorecase:
            needle = needle.lower()
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
                    body = body.lower()
                count = body.count(needle)
            else:
                count = len(needle_re.findall(body))
            if count:
                hits.append((count, page_name, None))

    # we sort:
    # 1. by descending number of hits
    # 2. by ascending name of page
    hits.sort( lambda x,y: cmp((y[0], x[1]), (x[0], y[1])) )

    return (len(all_pages), hits)


#############################################################################
### Plugins
#############################################################################

def importPlugin(kind, name, function="execute"):
    """
    Returns an object from a plugin module or None if module or 'function' is not found
    kind may be one of 'action', 'formatter', 'macro', 'processor', 'parser'
    or any other directory that exist in MoinMoin or data/plugin
    
    @param kind: what kind of module we want to import
    @param name: the name of the module
    @param function: the function name
    @rtype: callable
    @return: "function" of module "name" of kind "kind"
    """
    # First try data/plugins
    result = pysupport.importName("plugin." + kind + "." + name, function)
    if result == None:
        # then MoinMoin
        result = pysupport.importName("MoinMoin." + kind + "." + name, function)
    return result

def builtinPlugins(kind):
    """
    Gets a list of modules in MoinMoin.'kind'
    
    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    plugins =  pysupport.importName("MoinMoin." + kind, "modules")
    if plugins == None:
        return []
    else:
        return plugins

def extensionPlugins(kind):
    """
    Gets a list of modules in data/plugin/'kind'
    
    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    plugins =  pysupport.importName("plugin." + kind, "modules")
    if plugins == None:
        return []
    else:
        return plugins


def getPlugins(kind):
    """
    Gets a list of module names.
    
    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    builtin_plugins = builtinPlugins(kind)
    extension_plugins = extensionPlugins(kind)[:] # use a copy to not destroy the value
    for module in builtin_plugins:
        if module not in extension_plugins:
            extension_plugins.append(module)
    return extension_plugins

#############################################################################
### Misc
#############################################################################

def parseAttributes(request, attrstring, endtoken=None, extension=None):
    """
    Parse a list of attributes and return a dict plus a possible
    error message.
    If extension is passed, it has to be a callable that returns
    None when it was not interested into the token, '' when all was OK
    and it did eat the token, and any other string to return an error
    message.
    
    @param request: the request object
    @param attrstring: string containing the attributes to be parsed
    @param endtoken: token terminating parsing
    @param extension: extension function -
                      gets called with the current token, the parser and the dict
    @rtype: dict, msg
    @return: a dict plus a possible error message
    """
    import shlex, cStringIO

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

        key = escape(key) # make sure nobody cheats

        # safely escape and quote value
        if val[0] in ["'", '"']:
            val = escape(val)
        else:
            val = '"%s"' % escape(val, 1)

        attrs[key.lower()] = val

    return attrs, msg or ''


def taintfilename(basename):
    """
    Make a filename that is supposed to be a plain name secure, i.e.
    remove any possible path components that compromise our system.
    
    @param basename: (possibly unsafe) filename
    @rtype: string
    @return: (safer) filename
    """
    basename = basename.replace(os.pardir, '_')
    basename = basename.replace(':', '_')
    basename = basename.replace('/', '_')
    basename = basename.replace('\\', '_')
    return basename


def mapURL(url):
    """
    Map URLs according to 'config.url_mappings'.
    
    @param url: a URL
    @rtype: string
    @return: mapped URL
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
    """
    Return a group letter for `name`, which must be a unicode string.
    Currently supported: Hangul Syllables (U+AC00 - U+D7AF)
    
    @param name: a string
    @rtype: string
    @return: group letter or None
    """
    if u'\uAC00' <= name[0] <= u'\uD7AF': # Hangul Syllables
        return unichr(0xac00 + (int(ord(name[0]) - 0xac00) / 588) * 588)
    else:
        return None


def isUnicodeName(name):
    """
    Try to determine if the quoted wikiname is a special, pure unicode name.
    
    @param name: a string
    @rtype: bool
    @return: true if name is a pure unicode name
    """
    # escape name if not escaped
    text = name
    if not name.count('_'):
        text = quoteWikiname(name)

    # check if every character is escaped
    return len(text.replace('_','')) == len(text) * 2/3


def isStrictWikiname(name, word_re=re.compile(r"^(?:[%(u)s][%(l)s]+){2,}$" % {'u':config.upperletters, 'l':config.lowerletters})):
    """
    Check whether this is NOT an extended name.
    
    @param name: the wikiname in question
    @rtype: bool
    @return: true if name matches the word_re
    """
    return word_re.match(name)


def isPicture(url):
    """
    Is this a picture's url?
    
    @param url: the url in question
    @rtype: bool
    @return: true if url points to a picture
    """
    extpos = url.rfind(".")
    return extpos > 0 and url[extpos:].lower() in ['.gif', '.jpg', '.jpeg', '.png']


def link_tag(request, params, text=None, formatter=None, **kw):
    """
    Create a link.

    @param request: the request object
    @param params: parameter string appended to the URL after the scriptname/
    @param text: text / inner part of the <a>...</a> link
    @param formatter: the formatter object to use
    @keyword attrs: additional attrs (HTMLified string)
    @rtype: string
    @return: formatted link tag
    """
    css_class = kw.get('css_class', None)
    if text is None:
        text = params # default
    if formatter:
        return formatter.url("%s/%s" % (request.getScriptname(), params), text, css_class, **kw)
    attrs = ''
    if kw.has_key('attrs'):
        attrs += ' ' + kw['attrs']
    if css_class:
        attrs += ' class="%s"' % css_class
    return ('<a%s href="%s/%s">%s</a>' % (attrs, request.getScriptname(), params, text))


def linediff(oldlines, newlines, **kw):
    """
    Find changes between oldlines and newlines.
    
    @param oldlines: list of old text lines
    @param newlines: list of new text lines
    @keyword ignorews: if 1: ignore whitespace
    @rtype: list
    @return: lines like diff tool does output.
    """
    false = lambda s: None 
    if kw.get('ignorews', 0):
        d = difflib.Differ(false)
    else:
        d = difflib.Differ(false, false)

    lines = list(d.compare(oldlines,newlines))
 
    # return empty list if there were no changes
    changed = 0
    for l in lines:
        if l[0] != ' ':
            changed = 1
            break
    if not changed: return []

    if not "we want the unchanged lines, too":
        if "no questionmark lines":
            lines = filter(lambda line : line[0]!='?', lines)
        return lines


    # calculate the hunks and remove the unchanged lines between them
    i = 0              # actual index in lines
    count = 0          # number of unchanged lines
    lcount_old = 0     # line count old file
    lcount_new = 0     # line count new file
    while i < len(lines):
        marker = lines[i][0]
        if marker == ' ':
            count = count + 1
            i = i + 1
            lcount_old = lcount_old + 1
            lcount_new = lcount_new + 1
        elif marker in ['-', '+']:
            if (count == i) and count > 3:
                lines[:i-3] = []
                i = 4
                count = 0
            elif count > 6:
                # remove lines and insert new hunk indicator
                lines[i-count+3:i-3] = ['@@ -%i, +%i @@\n' %
                                        (lcount_old, lcount_new)]
                i = i - count + 8
                count = 0
            else:
                count = 0
                i = i + 1                            
            if marker == '-': lcount_old = lcount_old + 1
            else: lcount_new = lcount_new + 1
        elif marker == '?':
            lines[i:i+1] = []

    # remove unchanged lines a the end
    if count > 3:
        lines[-count+3:] = []
    
    return lines


def pagediff(page1, page2, **kw):
    """
    Calculate the "diff" between `page1` and `page2`.

    @param page1: first page
    @param page2: second page
    @keyword ignorews: if 1: ignore pure-whitespace changes.
    @rtype: tuple
    @return: (diff return code, page file name,
             backup page file name, list of lines of diff output)
    """
    lines1 = None
    lines2 = None
    try:
        fd = open(page1)
        lines1 = fd.readlines()
    finally:
        fd.close()
    try:
        fd = open(page2)
        lines2 = fd.readlines()
    finally:
        fd.close()

    if lines1 == None or lines2 == None:
        return -1, page1, page2, []
    
    lines = linediff(lines1,lines2,**kw)
    return 0, page1, page2, lines
 

#############################################################################
### Page header / footer
#############################################################################

def send_title(request, text, **keywords):
    """
    Output the page header (and title).
    
    @param request: the request object
    @param text: the title text
    @keyword link: URL for the title
    @keyword msg: additional message (after saving)
    @keyword pagename: 'PageName'
    @keyword print_mode: 1 (or 0)
    @keyword allow_doubleclick: 1 (or 0)
    @keyword html_head: additional <head> code
    @keyword body_attr: additional <body> attributes
    @keyword body_onload: additional "onload" JavaScript code
    """
    from MoinMoin import i18n
    from MoinMoin.Page import Page

    _ = request.getText
    pagename = keywords.get('pagename', None)

    # get name of system pages
    page_front_page = getSysPage(request, config.page_front_page).page_name
    page_help_contents = getSysPage(request, 'HelpContents').page_name
    page_title_index = getSysPage(request, 'TitleIndex').page_name
    page_word_index = getSysPage(request, 'WordIndex').page_name
    page_user_prefs = getSysPage(request, 'UserPreferences').page_name
    page_help_formatting = getSysPage(request, 'HelpOnFormatting').page_name
    page_find_page = getSysPage(request, 'FindPage').page_name

    # parent page?
    page_parent_page = None
    if pagename and config.allow_subpages:
        pos = pagename.rfind('/')
        if pos >= 0:
            pp = Page(pagename[:pos])
            if pp.exists():
                page_parent_page = pp.page_name

    # Print the HTML <head> element
    user_head = config.html_head
    if request.query_string or request.request_method == 'POST':
        user_head = user_head + config.html_head_queries
    if keywords.has_key('pi_refresh') and keywords['pi_refresh']:
        user_head = user_head + '<meta http-equiv="refresh" content="%(delay)d;URL=%(url)s">' % keywords['pi_refresh']
    request.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
%s
%s
%s
""" % (
        user_head,
        keywords.get('html_head', ''),
        request.theme.html_head({
            'title': escape(text),
            'sitename': escape(config.html_pagetitle or config.sitename),
            'print_mode': keywords.get('print_mode', False),
        })
    ))
# later: <html xmlns=\"http://www.w3.org/1999/xhtml\">

    # Links
    request.write('<link rel="Start" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_front_page)))
    if pagename:
        request.write('<link rel="Alternate" title="%s" href="%s/%s?action=raw">\n' % (
            _('Wiki Markup'), request.getScriptname(), quoteWikiname(pagename),))
        request.write('<link rel="Alternate" media="print" title="%s" href="%s/%s?action=print">\n' % (
            _('Print View'), request.getScriptname(), quoteWikiname(pagename),))

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
        #~         request.write('<link rel="First" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(all_pages[0]))
        #~         if pos > 0:
        #~             request.write('<link rel="Previous" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(all_pages[pos-1])))
        #~         if pos+1 < len(all_pages):
        #~             request.write('<link rel="Next" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(all_pages[pos+1])))
        #~         request.write('<link rel="Last" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(all_pages[-1])))

        if page_parent_page:
            request.write('<link rel="Up" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_parent_page)))

        from MoinMoin.action import AttachFile
        AttachFile.send_link_rel(request, pagename)

    request.write(
        '<link rel="Search" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_find_page)) +
        '<link rel="Index" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_title_index)) +
        '<link rel="Glossary" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_word_index)) +
        '<link rel="Help" href="%s/%s">\n' % (request.getScriptname(), quoteWikiname(page_help_formatting))
    )

    request.write("</head>\n")
    request.flush()

    # start the <body>
    bodyattr = ''
    if keywords.has_key('body_attr'):
        bodyattr += ' ' + keywords['body_attr']
    if keywords.get('allow_doubleclick', 0) and not keywords.get('print_mode', 0) \
            and pagename and request.user.may.edit(pagename) \
            and request.user.edit_on_doubleclick:
        bodyattr += ''' ondblclick="location.href='%s'"''' % (
            Page(pagename).url(request, "action=edit"))

    # Set body to the user interface language and direction
    bodyattr += ' %s' % request.theme.ui_lang_attr()
    
    body_onload = keywords.get('body_onload', '')
    if body_onload:
        bodyattr += ''' onload="%s"''' % body_onload
    request.write('\n<body%s>\n' % bodyattr)

    # if in Print mode, emit the title and return immediately
    if keywords.get('print_mode', 0):
        ## print '<h1>%s</h1><hr>\n' % (escape(text),)
        return

    navibar = None
    quicklinks = request.user.getQuickLinks()
    if config.navi_bar or quicklinks:
        # Print quicklinks
        if not quicklinks:
            for navi_link in config.navi_bar:
                newwin = ''
                if navi_link.startswith('^'):
                    newwin = '^'
                    navi_link = navi_link[1:]
                if not navi_link.startswith('['):
                    # copy real links verbatim, try to map system pages else
                    navi_link = getSysPage(request, navi_link).page_name
                quicklinks.append(newwin + navi_link)

        navibar = []
        for navi_link in quicklinks:
            if navi_link.startswith('[^'):
                navi_link = '[' + navi_link[2:]
            elif navi_link.startswith('^'):
                navi_link = navi_link[1:]

            if navi_link.startswith('[') and navi_link.endswith(']'):
                try:
                    link, navi_link = navi_link[1:-1].split(' ', 1)
                except (ValueError, TypeError):
                    link = "#error"
                    navi_link = "Broken link: " + escape(navi_link)
                else:
                    # escape untrusted input!                   
                    link = escape(link, quote=1)
                    navi_link = escape(navi_link)
            else:
                link =  "%s/%s" % (request.getScriptname(), quoteWikiname(navi_link))

            navibar.append((link, navi_link,))

    hp = getHomePage(request)
    if hp:
        page_home_page = hp.page_name
    else:
        page_home_page = None
        
    # prepare dict for theme code:
    d = {
        'theme': request.theme.name,
        'script_name': request.getScriptname(),
        'title_text': text,
        'title_link': keywords.get('link', ''),
        'logo_string': config.logo_string,
        'site_name': config.sitename,
        'page_name': pagename or '',
        'page_find_page': page_find_page,
        'page_front_page': page_front_page,
        'page_home_page': page_home_page,
        'page_help_contents': page_help_contents,
        'page_help_formatting': page_help_formatting,
        'page_parent_page': page_parent_page,
        'page_title_index': page_title_index,
        'page_word_index': page_word_index,
        'page_user_prefs': page_user_prefs,
        'user_name': request.user.name,
        'user_valid': request.user.valid,
        'user_prefs': (page_user_prefs, request.user.name)[request.user.valid],
        'navibar': navibar,
        'msg': keywords.get('msg', ''),
        'trail': keywords.get('trail', None),
    }
    # add quoted versions of pagenames
    newdict = {}
    for key in d:
        if key.startswith('page_'):
            if d[key]:
                newdict['q_'+key] = quoteWikiname(d[key])
            else:
                newdict['q_'+key] = None
    d.update(newdict)

    # now call the theming code to do the rendering
    request.write(request.theme.header(d))
    
    # emit it
    request.flush()


def send_footer(request, pagename, mod_string=None, **keywords):
    """
    Output the page footer.

    @param request: the request object
    @param pagename: WikiName of the page
    @param mod_string: "last modified" date
    @keyword editable: true, when page is editable (default: true)
    @keyword showpage: true, when link back to page is wanted (default: false)
    @keyword print_mode: true, when page is displayed in Print mode
    """
    from MoinMoin import i18n
    from MoinMoin.Page import Page

    _ = request.getText
    page = Page(pagename)

    page_find_page = getSysPage(request, 'FindPage').page_name

    form = keywords.get('form', None)
    icon = request.theme.get_icon('searchbutton')
    searchfield = (
        '<input type="text" name="text_%%(type)s" value="%%(value)s" size="15" maxlength="50">'
        '<input type="image" src="%(src)s" name="button_%%(type)s" alt="%(alt)s">'
        ) % {
            'alt': icon[0],
            'src': icon[1],
        }
    titlesearch = searchfield % {
        'type': 'title',
        'value': escape(form and form.get('text_title', [''])[0] or '', 1),
    }
    textsearch = searchfield %  {
        'type': 'full',
        'value': escape(form and form.get('text_full', [''])[0] or '', 1),
    }

    # list user actions that start with an uppercase letter
    available_actions = []
    if keywords.get('showactions', 1):
        from MoinMoin.wikiaction import getPlugins
        from MoinMoin.action import extension_actions
        dummy, actions = getPlugins()
        actions.extend(extension_actions)
        actions.sort()
        
        for action in actions:
            if action[0] != action[0].upper(): continue
            available_actions.append(action)

    # prepare dict for theme code:
    d = {
        'theme': request.theme.name,
        'script_name': request.getScriptname(),
        'site_name': config.sitename,
        'page_name': pagename,
        'page_find_page': page_find_page,
        'pagesize': page.size(),
        'last_edit_info': mod_string or '',
        'titlesearch': titlesearch,
        'textsearch': textsearch,
        'page': page,
        'footer_fragments': request._footer_fragments,
        'available_actions': available_actions,
    }
    # add quoted versions of pagenames
    newdict = {}
    for key in d:
        if key.startswith('page_'):
            if d[key]:
                newdict['q_'+key] = quoteWikiname(d[key])
            else:
                newdict['q_'+key] = None
    d.update(newdict)

    request.write('\n\n') # the content does not always end with a newline
    request.write(request.theme.footer(d, **keywords))
    

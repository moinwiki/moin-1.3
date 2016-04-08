"""
    MoinMoin - Page class

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Page.py,v 1.119 2002/04/25 19:32:30 jhermann Exp $
"""

# Imports
import cStringIO, os, re, sys, string, urllib
from MoinMoin import caching, config, user, util, wikiutil, webapi
from MoinMoin.i18n import _


#############################################################################
### Page - Manage a page associated with a WikiName
#############################################################################
class Page:
    """ An immutable wiki page.

        To change a page's content, use the PageEditor class.
    """

    _SPLIT_RE = re.compile('([%s])([%s])' % (config.lowerletters, config.upperletters))


    def __init__(self, page_name, **keywords):
        """ Create page object.

            Note that this is a 'lean' operation, since the text for the page
            is loaded on demand. Thus, things like `Page(name).link_to()` are
            efficient.

            **page_name** -- WikiName of the page
            **keywords** --
                date: date of older revision
                formatter: formatter instance
        """
        self.page_name = page_name
        self.prev_date = keywords.get('date')
        self.raw_body = None

        if keywords.has_key('formatter'):
            self.formatter = keywords.get('formatter')
            self.default_formatter = 0
        else:
            self.default_formatter = 1


    def split_title(self, force=0):
        """ Return a string with the page name split by spaces, if
            the user wants that.
        """
        if not force and not user.current.wikiname_add_spaces: return self.page_name
    
        # look for the end of words and the start of a new word,
        # and insert a space there
        return self._SPLIT_RE.sub(r'\1 \2', self.page_name)


    def _split_title_py16(self, force=0):
        """ Return a string with the page name split by spaces, if
            the user wants that.
        """
        if not force and not user.current.wikiname_add_spaces: return self.page_name
    
        # Provided by Magnus Lyckå
        # Note that "upperletters" HAS to start with "A-Z"
        # This is a quickfix, and not worth any more effort
        temp = [self.page_name[0]]
        ucase = string.uppercase + config.upperletters[3:]
        for letter in self.page_name[1:]:
            if letter in ucase:
                temp.append(' ')
            temp.append(letter)
        return string.join(temp,'')


    def _text_filename(self):
        """The name of the page file, possibly of an older page"""
        if self.prev_date:
            return os.path.join(config.backup_dir, wikiutil.quoteFilename(self.page_name) + "." + self.prev_date)
        else:
            return os.path.join(config.text_dir, wikiutil.quoteFilename(self.page_name))


    def _tmp_filename(self):
        """The name of the temporary file used while saving"""
        return os.path.join(config.text_dir, ('#' + wikiutil.quoteFilename(self.page_name) + '.' + `os.getpid()` + '#'))


    def exists(self):
        """True if the page exists"""
        return os.path.exists(self._text_filename())


    def size(self):
        """Return page size"""
        if self.raw_body is not None:
            return len(self.raw_body)
        
        return os.path.getsize(self._text_filename())


    def url(self, querystr=None):
        """ Return an URL for this page.
        """
        url = "%s/%s" % (webapi.getScriptname(), wikiutil.quoteWikiname(self.page_name))
        if querystr: url = "%s?%s" % (url, string.replace(querystr, '&', '&amp;'))
        return url


    def link_to(self, text=None, querystr=None, anchor=None):
        """Return HTML markup that links to this page"""
        text = text or self.split_title()
        fmt = getattr(self, 'formatter', None)
        url = wikiutil.quoteWikiname(self.page_name)
        if querystr: url = "%s?%s" % (url, string.replace(querystr, '&', '&amp;'))
        if anchor: url = "%s#%s" % (url, urllib.quote_plus(anchor))
        if self.exists():
            return wikiutil.link_tag(url, text, formatter=fmt)
        elif user.current.show_nonexist_qm:
            return wikiutil.link_tag(url,
                '?', 'nonexistent', formatter=fmt) + text
        else:
            return wikiutil.link_tag(url, text, 'nonexistent', formatter=fmt)


    def get_raw_body(self):
        """Load the raw markup from the page file"""
        if self.raw_body is not None:
            return self.raw_body

        # try to open file
        try:
            file = open(self._text_filename(), 'rb')
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty text (note that we
                # never store empty pages, so this is detectable and also
                # safe when passed to a function expecting a string)
                return ""
            else:
                raise er

        # read file content and make sure it is closed properly
        try:
            result = file.read()
        finally:
            file.close()

        return result


    def send_page(self, request, msg=None, **keywords):
        """ Send the formatted page to stdout.

            **form** -- CGI-Form
            **msg** -- if given, display message in header area
            **keywords** --
                content_only: 1 to omit page header and footer
                count_hit: add an event to the log
        """
        request.clock.start('send_page')
        import cgi
        form = request.form

        # determine modes
        print_mode = form.has_key('action') and form['action'].value == 'print'
        content_only = keywords.get('content_only', 0)
        self.hilite_re = keywords.get('hilite_re', None)
        if msg is None: msg = ""

        # count hit?
        if keywords.get('count_hit', 0):
            request.getEventLogger().add('VIEWPAGE', {'pagename': self.page_name})

        # load the text
        body = self.get_raw_body()

        # if necessary, load the default formatter
        if self.default_formatter:
            from formatter.text_html import Formatter
            self.formatter = Formatter(request, store_pagelinks=1)
        self.formatter.setPage(self)

        # default is wiki markup
        pi_format = config.default_markup or "wiki"
        pi_redirect = None
        pi_formtext = []
        pi_formfields = []
        wikiform = None

        # check for XML content
        if body and body[:5] == '<?xml':
            pi_format = "xslt"

        # check processing instructions
        while body and body[0] == '#':
            # extract first line
            try:
                line, body = string.split(body, '\n', 1)
            except ValueError:
                line = body
                body = ''

            # skip comments (lines with two hash marks)
            if line[1] == '#': continue

            # parse the PI
            verb, args = string.split(line[1:]+' ', ' ', 1)
            verb = string.lower(verb)
            args = string.strip(args)

            # check the PIs
            if verb == "format":
                # markup format
                pi_format = string.lower(args)
            elif verb == "redirect":
                # redirect to another page
                # note that by including "action=show", we prevent
                # endless looping (see code in "cgimain") or any
                # cascaded redirection
                pi_redirect = args
                if form.has_key('action') or form.has_key('redirect') or content_only: continue

                webapi.http_redirect(request, '%s/%s?action=show&redirect=%s' % (
                    webapi.getScriptname(),
                    wikiutil.quoteWikiname(pi_redirect),
                    urllib.quote_plus(self.page_name, ''),))
                return
            elif verb == "deprecated":
                # deprecated page, append last backup version to current contents
                # (which should be a short reason why the page is deprecated)
                msg = '%s<b>%s</b><br>%s' % (
                    wikiutil.getSmiley('/!\\', self.formatter),
                    _('The backupped content of this page is deprecated and will not be included in search results!'),
                    msg)

                oldversions = wikiutil.getBackupList(config.backup_dir, self.page_name)
                if oldversions:
                    oldfile = oldversions[0]
                    olddate = os.path.basename(oldfile)[len(wikiutil.quoteFilename(self.page_name))+1:]
                    oldpage = Page(self.page_name, date=olddate)
                    body = body + oldpage.get_raw_body()
                    del oldfile
                    del olddate
                    del oldpage
            elif verb == "pragma":
                # store a list of name/value pairs for general use
                try:
                    key, val = string.split(args, ' ', 1)
                except (ValueError, TypeError):
                    pass
                else:
                    request.setPragma(key, val)
            elif verb == "form":
                # ignore form PIs on non-form pages
                if not wikiutil.isFormPage(self.page_name):
                    continue

                # collect form definitions
                if not wikiform:
                    from MoinMoin import wikiform
                    pi_formtext.append('<table border="1" cellspacing="1" cellpadding="3">\n'
                        '<form method="POST" action="%s">\n'
                        '<input type="hidden" name="action" value="formtest">\n' % self.url())
                pi_formtext.append(wikiform.parseDefinition(args, pi_formfields))
            else:
                # unknown PI ==> end PI parsing
                break

        # start document output
        doc_leader = self.formatter.startDocument(self.page_name)
        if not content_only:
            # send the document leader
            webapi.http_headers(request)
            sys.stdout.write(doc_leader)

            # send the page header
            if self.default_formatter:
                page_needle = self.page_name
                if config.allow_subpages and string.count(page_needle, '/'):
                    page_needle = '/' + string.split(page_needle, '/')[-1]
                link = '%s/%s?action=fullsearch&value=%s&literal=1&case=1' % (
                    webapi.getScriptname(),
                    wikiutil.quoteWikiname(self.page_name),
                    urllib.quote_plus(page_needle, ''))
                title = self.split_title()
                if self.prev_date:
                    msg = "<b>%s</b><br>%s" % (
                        _('Version as of %(date)s') % {'date':
                            user.current.getFormattedDateTime(os.path.getmtime(self._text_filename()))},
                        msg)
                if form.has_key('redirect'):
                    redir = form['redirect'].value
                    msg = '%s<b>%s</b><br>%s' % (
                        wikiutil.getSmiley('/!\\', self.formatter),
                        _('Redirected from page "%(page)s"') % {'page':
                            wikiutil.link_tag(wikiutil.quoteWikiname(redir) + "?action=show", redir)},
                        msg)
                if pi_redirect:
                    msg = '%s<b>%s</b><br>%s' % (
                        wikiutil.getSmiley('<!>', self.formatter),
                        _('This page redirects to page "%(page)s"') % {'page': pi_redirect},
                        msg)
                wikiutil.send_title(title, link=link, msg=msg,
                    pagename=self.page_name, print_mode=print_mode,
                    allow_doubleclick=1)

                # page trail?
                if not print_mode and user.current.valid:
                    user.current.addTrail(self.page_name)
                    trail = user.current.getTrail()
                    if trail and user.current.show_page_trail:
                        delim = '&gt;'
                        if string.lower(config.charset) == 'iso-8859-1':
                            delim = '»'
                        print '<font face="Verdana" size="-1">%s&nbsp;%s %s</font><hr>' % (
                            string.join(
                                map(lambda p: Page(p).link_to(), trail[:-1]),
                                "&nbsp;%s " % delim),
                            delim, cgi.escape(trail[-1]))

                # user-defined form preview?
                if pi_formtext:
                    pi_formtext.append('<input type="hidden" name="fieldlist" value="%s">\n' %
                        string.join(pi_formfields, "|"))
                    pi_formtext.append('</form></table>\n')
                    pi_formtext.append(_(
                        '<p><small>If you submit this form, the submitted values'
                        ' will be displayed.\nTo use this form on other pages, insert a\n'
                        '<br><br><b><tt>&nbsp;&nbsp;&nbsp;&nbsp;'
                        '[[Form("%(pagename)s")]]'
                        '</tt></b><br><br>\n'
                        'macro call.</b></small></p>\n'
                    ) % {'pagename': self.page_name[:-len(config.page_form_ending)]})
                    print string.join(pi_formtext, '')

        # try to load the parser
        Parser = util.importName("MoinMoin.parser." + pi_format, "Parser")
        if Parser is None:
            # default to plain text formatter (i.e. show the page source)
            del Parser
            from parser.plain import Parser

        # new page?
        if not self.exists() and self.default_formatter and not content_only:
            # generate the default page content for new pages
            print wikiutil.link_tag(wikiutil.quoteWikiname(self.page_name)+'?action=edit',
                _("Create this page"))

            # look for template pages
            templates = filter(lambda page, u = wikiutil: u.isTemplatePage(page),
                wikiutil.getPageList(config.text_dir))
            if templates:
                print self.formatter.paragraph(1)
                print self.formatter.text(_('Alternatively, use one of these templates:'))
                print self.formatter.paragraph(0)

                # send list of template pages
                print self.formatter.bullet_list(1)
                for page in templates:
                    print self.formatter.listitem(1)
                    print wikiutil.link_tag("%s?action=edit&template=%s" % (
                            wikiutil.quoteWikiname(self.page_name),
                            wikiutil.quoteWikiname(page)),
                        page)
                    print self.formatter.listitem(0)
                print self.formatter.bullet_list(0)

            print self.formatter.paragraph(1)
            print self.formatter.text(_('To create you own templates, ' +
                'add a page with a name ending in Template.'))
            print self.formatter.paragraph(0)
        else:
            # parse the text and send the page content
            Parser(body, request).format(self.formatter, form)

            # check for pending footnotes
            if getattr(request, 'footnotes', None):
                from MoinMoin.macro.FootNote import emit_footnotes
                print self.formatter.linebreak(0)
                print emit_footnotes(request, self.formatter)

        # end document output
        doc_trailer = self.formatter.endDocument()
        if not content_only:
            # send the page footer
            if self.default_formatter and not print_mode:
                wikiutil.send_footer(request, self.page_name, self._last_modified(),
                    print_mode=print_mode)

            sys.stdout.write(doc_trailer)

        # cache the pagelinks
        if self.default_formatter and self.exists():
            arena = "pagelinks"
            key   = wikiutil.quoteFilename(self.page_name)
            cache = caching.CacheEntry(arena, key)
            if cache.needsUpdate(self._text_filename()):
                links = self.formatter.pagelinks
                links.sort()
                cache.update(string.join(links, '\n'))

        request.clock.stop('send_page')


    def _last_modified(self):
        if not self.exists():
            return None
        return user.current.getFormattedDateTime(os.path.getmtime(self._text_filename()))


    def getPageLinks(self, request):
        """Get a list of the links on this page"""
        if not self.exists(): return []

        arena = "pagelinks"
        key   = wikiutil.quoteFilename(self.page_name)
        cache = caching.CacheEntry(arena, key)
        if cache.needsUpdate(self._text_filename()):
            # this is normally never called, but is here to fill the cache
            # in existing wikis; thus, we do a "null" send_page here, which
            # is not efficient, but reduces code duplication
            stdout = sys.stdout
            sys.stdout = cStringIO.StringIO()
            try:
                try:
                    Page(self.page_name).send_page(request, content_only=1)
                except:
                    cache.update('')
            finally:
                sys.stdout = stdout
                if hasattr(request, '_fmt_hd_counters'):
                    del request._fmt_hd_counters

        return filter(None, string.split(cache.content(), '\n'))


# Python 1.6's "re" is buggy
if sys.version[:3] == "1.6":
    Page.split_title = Page._split_title_py16


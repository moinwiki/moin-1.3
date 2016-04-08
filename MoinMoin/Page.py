# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Page class

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import cStringIO, os, re, urllib, os.path, random
from MoinMoin import caching, config, user, util, wikiutil
#import MoinMoin.util.web
from MoinMoin.logfile import eventlog

class Page:
    """Page - Manage an (immutable) page associated with a WikiName.
       To change a page's content, use the PageEditor class.
    """

    _SPLIT_RE = re.compile('([%s])([%s])' % (config.lowerletters, config.upperletters))

    def __init__(self, page_name, **keywords):
        """
        Create page object.

        Note that this is a 'lean' operation, since the text for the page
        is loaded on demand. Thus, things like `Page(name).link_to()` are
        efficient.

        @param page_name: WikiName of the page
        @keyword date: date of older revision
        @keyword formatter: formatter instance
        """
        self.page_name = page_name
        self.prev_date = keywords.get('date')
        self._raw_body = None
        self._raw_body_modified = 0
        self.hilite_re = None
        
        if keywords.has_key('formatter'):
            self.formatter = keywords.get('formatter')
            self.default_formatter = 0
        else:
            self.default_formatter = 1


    def split_title(self, request, force=0):
        """
        Return a string with the page name split by spaces, if
        the user wants that.
        
        @param request: the request object
        @param force: if != 0, then force splitting the page_name
        @rtype: string
        @return: pagename of this page, splitted into space separated words
        """
        if not force and not request.user.wikiname_add_spaces: return self.page_name
    
        # look for the end of words and the start of a new word,
        # and insert a space there
        splitted = self._SPLIT_RE.sub(r'\1 \2', self.page_name)
        # also split at subpage separator
        return splitted.replace("/", "/ ")

    def _text_filename(self):
        """
        The name of the page file, possibly of an older page.
        
        @rtype: string
        @return: complete filename (including path) to this page
        """
        if self.prev_date:
            old_file = os.path.join(config.backup_dir, wikiutil.quoteFilename(self.page_name) + "." + self.prev_date)
            if os.path.exists(old_file):
                return old_file
#            if os.path.getmtime(os.path.join(config.text_dir, wikiutil.quoteFilename(self.page_name))) != self.prev_date:
#                os.errno = 2
#                raise OSError
        return os.path.join(config.text_dir, wikiutil.quoteFilename(self.page_name))


    def _tmp_filename(self):
        """
        The name of the temporary file used while saving.
        
        @rtype: string
        @return: temporary filename (complete path + filename)
        """
        rnd = random.randint(0,1000000000)
        return os.path.join(config.text_dir, ('#%s.%d#' % (wikiutil.quoteFilename(self.page_name), rnd)))


    def last_edit(self, request):
        """
        Return the last edit.
        This is used by wikirpc(2).py.
        
        @param request: the request object
        @rtype: dict
        @return: timestamp and editor information
        """
        if not self.exists():
            return None

        result = None
        if not self.prev_date: # we don't have a last-edited entry for backup versions        
            from MoinMoin.logfile import editlog
            try:
                log = editlog.EditLog(wikiutil.getPagePath(self.page_name, 'last-edited', check_create=0)).next()
            except StopIteration:
                log = None
            if log:
                editordata = log.getEditorData(request)
                editor = editordata[1]
                if editordata[0] == 'homepage':
                    editor = editordata[1].page_name
                result = {
                    'timestamp': log.ed_time,
                    'editor': editor,
                }
                del log
        if not result:
            timestamp = self.mtime()
            result = {
                'timestamp': timestamp,
                'editor': '?',
            }

        return result

    def _last_modified(self, request):
        """
        Return the last modified info.
        
        @param request: the request object
        @rtype: string
        @return: timestamp and editor information
        """
        if not self.exists():
            return None

        _ = request.getText
        
        result = None
        from MoinMoin.logfile import editlog
        try:
            log = editlog.EditLog(wikiutil.getPagePath
                                  (self.page_name, 'last-edited',
                                   check_create=0)).next()
        except StopIteration:
            log = None
        if log:
            result = _("(last edited %(time)s by %(editor)s)") % {
                'time': request.user.getFormattedDateTime(log.ed_time),
                'editor': log.getEditor(request),
            }
        del log

        return result or _("(last modified %s)") % request.user.getFormattedDateTime(
                os.path.getmtime(self._text_filename()))


    def isWritable(self):
        """
        Can this page be changed?
        
        @rtype: bool
        @return: true, if this page is writable or does not exist
        """
        return os.access(self._text_filename(), os.W_OK) or not self.exists()


    def exists(self):
        """
        Does this page exist?
        
        @rtype: bool
        @return: true, if page exists
        """
        return os.path.exists(self._text_filename())


    def size(self):
        """
        Get Page size.
        
        @rtype: int
        @return: page size, 0 for non-existent pages.
        """
        if self._raw_body is not None:
            return len(self._raw_body)

        try:
            return os.path.getsize(self._text_filename())
        except EnvironmentError, e:
            import errno
            if e.errno == errno.ENOENT: return 0
            raise

    def mtime(self):
        """
        Get modification timestamp of this page.
        
        @rtype: int
        @return: mtime of page (or 0 if page does not exist)
        """
        try:
            return os.path.getmtime(self._text_filename())
        except EnvironmentError, e:
            import errno
            if e.errno == errno.ENOENT: return 0
            raise

    def mtime_printable(self, request):
        """
        Get printable modification timestamp of this page.
        
        @rtype: string
        @return: formatted string with mtime of page
        """
        t = self.mtime()
        if not t:
            result = "0" # TODO: i18n, "Ever", "Beginning of time"...?
        else:
            result = request.user.getFormattedDateTime(t)
        return result
    
    def get_raw_body(self):
        """
        Load the raw markup from the page file.
        
        @rtype: string
        @return: raw page contents of this page
        """
        if self._raw_body is None:
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
                self.set_raw_body(file.read())
            finally:
                file.close()

        return self._raw_body


    def set_raw_body(self, body, modified=0):
        """
        Set the raw body text (prevents loading from disk).

        @param body: raw body text
        @param modified: 1 means that we internally modified the raw text and
                         that it is not in sync with the page file on disk.
                         This is used e.g. by PageEditor when previewing the page.
        """
        self._raw_body = body
        self._raw_body_modified = modified

    def url(self, request, querystr=None):
        """
        Return an URL for this page.

        @param request: the request object
        @param querystr: the query string to add after a "?" after the url
        @rtype: string
        @return: complete url of this page (including query string if specified)
        """
        url = "%s/%s" % (request.getScriptname(), wikiutil.quoteWikiname(self.page_name))
        if querystr:
            querystr = util.web.makeQueryString(querystr)
            url = "%s?%s" % (url, querystr)
        return url


    def link_to(self, request, text=None, querystr=None, anchor=None, **kw):
        """
        Return HTML markup that links to this page.
        See wikiutil.link_tag() for possible keyword parameters.

        @param request: the request object
        @param text: inner text of the link
        @param querystr: the query string to add after a "?" after the url
        @param anchor: if specified, make a link to this anchor
        @keyword attachment_indicator: if 1, add attachment indicator after link tag
        @keyword css_class: css class to use
        @rtype: string
        @return: formatted link
        """
        text = text or self.split_title(request)
        fmt = getattr(self, 'formatter', None)
        url = wikiutil.quoteWikiname(self.page_name)
        #that makes problems with moin_dump, thus commented out:
        #url = url.replace('_2f', '/')
        if querystr:
            querystr = util.web.makeQueryString(querystr)
            url = "%s?%s" % (url, querystr)
        if anchor: url = "%s#%s" % (url, urllib.quote_plus(anchor))

        # create a link to attachments if any exist
        attach_link = ''
        if kw.get('attachment_indicator', 0):
            from MoinMoin.action import AttachFile
            attach_link = AttachFile.getIndicator(request, self.page_name)

        if self.exists():
            return wikiutil.link_tag(request, url, text, formatter=fmt, **kw) + attach_link
        elif request.user.show_nonexist_qm:
            kw['css_class'] = 'nonexistent'
            return wikiutil.link_tag(request, url,
                '?', formatter=fmt, **kw) + text + attach_link
        else:
            kw['css_class'] = 'nonexistent'
            return wikiutil.link_tag(request, url, text, formatter=fmt, **kw) + attach_link


    def getSubscribers(self, request, **kw):
        """
        Get all subscribers of this page.

        @param request: the request object
        @keyword include_self: if 1, include current user (default: 0)
        @keyword return_users: if 1, return user instances (default: 0)
        @rtype: dict
        @return: lists of subscribed email addresses in a dict by language key
        """
        include_self = kw.get('include_self', 0)
        return_users = kw.get('return_users', 0)

        # extract categories of this page
        pageList = self.getCategories(request)
        
        # add current page name for list matching
        pageList.append(self.page_name)

        if config.SecurityPolicy:
            UserPerms = config.SecurityPolicy
        else:
            from security import Default as UserPerms

        # get email addresses of the all wiki user which have a profile stored;
        # add the address only if the user has subscribed to the page and
        # the user is not the current editor
        userlist = user.getUserList()
        emails = {}
        for uid in userlist:
            if uid == request.user.id and not include_self: continue # no self notification
            subscriber = user.User(request, uid)
            if not subscriber.email: continue # skip empty email address

            if not UserPerms(subscriber).read(self.page_name): continue

            if subscriber.isSubscribedTo(pageList):                
                lang = subscriber.language or 'en'
                if not emails.has_key(lang): emails[lang] = []
                if return_users:
                    emails[lang].append(subscriber)
                else:
                    emails[lang].append(subscriber.email) 

        return emails


    def send_page(self, request, msg=None, **keywords):
        """
        Output the formatted page.

        @param request: the request object
        @param msg: if given, display message in header area
        @keyword content_only: if 1, omit page header and footer
        @keyword count_hit: if 1, add an event to the log
        @keyword hilite_re: a regular expression for highlighting e.g. search results
        """
        request.clock.start('send_page')
        _ = request.getText

        # determine modes
        print_mode = request.form.has_key('action') and request.form['action'][0] == 'print'
        content_only = keywords.get('content_only', 0)
        content_id = keywords.get('content_id', 'content')
        self.hilite_re = keywords.get('hilite_re', None)
        if msg is None: msg = ""

        # count hit?
        if keywords.get('count_hit', 0):
            eventlog.EventLog().add(request, 'VIEWPAGE', {'pagename': self.page_name})

        # load the text
        body = self.get_raw_body()

        # if necessary, load the default formatter
        if self.default_formatter:
            from MoinMoin.formatter.text_html import Formatter
            self.formatter = Formatter(request, store_pagelinks=1)
        self.formatter.setPage(self)
        request.formatter = self.formatter

        # default is wiki markup
        pi_format = config.default_markup or "wiki"
        pi_redirect = None
        pi_refresh = None
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
                line, body = body.split('\n', 1)
            except ValueError:
                line = body
                body = ''

            # end parsing on empty (invalid) PI
            if line == "#":
                body = line + '\n' + body
                break

            # skip comments (lines with two hash marks)
            if line[1] == '#': continue

            # parse the PI
            verb, args = (line[1:]+' ').split(' ', 1)
            verb = verb.lower()
            args = args.strip()

            # check the PIs
            if verb == "format":
                # markup format
                pi_format = args.lower()
            elif verb == "refresh":
                if config.refresh:
                    try:
                        mindelay, targetallowed = config.refresh
                        args = args.split()
                        if len(args) >= 1:
                            delay = max(int(args[0]), mindelay)
                        if len(args) >= 2:
                            target = args[1]
                        else:
                            target = self.page_name
                        if target.find('://') >= 0:
                            if targetallowed == 'internal':
                                raise ValueError
                            elif targetallowed == 'external':
                                url = target
                        else:
                            url = Page(target).url(request)
                        pi_refresh = {'delay': delay, 'url': url, }
                    except (ValueError,):
                        pi_refresh = None
            elif verb == "redirect":
                # redirect to another page
                # note that by including "action=show", we prevent
                # endless looping (see code in "request") or any
                # cascaded redirection
                pi_redirect = args
                if request.form.has_key('action') or request.form.has_key('redirect') or content_only: continue

                request.http_redirect('%s/%s?action=show&redirect=%s' % (
                    request.getScriptname(),
                    wikiutil.quoteWikiname(pi_redirect),
                    urllib.quote_plus(self.page_name, ''),))
                return
            elif verb == "deprecated":
                # deprecated page, append last backup version to current contents
                # (which should be a short reason why the page is deprecated)
                msg = '%s<strong>%s</strong><br>%s' % (
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
                    key, val = args.split(' ', 1)
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
                        '<input type="hidden" name="action" value="formtest">\n' % self.url(request))
                pi_formtext.append(wikiform.parseDefinition(request, args, pi_formfields))
            elif verb == "acl":
                # We could build it here, but there's no request.
                pass
            else:
                # unknown PI ==> end PI parsing, and show invalid PI as text
                body = line + '\n' + body
                break

        # start document output
        doc_leader = self.formatter.startDocument(self.page_name)
        if not content_only:
            # send the document leader
            request.http_headers()
            request.write(doc_leader)

            # send the page header
            if self.default_formatter:
                page_needle = self.page_name
                if config.allow_subpages and page_needle.count('/'):
                    page_needle = '/' + page_needle.split('/')[-1]
                link = '%s/%s?action=fullsearch&amp;value=%s&amp;literal=1&amp;case=1&amp;context=40' % (
                    request.getScriptname(),
                    wikiutil.quoteWikiname(self.page_name),
                    urllib.quote_plus(page_needle, ''))
                title = self.split_title(request)
                if self.prev_date:
                    msg = "<strong>%s</strong><br>%s" % (
                        _('Version as of %(date)s') % {'date':
                            request.user.getFormattedDateTime(os.path.getmtime(self._text_filename()))},
                        msg)
                
                # This redirect message is very annoying.
                # Todo: add a config variable to disable it or delete it.
                if request.form.has_key('redirect'):
                    redir = request.form['redirect'][0]
                    msg = '%s<strong>%s</strong><br>%s' % (
                        wikiutil.getSmiley('/!\\', self.formatter),
                        _('Redirected from page "%(page)s"') % {'page':
                            wikiutil.link_tag(request, wikiutil.quoteWikiname(redir) + "?action=show", redir)},
                        msg)
                if pi_redirect:
                    msg = '%s<strong>%s</strong><br>%s' % (
                        wikiutil.getSmiley('<!>', self.formatter),
                        _('This page redirects to page "%(page)s"') % {'page': pi_redirect},
                        msg)

                
                # Page trail
                trail = None
                if not print_mode and request.user.valid and request.user.show_page_trail:
                    request.user.addTrail(self.page_name)
                    trail = request.user.getTrail()

                wikiutil.send_title(request, title, link=link, msg=msg,
                    pagename=self.page_name, print_mode=print_mode, pi_refresh=pi_refresh,
                    allow_doubleclick=1, trail=trail)

                # user-defined form preview?
                # Todo: check if this is also an RTL form - then add ui_lang_attr
                if pi_formtext:
                    pi_formtext.append('<input type="hidden" name="fieldlist" value="%s">\n' %
                        "|".join(pi_formfields))
                    pi_formtext.append('</form></table>\n')
                    pi_formtext.append(_(
                        '<p><small>If you submit this form, the submitted values'
                        ' will be displayed.\nTo use this form on other pages, insert a\n'
                        '<br><br><strong><tt>&nbsp;&nbsp;&nbsp;&nbsp;'
                        '[[Form("%(pagename)s")]]'
                        '</tt></strong><br><br>\n'
                        'macro call.</small></p>\n'
                    ) % {'pagename': self.page_name})
                    request.write(''.join(pi_formtext))

        # try to load the parser
        Parser = wikiutil.importPlugin("parser", pi_format, "Parser")
        if Parser is None:
            # default to plain text formatter (i.e. show the page source)
            del Parser
            from parser.plain import Parser
        
        # start wiki content div
        # Content language and direction is set by the theme
        lang_attr = request.theme.content_lang_attr()
        request.write('<div id="%s" %s>\n' % (content_id, lang_attr))
        
        # new page?
        if not self.exists() and self.default_formatter and not content_only:
            self._emptyPageText(request)
        elif not request.user.may.read(self.page_name):
            request.write("<strong>%s</strong><br>" % _("You are not allowed to view this page."))
        else:
            # parse the text and send the page content
            self.send_page_content(request, Parser, body)

            # check for pending footnotes
            if getattr(request, 'footnotes', None):
                from MoinMoin.macro.FootNote import emit_footnotes
                request.write(emit_footnotes(request, self.formatter))

        # end wiki content div
        request.write('</div>\n')
        
        # end document output
        doc_trailer = self.formatter.endDocument()
        if not content_only:
            # send the page footer
            if self.default_formatter and not print_mode:
                wikiutil.send_footer(request, self.page_name, self._last_modified(request),
                    print_mode=print_mode)

            request.write(doc_trailer)
        
        # cache the pagelinks
        if self.default_formatter and self.exists():
            arena = "pagelinks"
            key   = wikiutil.quoteFilename(self.page_name)
            cache = caching.CacheEntry(arena, key)
            if cache.needsUpdate(self._text_filename()):
                links = self.formatter.pagelinks
                links.sort()
                cache.update('\n'.join(links))

        request.clock.stop('send_page')


    def send_page_content(self, request, Parser, body, needsupdate=0):
        """
        Output the formatted wiki page, using caching, if possible.

        @param request: the request object
        @param Parser: the Parser
        @param body: text of the wiki page
        @param needsupdate: if 1, force update of the cached compiled page
        """
        formatter_name = str(self.formatter.__class__).\
                         replace('MoinMoin.formatter.', '').\
                         replace('.Formatter', '')

        # if no caching
        if  (self.prev_date or self.hilite_re or self._raw_body_modified or
            (not getattr(Parser, 'caching', None)) or
            (not formatter_name in config.caching_formats)):
            # parse the text and send the page content
            Parser(body, request).format(self.formatter)
            return

        #try cache
        _ = request.getText
        from MoinMoin import wikimacro
        arena = 'Page.py'
        key = wikiutil.quoteFilename(self.page_name) + '.' + formatter_name
        cache = caching.CacheEntry(arena, key)
        code = None

        # render page
        if cache.needsUpdate(self._text_filename(),
                wikiutil.getPagePath(self.page_name, 'attachments', check_create=0)) or needsupdate:
            from MoinMoin.formatter.text_python import Formatter
            formatter = Formatter(request, ["page"], self.formatter)

            import marshal
            buffer = cStringIO.StringIO()
            request.redirect(buffer)
            parser = Parser(body, request)
            parser.format(formatter)
            request.redirect()
            text = buffer.getvalue()
            buffer.close()
            src = formatter.assemble_code(text)
            #request.write(src) # debug 
            code = compile(src, self.page_name, 'exec')
            cache.update(marshal.dumps(code))
            
        # send page
        formatter = self.formatter
        parser = Parser(body, request)
        macro_obj = wikimacro.Macro(parser)

        if not code:
            import marshal
            code = marshal.loads(cache.content())
        try:
            exec code
        except 'CacheNeedsUpdate': # if something goes wrong, try without caching
           self.send_page_content(request, Parser, body, needsupdate=1)
           cache = caching.CacheEntry(arena, key)
            
        refresh = wikiutil.link_tag(request,
            wikiutil.quoteWikiname(self.page_name) +
            "?action=refresh&amp;arena=%s&amp;key=%s" % (arena, key),
            _("RefreshCache")
        ) + ' %s<br>' % _('for this page (cached %(date)s)') % {
                'date': self.formatter.request.user.getFormattedDateTime(cache.mtime())
        }
        self.formatter.request.add2footer('RefreshCache', refresh)


    def _emptyPageText(self, request):
        """
        Output the default page content for new pages.
        
        @param request: the request object
        """
        from MoinMoin.action import LikePages
        _ = request.getText
  
        request.write(self.formatter.paragraph(1))
        request.write(wikiutil.link_tag(request,
            wikiutil.quoteWikiname(self.page_name)+'?action=edit',
            _("Create this page")))
        request.write(self.formatter.paragraph(0))
  
        # look for template pages
        templates = filter(lambda page, u = wikiutil: u.isTemplatePage(page),
            wikiutil.getPageList(config.text_dir))
        if templates:
            templates.sort()

            request.write(self.formatter.paragraph(1) +
                self.formatter.text(_('Alternatively, use one of these templates:')) +
                self.formatter.paragraph(0))

            # send list of template pages
            request.write(self.formatter.bullet_list(1))
            for page in templates:
                request.write(self.formatter.listitem(1) +
                    wikiutil.link_tag(request, "%s?action=edit&amp;template=%s" % (
                        wikiutil.quoteWikiname(self.page_name),
                        wikiutil.quoteWikiname(page)),
                    page) +
                    self.formatter.listitem(0))
            request.write(self.formatter.bullet_list(0))

        request.write(self.formatter.paragraph(1) +
            self.formatter.text(_('To create your own templates, ' 
                'add a page with a name matching the regex "%(page_template_regex)s".') % vars(config)) +
            self.formatter.paragraph(0))

        # list similar pages that already exist
        start, end, matches = LikePages.findMatches(self.page_name, request)
        if matches and not isinstance(matches, type('')):
            request.write(self.formatter.rule() + '<p>' +
                _('The following pages with similar names already exist...') + '</p>')
            LikePages.showMatches(self.page_name, request, start, end, matches)


    def getPageLinks(self, request):
        """
        Get a list of the links on this page.
        
        @param request: the request object
        @rtype: list
        @return: page names this page links to
        """
        if not self.exists(): return []

        arena = "pagelinks"
        key   = wikiutil.quoteFilename(self.page_name)
        cache = caching.CacheEntry(arena, key)
        if cache.needsUpdate(self._text_filename()):
            # this is normally never called, but is here to fill the cache
            # in existing wikis; thus, we do a "null" send_page here, which
            # is not efficient, but reduces code duplication
            # !!! it is also an evil hack, and needs to be removed
            # !!! by refactoring Page to separate body parsing & send_page
            request.redirect(cStringIO.StringIO())
            try:
                try:
                    request.mode_getpagelinks = 1
                    Page(self.page_name).send_page(request, content_only=1)
                except:
                    import traceback
                    traceback.print_exc()
                    cache.update('')
            finally:
                request.mode_getpagelinks = 0
                request.redirect()
                if hasattr(request, '_fmt_hd_counters'):
                    del request._fmt_hd_counters

        return filter(None, cache.content().split('\n'))


    def getCategories(self, request):
        """
        Get categories this page belongs to.

        @param request: the request object
        @rtype: list
        @return: categories this page belongs to
        """
        return wikiutil.filterCategoryPages(self.getPageLinks(request))

    # There are many places accessing ACLs even without actually sending
    # the page. This cache ensures that we don't have to parse ACLs for
    # some page twice.
    _acl_cache = {}
    
    def getACL(self):
        """
        Get ACLs of this page.

        @param request: the request object
        @rtype: dict
        @return: ACLs of this page
        """
        if not config.acl_enabled:
            import wikiacl
            return wikiacl.AccessControlList()
        # mtime check for forked long running processes
        fn = self._text_filename()
        acl = None
        if os.path.exists(fn):
            mtime = os.path.getmtime(fn)
        else:
            mtime = 0
        if self._acl_cache.has_key(self.page_name):
            (omtime, acl) = self._acl_cache[self.page_name]
            if omtime < mtime:
                acl = None
        if acl is None:
            import wikiacl
            body = ''
            if self.exists():
                body = self.get_raw_body()
            else:
                # if the page isn't there any more, use the ACLs of the last backup
                oldversions = wikiutil.getBackupList(config.backup_dir, self.page_name)
                if oldversions:
                    oldfile = oldversions[0]
                    olddate = os.path.basename(oldfile)[len(wikiutil.quoteFilename(self.page_name))+1:]
                    oldpage = Page(self.page_name, date=olddate)
                    body = oldpage.get_raw_body()
            acl = wikiacl.parseACL(body)
            self._acl_cache[self.page_name] = (mtime, acl)
        return acl



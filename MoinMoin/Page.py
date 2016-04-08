"""
    MoinMoin - Page class

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Page.py,v 1.106 2002/03/06 22:36:52 jhermann Exp $
"""

# Imports
import cStringIO, os, re, sys, string, time, urllib
from MoinMoin import caching, config, eventlog, user, util, wikiutil, webapi
from MoinMoin.cgimain import request
from MoinMoin.i18n import _


#############################################################################
### Page - Manage a page associated with a WikiName
#############################################################################
class Page:
    """ A wiki page """

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
        if querystr: url = "%s?%s" % (url, querystr)
        return url


    def link_to(self, text=None, querystr=None, anchor=None):
        """Return HTML markup that links to this page"""
        text = text or self.split_title()
        fmt = getattr(self, 'formatter', None)
        url = wikiutil.quoteWikiname(self.page_name)
        if querystr: url = "%s?%s" % (url, querystr)
        if anchor: url = "%s#%s" % (url, urllib.quote_plus(anchor))
        if self.exists():
            return wikiutil.link_tag(url, text, formatter=fmt)
        elif user.current.show_nonexist_qm:
            return wikiutil.link_tag(url,
                '?', 'nonexistent', formatter=fmt) + text
        else:
            return wikiutil.link_tag(url, text, 'nonexistent', formatter=fmt)


    def set_raw_body(self, body):
        """Set the raw body text (prevents loading from disk)"""
        self.raw_body = body


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


    def send_page(self, form, msg=None, **keywords):
        """ Send the formatted page to stdout.

            **form** -- CGI-Form
            **msg** -- if given, display message in header area
            **keywords** --
                content_only: 1 to omit page header and footer
                count_hit: add an event to the log
        """
        request.clock.start('send_page')
        import cgi

        # determine modes
        print_mode = form.has_key('action') and form['action'].value == 'print'
        content_only = keywords.get('content_only', 0)
        self.hilite_re = keywords.get('hilite_re', None)
        if msg is None: msg = ""

        # count hit?
        if keywords.get('count_hit', 0):
            eventlog.logger.add('VIEWPAGE', {'pagename': self.page_name})

        # load the text
        body = self.get_raw_body()

        # if necessary, load the default formatter
        if self.default_formatter:
            from formatter.text_html import Formatter
            self.formatter = Formatter(store_pagelinks=1)
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

                webapi.http_redirect('%s/%s?action=show&redirect=%s' % (
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
            webapi.http_headers()
            sys.stdout.write(doc_leader)

            # send the page header
            if self.default_formatter:
                page_needle = self.page_name
                if config.allow_subpages and string.count(page_needle, '/'):
                    page_needle = '/' + string.split(page_needle, '/')[-1]
                link = '%s/%s?action=fullsearch&value=%s&literal=1' % (
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
            Parser(body).format(self.formatter, form)

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
                wikiutil.send_footer(self.page_name, self._last_modified(),
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


    def getPageLinks(self):
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
                    Page(self.page_name).send_page({}, content_only=1)
                except:
                    cache.update('')
            finally:
                sys.stdout = stdout

        return filter(None, string.split(cache.content(), '\n'))


    def send_editor(self, form, **kw):
        """ Send the editor form page.

            Keywords:
                preview - if true, show preview
                comment - comment field (when preview is true)
        """
        from cgi import escape
        try:
            from MoinMoin.action import SpellCheck
        except ImportError:
            SpellCheck = None

        # check edit permissions
        if not user.current.may.edit:
            self.send_page(form,
                msg=_("""<b>You are not allowed to edit any pages.</b>"""))
            return

        webapi.http_headers(webapi.nocache)

        if self.prev_date:
            print '<b>Cannot edit old revisions</b>'
            return

        # check for preview submit
        title = _('Edit "%(pagename)s"')
        preview = kw.get('preview', 0)
        if preview:
            title = _('Preview of "%(pagename)s"')
            try:
                newtext = form['savetext'].value
            except KeyError:
                newtext = ""

            newtext = string.replace(newtext, "\r", "")
            self.set_raw_body(newtext)

        # send header stuff
        wikiutil.send_title(
            title % {'pagename': self.split_title(),},
            pagename=self.page_name)
        template_param = ''
        if form.has_key('template'):
            template_param = '&template=' + form['template'].value
        print '<a href="%s?action=edit&rows=10&cols=60%s">%s</a>' % (
            wikiutil.quoteWikiname(self.page_name), template_param,
            _('Reduce editor size'))
        print "|", wikiutil.getSysPage('HelpOnFormatting').link_to()
        if preview:
            print '| <a href="#preview">%s</a>' % _('Skip to preview')

        # send form
        try:
            text_rows = int(form['rows'].value)
        except StandardError:
            text_rows = config.edit_rows
            if user.current.valid: text_rows = int(user.current.edit_rows)
        try:
            text_cols = int(form['cols'].value)
        except StandardError:
            text_cols = 80
            if user.current.valid: text_cols = int(user.current.edit_cols)

        print '<form method="post" action="%s/%s%s">' % (
            webapi.getScriptname(),
            wikiutil.quoteWikiname(self.page_name),
            '#preview',
            )
        print '<input type="hidden" name="action" value="savepage">'
        if os.path.isfile(self._text_filename()):
            mtime = os.path.getmtime(self._text_filename())
        else:
            mtime = 0
        print '<input type="hidden" name="datestamp" value="%d">' % (mtime,)

        # get the text body for the editor field
        if form.has_key('template'):
            # "template" parameter contains the name of the template page
            template_page = wikiutil.unquoteWikiname(form['template'].value)
            raw_body = Page(template_page).get_raw_body()
            if raw_body:
                print _("[Content of new page loaded from %s]") % (template_page,)
            else:
                print _("[Template %s not found]") % (template_page,)
        else:
            raw_body = self.get_raw_body()

        # generate default content
        if not raw_body:
            raw_body = _('Describe %s here.') % (self.page_name,)

        # replace CRLF with LF
        raw_body = string.replace(raw_body, '\r\n', '\n')

        # print the editor textarea and the save button
        print ('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, escape(raw_body)))

        notify = ''
        if config.mail_smarthost:
            notify = '''<input type="checkbox" name="notify" value="1"%s>
                        <font face="Verdana" size="-1">%s</font><br>''' % (
                ('', ' checked')[not preview or (form.getvalue('notify') == '1')],
                _('Send mail notification'),
            )

        if preview: print '<a name="preview">'
        print "<br>", _("Optional comment about this change") + \
            '<br><input type="text" name="comment" value="%s" size="%d" maxlength="60" style="width:100%%">' % (
                escape(kw.get('comment', ''), 1), text_cols,)

        button_spellcheck = (SpellCheck and
            '<input type="submit" name="button_spellcheck" value="%s"> &nbsp; '
                % _('Check Spelling')) or ''

        print '''
<div style="margin-top:6pt;margin-bottom:6pt;">
<input type="submit" name="button_save" value="%s"> &nbsp;
<input type="submit" name="button_preview" value="%s"> &nbsp; %s&nbsp; &nbsp; &nbsp;
<input type="submit" name="button_cancel" value="%s">
</div>''' % (_('Save Changes'), _('Preview'), button_spellcheck, _('Cancel'),)

        print '''%s
<input type="checkbox" name="rstrip" value="1"%s>
<font face="Verdana" size="-1">%s</font>
''' % (     notify,
            ('', ' checked')[preview and (form.getvalue('rstrip') == '1')],
            _('Remove trailing whitespace from each line')
        )

        badwords_re = None
        if preview:
            if SpellCheck and (
                    form.has_key('button_spellcheck') or
                    form.has_key('button_newwords')):
                badwords, badwords_re, msg = SpellCheck.checkSpelling(self, form, own_form=0)
                print "<p>", msg
            print '</a>'
        print "</form>"

        if preview:
            print ('<hr size="1">'
                '<table border="0" cellspacing="0" cellpadding="3" bgcolor="#F4F4F4"'
                    ' style="background-image:url(%s/img/draft.png); background-color:#F4F4F4;">'
                '<tr><td>') % (config.url_prefix,)
            self.send_page(form, content_only=1, hilite_re=badwords_re)
            print '</td></tr></table>'

        # QuickHelp originally by Georg Mischler <schorsch@lightingwiki.com>
        print _("""<hr>
<font face="Verdana" size="-1">
<b>Emphasis:</b> ''<i>italics</i>''; '''<b>bold</b>'''; '''''<b><i>bold italics</i></b>''''';
    ''<i>mixed '''<b>bold</b>''' and italics</i>''; ---- horizontal rule.<br>
<b>Headings:</b> = Title 1 =; == Title 2 ==; === Title 3 ===;
    ==== Title 4 ====; ===== Title 5 =====.<br>
<b>Lists:</b> space and one of * bullets; 1., a., A., i., I. numbered items;
    1.#n start numbering at n; space alone indents.<br>
<b>Links:</b> JoinCapitalizedWords; ["brackets and double quotes"];
    url; [url]; [url label].<br>
<b>Tables</b>: || cell text |||| cell text spanning two columns ||;
    no trailing white space allowed after tables or titles.<br>
</font>
<hr>
""")


    def delete(self):
        """Delete the page (but keep the backups)"""
        # First save a final backup copy of the current page
        # (recreating the page allows access to the backups again)
        self.save_text("deleted", '0')

        # Then really delete it
        try:
            os.remove(self._text_filename())
        except OSError, er:
            import errno
            if er.errno <> errno.ENOENT: raise er

        # delete pagelinks
        arena = "pagelinks"
        key   = wikiutil.quoteFilename(self.page_name)
        cache = caching.CacheEntry(arena, key)
        cache.remove()


    def notifySubscribers(self, comment):
        """ Send email to all subscribers of this page.
            Return message, indicating success or errors.
        """
        # extract categories of this page
        pageList = self.getPageLinks()
        CATEGORY_RE = re.compile("^Category")
        pageList = filter(CATEGORY_RE.match, pageList)
        
        # add current page name for list matching
        pageList.append(self.page_name)

        # get email addresses of the all wiki user which have a profile stored;
        # add the address only if the user has subscribed to the page and
        # the user is not the current editor
        userlist = user.getUserList()
        emails = []
        for uid in userlist:
            if uid == user.current.id: continue # no self notification
            subscriber = user.User(uid)
            if not subscriber.email: continue # skip empty email address

            if subscriber.isSubscribedTo(pageList):
                emails.append(subscriber.email)

        if emails:
            # send email to all subscribers; note that text must be in
            # English for all users, since currently we cannot (easily)
            # send the text in the recipient's language.
            # !!! TODO: make this possible
            mailBody = ("Dear Wiki user,\n\n"
                'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
                "The following page has been changed by %(editor)s:\n"
                "%(pagelink)s\n\n") % {
                    'editor': user.current.name or os.environ.get('REMOTE_ADDR', "<unknown>"),
                    'pagelink': webapi.getQualifiedURL(self.url()),
                    'sitename': config.sitename or webapi.getBaseURL(),
            }

            if comment:
                mailBody = mailBody + \
                    "The comment on the change is:\n%s\n\n" % comment

            # get a list of old revisions, and append a diff
            oldversions = wikiutil.getBackupList(config.backup_dir, self.page_name)
            if not oldversions:
                mailBody = mailBody + \
                    "No older revisions of the page stored, diff not available."
            else:
                page_file, backup_file, lines = wikiutil.pagediff(self.page_name, oldversions[0])
                if lines and len(lines) > 2:
                    mailBody = "%s%s\n%s" % (
                        mailBody, ("-" * 78), string.join(lines[2:], ''))
                else:
                    mailBody = mailBody + "No differences found!\n"

            msg = _('\n'
                    'Sent a mail notification to these addresses: %s\n'
                    '<br>Result was: ') % string.join(emails, ", ")
            msg = msg + util.sendmail(emails,
                '[%(sitename)s] Update of "%(pagename)s"' % {
                    'sitename': config.sitename or "Wiki",
                    'pagename': self.page_name,
                },
                mailBody, mail_from=user.current.email)
            return msg

        return _('Nobody subscribed to this page, no mail sent.')


    def _user_variable(self):
        """If user has a profile return the user name from the profile
           else return the remote address or "anonymous"

           If the user name contains spaces it is wiki quoted to allow
           links to the wiki user homepage (if one exists).
        """
        username = user.current.name
        if username and config.allow_extended_names and \
                string.count(username, ' ') and Page(username).exists():
            username = '["%s"]' % username
        return username or os.environ.get('REMOTE_ADDR', 'anonymous')


    def _expand_variables(self, text):
        """Expand @VARIABLE@ in `text`and return the expanded text."""
        #!!! TODO: Allow addition of variables via moin_config (and/or a text file)
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time()))
        system_vars = {
            'TIME': lambda t=now: "[[DateTime(%s)]]" % t,
            'DATE': lambda t=now: "[[Date(%s)]]" % t,
            'USERNAME': lambda s=self: s._user_variable(),
            'USER': lambda s=self: "-- %s" % (s._user_variable(),),
            'SIG': lambda s=self, t=now: "-- %s [[DateTime(%s)]]"
                % (s._user_variable(), t,),
        }

        if user.current.valid and user.current.name and user.current.email:
            system_vars['MAILTO'] = lambda u=user.current: \
                "[mailto:%s %s]" % (u.email, u.name)
        #!!! TODO: Use a more stream-lined re.sub algorithm
        for name, val in system_vars.items():
            text = string.replace(text, '@' + name + '@', val())
        return text


    def _write_file(self, text):
        is_deprecated = string.lower(text[:11]) == "#deprecated"

        # save to tmpfile
        tmp_filename = self._tmp_filename()
        tmp_file = open(tmp_filename, 'wb')
        tmp_file.write(text)
        tmp_file.close()
        page_filename = self._text_filename()

        if not os.path.isdir(config.backup_dir):
            os.mkdir(config.backup_dir, 0777 & config.umask)

        if os.path.isfile(page_filename) \
                and not is_deprecated:
            os.rename(page_filename, os.path.join(config.backup_dir,
                wikiutil.quoteFilename(self.page_name) + '.' + str(os.path.getmtime(page_filename))))
        else:
            if os.name == 'nt':
                # Bad Bill!  POSIX rename ought to replace. :-(
                try:
                    os.remove(page_filename)
                except OSError, er:
                    import errno
                    if er.errno <> errno.ENOENT: raise er

        # set in-memory content
        self.set_raw_body(text)

        # replace old page by tmpfile
        os.chmod(tmp_filename, 0666 & config.umask)
        os.rename(tmp_filename, page_filename)
        return os.path.getmtime(page_filename)


    def save_text(self, newtext, datestamp, **kw):
        """ Save new text for a page.

            Keyword parameters:
                stripspaces - strip whitespace from line ends (default: 0)
                notify - send email notice tp subscribers (default: 0)
                comment - comment field (when preview is true)
        """
        msg = ""
        if not user.current.may.edit:
            msg = _("""<b>You are not allowed to edit any pages.</b>""")
        if not newtext:
            msg = _("""<b>You cannot save empty pages.</b>""")
        elif datestamp == '0':
            pass
        elif datestamp != str(os.path.getmtime(self._text_filename())):
            msg = _("""<b>Sorry, someone else saved the page while you edited it.
<p>Please do the following: Use the back button of your browser, and cut&paste
your changes from there. Then go forward to here, and click EditText again.
Now re-add your changes to the current page contents.
<p><em>Do not just replace
the content editbox with your version of the page, because that would
delete the changes of the other person, which is excessively rude!</em></b>
""")

        # save only if no error occured (msg is empty)
        if not msg:
            # set success msg
            msg = _("""<b>Thank you for your changes.
Your attention to detail is appreciated.</b>""")

            # remove CRs (so Win32 and Unix users save the same text)
            newtext = string.replace(newtext, "\r", "")

            # possibly strip trailing spaces
            if kw.get('stripspaces', 0):
                newtext = string.join(map(string.rstrip, string.split(newtext, '\n')), '\n')

            # add final newline if not present in textarea, better for diffs
            # (does not include former last line when just adding text to
            # bottom; idea by CliffordAdams)
            if newtext and newtext[-1] != '\n':
                newtext = newtext + '\n'

            # expand variables, unless it's a template or form page
            if not (wikiutil.isTemplatePage(self.page_name) or
                    wikiutil.isFormPage(self.page_name)):
                newtext = self._expand_variables(newtext)

            # write the page file
            mtime = self._write_file(newtext)

            # write the editlog entry
            from MoinMoin import editlog
            log = editlog.makeLogStore()
            remote_name = os.environ.get('REMOTE_ADDR', '')
            log.addEntry(self.page_name, remote_name, mtime, kw.get('comment', ''))

            # add event log entry
            eventlog.logger.add('SAVEPAGE', {'pagename': self.page_name})

            # send notification mails
            if config.mail_smarthost and kw.get('notify', 0):
                msg = msg + "<p>" + self.notifySubscribers(kw.get('comment', ''))

        return msg


# Python 1.6's "re" is buggy
if sys.version[:3] == "1.6":
    Page.split_title = Page._split_title_py16


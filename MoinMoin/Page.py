"""
    MoinMoin - Page class

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Page.py,v 1.36 2001/04/04 21:47:08 jhermann Exp $
"""

# Imports
import cStringIO, os, re, sys, string, time, urllib
from MoinMoin import caching, config, user, util, wikiutil, webapi


#############################################################################
### Page - Manage a page associated with a WikiName
#############################################################################
class Page:
    def __init__(self, page_name, **keywords):
        """ Load page object.

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


    def split_title(self):
        """Return a string with the page name split by spaces"""
        # Python 1.6's "re" is buggy
        if sys.version[:3] == "1.6":
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

        # look for the end of words and the start of a new word,
        # and insert a space there
        return re.sub('([%s])([%s])' % (config.lowerletters, config.upperletters),
            r'\1 \2', self.page_name)


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


    def link_to(self, text=None):
        """Return HTML markup that links to this page"""
        word = self.page_name
        text = text or word
        if self.exists():
            return wikiutil.link_tag(wikiutil.quoteWikiname(word), text)
        else:
            if config.nonexist_qm:
                return wikiutil.link_tag(wikiutil.quoteWikiname(word), '?', 'nonexistent') + text
            else:
                return wikiutil.link_tag(wikiutil.quoteWikiname(word), text, 'nonexistent')


    def set_raw_body(self, body):
        """Set the raw body text (prevents loading from disk)"""
        self.raw_body = body


    def get_raw_body(self):
        """Load the raw markup from the page file"""
        if self.raw_body is not None:
            return self.raw_body

        # try to open file
        try:
            file = open(self._text_filename(), 'rt')
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
        """

        util.clock.start('send_page')

        # determine modes
        print_mode = form.has_key('action') and form['action'].value == 'print'
        content_only = keywords.get('content_only', 0)
        self.hilite_re = keywords.get('hilite_re', None)

        # load the text
        body = self.get_raw_body()

        # if necessary, load the default formatter
        if self.default_formatter:
            from formatter.text_html import Formatter
            self.formatter = Formatter(store_pagelinks=1)
        self.formatter.setPage(self)

        # default is wiki markup
        pi_format = "wiki"
        pi_redirect = None

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

            # skip comments
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
                link = '%s/%s?action=fullsearch&value=%s&literal=1' % (
                    webapi.getScriptname(),
                    wikiutil.quoteWikiname(self.page_name),
                    urllib.quote_plus(self.page_name, ''))
                title = self.split_title()
                if msg is None: msg = ""
                if self.prev_date:
                    msg = "<b>%s</b><br>%s" % (
                        user.current.text('Version as of %(date)s') % {'date':
                            user.current.getFormattedDateTime(os.path.getmtime(self._text_filename()))},
                        msg)
                if form.has_key('redirect'):
                    redir = form['redirect'].value
                    msg = '%s<b>%s</b><br>%s' % (
                        wikiutil.getSmiley('/!\\'),
                        user.current.text('Redirected from page "%(page)s"') % {'page':
                            wikiutil.link_tag(wikiutil.quoteWikiname(redir) + "?action=show", redir)},
                        msg)
                if pi_redirect:
                    msg = '%s<b>%s</b><br>%s' % (
                        wikiutil.getSmiley('<!>'),
                        user.current.text('This page redirects to page "%(page)s"') % {'page': pi_redirect},
                        msg)
                wikiutil.send_title(title, link=link, msg=msg, pagename=self.page_name, print_mode=print_mode)

        # try to load the parser
        Parser = util.importName("MoinMoin.parser." + pi_format, "Parser")
        if Parser is None:
            # default to plain text formatter (i.e. show the page source)
            del Parser
            from parser.plain import Parser

        # new page?
        if not self.exists() and self.default_formatter:
            # generate the default page content for new pages
            print wikiutil.link_tag(wikiutil.quoteWikiname(self.page_name)+'?action=edit',
                user.current.text("Create this page"))

            # look for template pages
            templates = filter(lambda page: page[-8:] == 'Template',
                wikiutil.getPageList(config.text_dir))
            if templates:
                print self.formatter.paragraph()
                print self.formatter.text(user.current.text('Alternatively, use one of these templates:'))

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

            print self.formatter.paragraph()
            print self.formatter.text(user.current.text('To create you own templates, ' +
                'add a page with a name ending in Template.'))
        else:
            # parse the text and send the page content
            Parser(body).format(self.formatter, form)

        # end document output
        doc_trailer = self.formatter.endDocument()
        if not content_only:
            # send the page footer
            if self.default_formatter and not print_mode:
                wikiutil.send_footer(self.page_name, self._last_modified())

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

        util.clock.stop('send_page')


    def _last_modified(self):
        if not self.exists():
            return None
        return user.current.getFormattedDateTime(os.path.getmtime(self._text_filename()))


    def getPageLinks(self):
        """Get a list of the links on this page"""
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

        return string.split(cache.content(), '\n')


    def send_editor(self, form):
        import cgi

        webapi.http_headers(["Pragma: no-cache"])

        if self.prev_date:
            print '<b>Cannot edit old revisions</b>'
            return

        # send header stuff
        wikiutil.send_title('Edit "%s"' % (self.split_title(),), pagename=self.page_name)
        template_param = ''
        if form.has_key('template'):
            template_param = '&template=' + form['template'].value
        print '<a href="%s?action=edit&rows=10&cols=60%s">%s</a>' % (
            wikiutil.quoteWikiname(self.page_name), template_param,
            user.current.text('Reduce editor size'))
        print "|", Page(config.page_edit_tips).link_to()

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

        print '<form method="post" action="%s/%s">' % (webapi.getScriptname(), wikiutil.quoteWikiname(self.page_name))
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
                print user.current.text("[Content of new page loaded from %s]") % (template_page,)
            else:
                print user.current.text("[Template %s not found]") % (template_page,)
        else:
            raw_body = self.get_raw_body()

        # generate default content
        if not raw_body:
            raw_body = user.current.text('Describe %s here.') % (self.page_name,)

        # replace CRLF with LF
        raw_body = string.replace(raw_body, '\r\n', '\n')

        # print the editor textarea and the save button
        print ('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, cgi.escape(raw_body)))
        print '''<div style="margin-top:6pt;margin-bottom:6pt;"><input type="submit" value="%s">
</div>
<input type="checkbox" name="rstrip">
<font face="Verdana" size="-1">%s</font>
''' % (
    user.current.text('Save Changes'),
    user.current.text('Remove trailing whitespace from each line'))
        ##print Page("UploadFile").link_to()
        ##print "<input type=file name=imagefile>"
        ##print "(not enabled yet)"
        print "</form>"

        # QuickHelp originally by Georg Mischler <schorsch@lightingwiki.com>
        print user.current.text("""<hr>
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


    def _write_file(self, text):
        # save to tmpfile
        tmp_filename = self._tmp_filename()
        tmp_file = open(tmp_filename, 'wt')
        tmp_file.write(text)
        tmp_file.close()
        text = self._text_filename()

        if os.path.isdir(config.backup_dir) and os.path.isfile(text):
            os.rename(text, os.path.join(config.backup_dir,
                wikiutil.quoteFilename(self.page_name) + '.' + str(os.path.getmtime(text))))
        else:
            if os.name == 'nt':
                # Bad Bill!  POSIX rename ought to replace. :-(
                try:
                    os.remove(text)
                except OSError, er:
                    import errno
                    if er.errno <> errno.ENOENT: raise er

        # replace old page by tmpfile
        os.chmod(tmp_filename, 0666)
        os.rename(tmp_filename, text)
        return os.path.getmtime(text)


    def save_text(self, newtext, datestamp, **kw):
        msg = ""
        if not newtext:
            msg = user.current.text("""<b>You cannot save empty pages.</b>""")
        elif datestamp == '0':
            pass
        elif datestamp != str(os.path.getmtime(self._text_filename())):
            msg = user.current.text("""<b>Sorry, someone else saved the page while you edited it.
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
            msg = user.current.text("""<b>Thank you for your changes.
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

            # write the page file
            mtime = self._write_file(newtext)

            # write the editlog entry
            from MoinMoin import editlog
            remote_name = os.environ.get('REMOTE_ADDR', '')
            editlog.editlog_add(self.page_name, remote_name, mtime)

        return msg        


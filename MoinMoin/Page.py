"""
    MoinMoin - Page class

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Page.py,v 1.21 2001/01/10 01:57:40 jhermann Exp $
"""

# Imports
import os, re, sys, string, time, urllib
from MoinMoin import config, user, util, wikiutil


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

        try:
            return open(self._text_filename(), 'rt').read()
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty text (note that we
                # never store empty pages, so this is detectable and also
                # safe when passed to a function expecting a string)
                return ""
            else:
                raise er
    

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
            self.formatter = Formatter()
        self.formatter.setPage(self)

        # default is wiki markup
        pi_format = "wiki"
        pi_redirect = None

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
                if form.has_key('action') or form.has_key('redirect'): continue

                util.http_redirect('%s/%s?action=show&redirect=%s' % (
                    util.getScriptname(),
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
            util.http_headers()
            sys.stdout.write(doc_leader)

            # send the page header
            if self.default_formatter:
                link = '%s/%s?action=fullsearch&value=%s&literal=1' % (
                    util.getScriptname(),
                    wikiutil.quoteWikiname(self.page_name),
                    urllib.quote_plus(self.page_name, ''))
                title = self.split_title()
                if msg is None: msg = ""
                if self.prev_date:
                    msg = "<b>Version as of %s</b><br>%s" % (
                        user.current.getFormattedDateTime(os.path.getmtime(self._text_filename())),
                        msg)
                if form.has_key('redirect'):
                    redir = form['redirect'].value
                    msg = '%s<b>Redirected from page "%s"</b><br>%s' % (
                        wikiutil.getSmiley('/!\\'),
                        wikiutil.link_tag(wikiutil.quoteWikiname(redir) + "?action=show", redir),
                        msg)
                if pi_redirect:
                    msg = '%s<b>This page redirects to page "%s"</b><br>%s' % (
                        wikiutil.getSmiley('<!>'), pi_redirect, msg)
                wikiutil.send_title(title, link=link, msg=msg, pagename=self.page_name, print_mode=print_mode)

        # try to load the parser
        Parser = util.importName("MoinMoin.parser." + pi_format, "Parser")
        if Parser is None:
            # default to plain text formatter (i.e. show the page source)
            del Parser
            from parser.plain import Parser

        # new page?
        if not body and self.default_formatter:
            # generate the default page content for new pages
            print wikiutil.link_tag(wikiutil.quoteWikiname(self.page_name)+'?action=edit',
                "Create this page")

            # look for template pages
            templates = filter(lambda page: page[-8:] == 'Template',
                wikiutil.getPageList(config.text_dir))
            if templates:
                print self.formatter.paragraph()
                print self.formatter.text('Alternatively, use one of these templates:')

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
            print self.formatter.text('To create you own templates, ' +
                'add a page with a name ending in Template.')
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

        util.clock.stop('send_page')


    def _last_modified(self):
        if not self.exists():
            return None
        return user.current.getFormattedDateTime(os.path.getmtime(self._text_filename()))


    def send_editor(self, form):
        import cgi

        util.http_headers()

        if self.prev_date:
            print '<b>Cannot edit old revisions</b>'
            return

        # send header stuff
        wikiutil.send_title('Edit "%s"' % (self.split_title(),), pagename=self.page_name)
        template_param = ''
        if form.has_key('template'):
            template_param = '&template=' + form['template'].value
        print '<a href="%s?action=edit&rows=10&cols=60%s">Reduce editor size</a>' % (
            wikiutil.quoteWikiname(self.page_name), template_param)
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

        print '<form method="post" action="%s/%s">' % (util.getScriptname(), wikiutil.quoteWikiname(self.page_name))
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
                print "[Content of new page loaded from %s]" % (template_page,)
            else:
                print "[Template %s not found]" % (template_page,)
        else:
            raw_body = self.get_raw_body()

        # generate default content
        if not raw_body:
            raw_body = 'Describe %s here.' % (self.page_name,)

        # replace CRLF with LF
        raw_body = string.replace(raw_body, '\r\n', '\n')

        # print the editor textarea and the save button
        print ('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, cgi.escape(raw_body)))
        print '<div style="margin-top:6pt;"><input type="submit" value="Save Changes">'
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

        # save only if no error occured (msg is empty)
        if not msg:
            # set success msg
            msg = """<b>Thank you for your changes.
Your attention to detail is appreciated.</b>"""

            # remove CRs (so Win32 and Unix users save the same text)
            newtext = string.replace(newtext, "\r", "")

            # add final newline if not present in textarea, better for diffs
            # (does not include former last line when just adding text to
            # bottom; idea by CliffordAdams)
            if newtext and newtext[-1] != '\n':
                newtext = newtext + '\n'

            # write the page file
            self._write_file(newtext)

            # write the editlog entry
            remote_name = os.environ.get('REMOTE_ADDR', '')
            wikiutil.editlog_add(self.page_name, remote_name)

        return msg        


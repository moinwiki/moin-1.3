"""
    MoinMoin - Page class

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Page.py,v 1.11 2000/12/06 10:48:50 jhermann Exp $
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


    def link_to(self):
        """Return HTML markup that links to this page"""
        word = self.page_name
        if self.exists():
            return wikiutil.link_tag(wikiutil.quoteWikiname(word), word)
        else:
            if config.nonexist_qm:
                return wikiutil.link_tag(wikiutil.quoteWikiname(word), '?', 'nonexistent') + word
            else:
                return wikiutil.link_tag(wikiutil.quoteWikiname(word), word, 'nonexistent')


    def get_raw_body(self):
        """Load the raw markup from the page file"""
        try:
            return open(self._text_filename(), 'rt').read()
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, use default
                return 'Describe %s here.' % self.page_name
            else:
                raise er
    

    def send_page(self, form, msg=None, print_mode=0):
        #!!!clock.start('send_page')

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
            except:
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

        # send the document leader
        util.http_headers()
        sys.stdout.write(self.formatter.startDocument(self.page_name))

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
                    time.strftime(config.datetime_fmt,
                        user.current.getTime(float(self.prev_date))),
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

        # parse the text and send the page content
        Parser(body).format(self.formatter, form)

        # send the page footer
        if self.default_formatter and not print_mode:
            wikiutil.send_footer(self.page_name, self._last_modified())

        sys.stdout.write(self.formatter.endDocument())

        #!!!clock.stop('send_page')


    def _last_modified(self):
        if not self.exists():
            return None
        modtime = user.current.getTime(os.path.getmtime(self._text_filename()))
        return time.strftime(config.datetime_fmt, modtime)


    def send_editor(self, form):
        import cgi

        util.http_headers()

        if self.prev_date:
            print '<b>Cannot edit old revisions</b>'
            return

        # send header stuff
        wikiutil.send_title('Edit ' + self.split_title(), pagename=self.page_name)
        print '<a href="%s?action=edit&rows=10&cols=60">Reduce editor size</a>' % (wikiutil.quoteWikiname(self.page_name),)
        print "|", Page(config.page_edit_tips).link_to()

        # send form
        try:
            text_rows = int(form['rows'].value)
        except:
            text_rows = config.edit_rows
            if user.current.valid: text_rows = int(user.current.edit_rows)
        try:
            text_cols = int(form['cols'].value)
        except:
            text_cols = 80
            if user.current.valid: text_cols = int(user.current.edit_cols)

        print '<form method="post" action="%s/%s">' % (util.getScriptname(), wikiutil.quoteWikiname(self.page_name))
        print '<input type="hidden" name="action" value="savepage">' 
        if os.path.isfile(self._text_filename()):
            mtime = os.path.getmtime(self._text_filename())
        else:
            mtime = 0
        print '<input type="hidden" name="datestamp" value="%d">' % (mtime,)
        raw_body = string.replace(self.get_raw_body(), '\r\n', '\n')
        print ('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, cgi.escape(raw_body)))
        print '<div style="margin-top:6pt;"><input type="submit" value="Save Changes">'
        ##<input type=reset value="Reset">"""
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
            os.rename(text, os.path.join(config.backup_dir, wikiutil.quoteFilename(self.page_name) + '.' + `time.time()`))
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


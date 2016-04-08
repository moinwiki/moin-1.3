"""
    MoinMoin - PageEditor class

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: PageEditor.py,v 1.11 2002/05/09 11:33:07 jhermann Exp $
"""

# Imports
import cStringIO, os, re, sys, string, time, urllib
from MoinMoin import caching, config, user, util, wikiutil, webapi
from MoinMoin.Page import Page
from MoinMoin.i18n import _, getText


#############################################################################
### PageEditor - Edit pages
#############################################################################
class PageEditor(Page):
    """ Editor for a wiki page """

    def __init__(self, page_name, **keywords):
        """ Create page editor object.
        """
        apply(Page.__init__, (self, page_name), keywords)


    def set_raw_body(self, body):
        """Set the raw body text (prevents loading from disk)"""
        self.raw_body = body


    def send_editor(self, request, **kw):
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

        form = request.form

        # check edit permissions
        if not request.user.may.edit:
            self.send_page(request,
                msg=_("""<b>You are not allowed to edit any pages.</b>"""))
            return

        webapi.http_headers(request, webapi.nocache)

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
            if request.user.valid: text_rows = int(request.user.edit_rows)
        try:
            text_cols = int(form['cols'].value)
        except StandardError:
            text_cols = 80
            if request.user.valid: text_cols = int(request.user.edit_cols)

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
                badwords, badwords_re, msg = SpellCheck.checkSpelling(self, request, own_form=0)
                print "<p>", msg
            print '</a>'
        print "</form>"

        if preview:
            print ('<hr size="1">'
                '<table border="0" cellspacing="0" cellpadding="3" bgcolor="#F4F4F4"'
                    ' style="background-image:url(%s/img/draft.png); background-color:#F4F4F4;">'
                '<tr><td>') % (config.url_prefix,)
            self.send_page(request, content_only=1, hilite_re=badwords_re)
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


    def deletePage(self, request, comment=None):
        """Delete the page (but keep the backups)"""
        # First save a final backup copy of the current page
        # (recreating the page allows access to the backups again)
        self.save_text(request, "deleted", '0', comment=comment or '')

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


    def _sendNotification(self, request, comment, emails, email_lang, oldversions):
        """ Send notification email for a single language.

            Returns sendmail result.
        """
        _ = lambda s, l=email_lang: getText(s, lang=l)

        mailBody = _("Dear Wiki user,\n\n"
            'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
            "The following page has been changed by %(editor)s:\n"
            "%(pagelink)s\n\n") % {
                'editor': request.user.name or os.environ.get('REMOTE_ADDR', _("<unknown>")),
                'pagelink': webapi.getQualifiedURL(self.url()),
                'sitename': config.sitename or webapi.getBaseURL(),
        }

        if comment:
            mailBody = mailBody + \
                _("The comment on the change is:\n%(comment)s\n\n") % locals()

        # append a diff
        if not oldversions:
            mailBody = mailBody + \
                _("No older revisions of the page stored, diff not available.")
        else:
            rc, page_file, backup_file, lines = wikiutil.pagediff(self.page_name, oldversions[0])
            if lines and len(lines) > 2:
                mailBody = "%s%s\n%s" % (
                    mailBody, ("-" * 78), string.join(lines[2:], ''))
            else:
                mailBody = mailBody + _("No differences found!\n")
                if rc:
                    mailBody = mailBody + '\n\n' + \
                        _('The external diff utility returned with error code %(rc)s!') % locals()

        return util.sendmail(emails,
            _('[%(sitename)s] Update of "%(pagename)s"') % {
                'sitename': config.sitename or "Wiki",
                'pagename': self.page_name,
            },
            mailBody, mail_from=request.user.email)


    def _notifySubscribers(self, request, comment):
        """ Send email to all subscribers of this page.
            Return message, indicating success or errors.
        """
        # extract categories of this page
        pageList = self.getPageLinks(request)
        CATEGORY_RE = re.compile("^Category")
        pageList = filter(CATEGORY_RE.match, pageList)
        
        # add current page name for list matching
        pageList.append(self.page_name)

        # get email addresses of the all wiki user which have a profile stored;
        # add the address only if the user has subscribed to the page and
        # the user is not the current editor
        userlist = user.getUserList()
        emails = {}
        for uid in userlist:
            if uid == request.user.id: continue # no self notification
            subscriber = user.User(uid)
            if not subscriber.email: continue # skip empty email address

            if subscriber.isSubscribedTo(pageList):                
                lang = subscriber.language or 'en'
                if not emails.has_key(lang): emails[lang] = []
                emails[lang].append(subscriber.email) 

        if emails:
            # get a list of old revisions, and append a diff
            oldversions = wikiutil.getBackupList(config.backup_dir, self.page_name)

            # send email to all subscribers 
            results = [_('Status of sending notification mails:')]
            for lang in emails.keys(): 
                status = self._sendNotification(request, comment, emails[lang], lang, oldversions)
                recipients = string.join(emails[lang], ", ")
                results.append(_('[%(lang)s] %(recipients)s: %(status)s') % locals())

            return string.join(results, '<br>')

        return _('Nobody subscribed to this page, no mail sent.')


    def _user_variable(self, request):
        """If user has a profile return the user name from the profile
           else return the remote address or "anonymous"

           If the user name contains spaces it is wiki quoted to allow
           links to the wiki user homepage (if one exists).
        """
        username = request.user.name
        if username and config.allow_extended_names and \
                string.count(username, ' ') and Page(username).exists():
            username = '["%s"]' % username
        return username or os.environ.get('REMOTE_ADDR', 'anonymous')


    def _expand_variables(self, request, text):
        """Expand @VARIABLE@ in `text`and return the expanded text."""
        #!!! TODO: Allow addition of variables via moin_config (and/or a text file)
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time()))
        system_vars = {
            'PAGE': lambda s=self: s.page_name,
            'TIME': lambda t=now: "[[DateTime(%s)]]" % t,
            'DATE': lambda t=now: "[[Date(%s)]]" % t,
            'USERNAME': lambda s=self, r=request: s._user_variable(r),
            'USER': lambda s=self, r=request: "-- %s" % (s._user_variable(r),),
            'SIG': lambda s=self, r=request, t=now: "-- %s [[DateTime(%s)]]"
                % (s._user_variable(r), t,),
        }

        if request.user.valid and request.user.name and request.user.email:
            system_vars['MAILTO'] = lambda u=request.user: \
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


    def save_text(self, request, newtext, datestamp, **kw):
        """ Save new text for a page.

            Keyword parameters:
                stripspaces - strip whitespace from line ends (default: 0)
                notify - send email notice tp subscribers (default: 0)
                comment - comment field (when preview is true)
        """
        msg = ""
        if not request.user.may.edit:
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
                newtext = self._expand_variables(request, newtext)

            # write the page file
            mtime = self._write_file(newtext)

            # write the editlog entry
            from MoinMoin import editlog
            log = editlog.makeLogStore()
            remote_name = os.environ.get('REMOTE_ADDR', '')
            log.addEntry(self.page_name, remote_name, mtime, kw.get('comment', ''))

            # add event log entry
            request.getEventLogger().add('SAVEPAGE', {'pagename': self.page_name})

            # send notification mails
            if config.mail_smarthost and kw.get('notify', 0):
                msg = msg + "<p>" + self._notifySubscribers(request, kw.get('comment', ''))

        return msg


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PageEditor class

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: PageEditor.py,v 1.67 2003/11/29 16:45:32 thomaswaldmann Exp $
"""

# Imports
import cStringIO, os, re, sys, time, urllib, cgi
from MoinMoin import caching, config, editlog, user, util, wikiutil, webapi
from MoinMoin.Page import Page
from MoinMoin.widget import html
import MoinMoin.util.web
import MoinMoin.util.mail
import MoinMoin.util.datetime


#############################################################################
### Javascript code for editor page
#############################################################################

# This code is internal to allow I18N, else we'd use a .js file;
# we avoid the "--" operator to make this XHTML happy!
_countdown_js = """
<script type="text/javascript"><!--
var timeout_min = %(lock_timeout)s;
var state = 0; // 0: start; 1: long count; 2: short count; 3: timeout; 4/5: blink
var counter = 0, step = 1, delay = 1;

function countdown() {
    // change state if counter is down
    if (counter <= 1) {
        state += 1
        if (state == 1) {
            counter = timeout_min
            step = 1
            delay = 60000
        }
        if (state == 2) {
            counter = 60
            step = 5
            delay = step * 1000
        }
        if (state == 3 || state == 5) {
            window.status = "%(lock_expire)s"
            state = 3
            counter = 1
            step = 1
            delay = 500
        }
        if (state == 4) {
            // blink the above text
            window.status = " "
            counter = 1
            delay = 250
        }
    }

    // display changes
    if (state < 3) {
        var msg
        if (state == 1) msg = "%(lock_mins)s"
        if (state == 2) msg = "%(lock_secs)s"
        window.status = msg.replace(/#/, counter)
    }
    counter -= step

    // Set timer for next update
    setTimeout("countdown()", delay)
}
//-->
</script>
"""


#############################################################################
### PageEditor - Edit pages
#############################################################################
class PageEditor(Page):
    """ Editor for a wiki page """

    def __init__(self, page_name, request, **keywords):
        """ Create page editor object.
        """
        self.request = request
        self._ = request.getText
        Page.__init__(self, page_name, **keywords)

        self.do_revision_backup = keywords.get('do_revision_backup', 1)
        self.do_editor_backup = keywords.get('do_editor_backup', 1)

        self.lock = PageLock(page_name, request)


    def sendEditor(self, **kw):
        """ Send the editor form page.

            Keywords:
                preview - if given, show this text in preview mode
                comment - comment field (when preview is true)
        """
        from cgi import escape
        try:
            from MoinMoin.action import SpellCheck
        except ImportError:
            SpellCheck = None

        form = self.request.form
        webapi.http_headers(self.request, webapi.nocache)
        msg = None
        edit_lock_message = None
        preview = kw.get('preview', None)
        emit_anchor = 1

        base_uri = "%s?action=edit" % wikiutil.quoteWikiname(self.page_name)
        backto = form.getvalue('backto', None)
        if backto:
            base_uri += '&' + util.web.makeQueryString(backto=backto)

        # check edit permissions
        if not self.request.user.may.edit(self.page_name):
            # CNC:2003-05-30
            msg = self._('<b>You are not allowed to edit this page.</b>')
        elif not self.isWritable():
            msg = self._('<b>Page is immutable!</b>')
        elif self.prev_date:
            # Trying to edit an old version, this is not possible via
            # the web interface, but catch it just in case...
            msg = self._('<b>Cannot edit old revisions!</b>')
        else:
            # try to aquire edit lock
            ok, edit_lock_message = self.lock.aquire()
            if not ok:
                # failed to get the lock
                if preview is not None:
                    edit_lock_message = self._(
                        '<strong class="highlight">The lock you held timed out, be prepared for editing conflicts!</strong><br>'
                        ) + edit_lock_message
                else:
                    msg = edit_lock_message

            if edit_lock_message.count('<strong class="highlight">'):
                emit_anchor = 0

        # Did one of the prechecks fail?
        if msg:
            self.send_page(self.request, msg=msg)
            return

        # check for preview submit
        title = self._('Edit "%(pagename)s"')
        if preview is not None:
            title = self._('Preview of "%(pagename)s"')
            self.set_raw_body(preview.replace("\r", ""))

        # send header stuff
        lock_timeout = self.lock.timeout / 60
        lock_page = cgi.escape(self.page_name, quote=1)
        lock_expire = self._("Your exclusive lock on %(lock_page)s has expired!") % locals()
        lock_mins = self._("Your edit lock on %(lock_page)s will expire in # minutes.") % locals()
        lock_secs = self._("Your edit lock on %(lock_page)s will expire in # seconds.") % locals()
        wikiutil.send_title(self.request,
            title % {'pagename': self.split_title(),},
            pagename=self.page_name, body_class="editor",
            body_onload=self.lock.locktype and 'countdown()' or '',
            html_head=self.lock.locktype and (_countdown_js % locals()) or ''
        )

        # get request parameters
        try:
            text_rows = int(form['rows'].value)
        except StandardError:
            text_rows = config.edit_rows
            if self.request.user.valid: text_rows = int(self.request.user.edit_rows)
        try:
            text_cols = int(form['cols'].value)
        except StandardError:
            text_cols = 80
            if self.request.user.valid: text_cols = int(self.request.user.edit_cols)

        # check datestamp (version) of the page our edit is based on
        if preview is not None:
            # propagate original datestamp
            mtime = int(form['datestamp'].value)

            # did someone else change the page while we were editing?
            conflict_msg = None
            if not self.exists():
                # page does not exist, are we creating it?
                if mtime:
                    conflict_msg = self._(
                        'Someone else deleted this page while you were editing!'
                        )
            elif mtime != os.path.getmtime(self._text_filename()):
                conflict_msg = self._(
                    'Someone else changed this page while you were editing!'
                    )

            if conflict_msg:
                self.request.write('<div class="message"><b>', conflict_msg, '</b></div><br>')
                emit_anchor = 0 # make this msg visible!
        elif self.exists():
            # datestamp of existing page
            mtime = os.path.getmtime(self._text_filename())
        else:
            # page creation
            mtime = 0

        # if we are using edit locking give any applicable warning
        if edit_lock_message:
            self.request.write('<div class="message">', edit_lock_message, '</div><br>')

        # get the text body for the editor field
        if form.has_key('template'):
            # "template" parameter contains the name of the template page
            template_page = wikiutil.unquoteWikiname(form['template'].value)
            raw_body = Page(template_page).get_raw_body()
            if raw_body:
                self.request.write(self._("[Content of new page loaded from %s]") % (template_page,), '<br>')
            else:
                self.request.write(self._("[Template %s not found]") % (template_page,), '<br>')
        else:
            raw_body = self.get_raw_body()

        # send text above text area
        template_param = ''
        if form.has_key('template'):
            template_param = '&template=' + form['template'].value
        self.request.write('<a href="%s&rows=10&cols=60%s">%s</a>' % (
            base_uri, template_param, self._('Reduce editor size')))
        self.request.write(" | ", wikiutil.getSysPage('HelpOnFormatting').link_to(target='_blank'))
        self.request.write(" | ", wikiutil.getSysPage('InterWiki').link_to(target='_blank'))
        if preview is not None and emit_anchor:
            self.request.write(' | <a href="#preview">%s</a>' % self._('Skip to preview'))
        self.request.write(self._('&nbsp;&nbsp; [current page size <b>%(size)d</b> bytes]') % {'size': self.size()})

        # send form
        self.request.write('<form method="post" action="%s/%s%s">' % (
            webapi.getScriptname(),
            wikiutil.quoteWikiname(self.page_name),
            '#preview',
            ))
        self.request.write(str(html.INPUT(type="hidden", name="action", value="savepage")))
        if backto:
            self.request.write(str(html.INPUT(type="hidden", name="backto", value=backto)))

        # generate default content
        if not raw_body:
            raw_body = self._('Describe %s here.') % (self.page_name,)

        # replace CRLF with LF
        raw_body = self._normalize_text(raw_body)

        # make a preview backup?
        if preview is not None:
            # make backup on previews
            self._make_backup(raw_body)

        # send datestamp (version) of the page our edit is based on
        self.request.write('<input type="hidden" name="datestamp" value="%d">' % (mtime,))

        # print the editor textarea and the save button
        self.request.write('<textarea wrap="virtual" name="savetext" rows="%d" cols="%d" style="width:100%%">%s</textarea>'
            % (text_rows, text_cols, escape(raw_body)))

        notify = ''
        if config.mail_smarthost:
            notify = '''<input type="checkbox" name="notify" value="1"%s>
                        <font face="Verdana" size="-1">%s</font><br>''' % (
                ('', ' checked')[preview is None or (form.getvalue('notify') == '1')],
                self._('Send mail notification'),
            )

        self.request.write("<br>", self._("Optional comment about this change"),
            '<br><input type="text" name="comment" value="%s" size="%d" maxlength="80" style="width:100%%">' % (
                escape(kw.get('comment', ''), 1), text_cols,))

        # category selection
        cat_pages = wikiutil.filterCategoryPages(wikiutil.getPageList(config.text_dir))
        cat_pages.sort()
        cat_pages.insert(0, ('', self._('<No addition>')))
        self.request.write("<p>", self._('Make this page belong to category %(category)s') % {
            'category': str(util.web.makeSelection('category', cat_pages)),
        })

        # button bar
        button_spellcheck = (SpellCheck and
            '<input type="submit" name="button_spellcheck" value="%s"> &nbsp; '
                % self._('Check Spelling')) or ''

        save_button_text = self._('Save Changes')
        cancel_button_text = self._('Cancel')
        if config.page_license_enabled and config.page_license_text:
            self.request.write(self._(config.page_license_text) % {
                'save_button_text': save_button_text,
                'cancel_button_text': cancel_button_text,
                'license_link': wikiutil.getSysPage(config.page_license_page).link_to(),
            })
            
        self.request.write('''
<div style="margin-top:6pt;margin-bottom:6pt;">
<input type="submit" name="button_save" value="%s"> &nbsp;
<input type="submit" name="button_preview" value="%s"> &nbsp; %s&nbsp; &nbsp; &nbsp;
<input type="submit" name="button_cancel" value="%s">
</div>''' % (save_button_text, self._('Preview'), button_spellcheck, cancel_button_text,))

        self.request.write('''%s
<input type="checkbox" name="rstrip" value="1"%s>
<font face="Verdana" size="-1">%s</font>
''' % (     notify,
            ('', ' checked')[preview is not None and (form.getvalue('rstrip') == '1')],
            self._('Remove trailing whitespace from each line')
        ))

        badwords_re = None
        if preview is not None:
            if SpellCheck and (
                    form.has_key('button_spellcheck') or
                    form.has_key('button_newwords')):
                badwords, badwords_re, msg = SpellCheck.checkSpelling(self, self.request, own_form=0)
                self.request.write("<p>", msg)
        self.request.write("</form>")

        # QuickHelp originally by Georg Mischler <schorsch@lightingwiki.com>
        self.request.write(self._("""<hr>
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
"""))

        if preview is not None:
            self.request.write('<hr>')
            if emit_anchor:
                self.request.write('<a name="preview"></a>')
            self.request.write(
                '<table border="0" cellspacing="0" cellpadding="3" bgcolor="#F4F4F4"'
                    ' style="background-image:url(%s/img/draft.png); background-color:#F4F4F4;">'
                '<tr><td>' % config.url_prefix)
            self.send_page(self.request, content_only=1, hilite_re=badwords_re)
            self.request.write('</td></tr></table>')

        print '<a name="bottom"></a>'
        wikiutil.emit_custom_html(self.request, config.page_footer1)
        wikiutil.emit_custom_html(self.request, config.page_footer2)
    
    def sendCancel(self, newtext, datestamp):
        """ User clicked on Cancel button. If edit locking is active,
            delete the current lock file.
        """
        self._make_backup(self._normalize_text(newtext))
        self.lock.release()

        backto = self.request.form.getvalue('backto', None)
        page = backto and Page(backto) or self
        page.send_page(self.request, msg=self._('Edit was cancelled.'))


    def deletePage(self, comment=None):
        """Delete the page (but keep the backups)"""
        # !!! Need to aquire lock for this, and possibly BEFORE user pressed DELETE.
        # !!! Possibly with shorter timeout.

        # First save a final backup copy of the current page
        # (recreating the page allows access to the backups again)
        self.saveText("deleted", '0', comment=comment or '')

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


    def _sendNotification(self, comment, emails, email_lang, oldversions):
        """ Send notification email for a single language.

            Returns sendmail result.
        """
        _ = lambda s, r=self.request, l=email_lang: r.getText(s, lang=l)

        mailBody = _("Dear Wiki user,\n\n"
            'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
            "The following page has been changed by %(editor)s:\n"
            "%(pagelink)s\n\n") % {
                'editor': user.getUserIdentification(self.request),
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
                    mailBody, ("-" * 78), ''.join(lines[2:]))
            else:
                mailBody = mailBody + _("No differences found!\n")
                if rc:
                    mailBody = mailBody + '\n\n' + \
                        _('The external diff utility returned with error code %(rc)s!') % locals()

        return util.mail.sendmail(self.request, emails,
            _('[%(sitename)s] Update of "%(pagename)s"') % {
                'sitename': config.sitename or "Wiki",
                'pagename': self.page_name,
            },
            mailBody, mail_from=config.mail_from)
            # was: self.request.user.email, but we don't want to disclose email


    def _notifySubscribers(self, comment):
        """ Send email to all subscribers of this page.
            Return message, indicating success or errors.
        """
        subscribers = self.getSubscribers(self.request, return_users=1)

        wiki_is_smarter_than_its_users = self._(
            "<p><b>You will not be notified of your own changes!</b></p>"
        )

        if subscribers:
            # get a list of old revisions, and append a diff
            oldversions = wikiutil.getBackupList(config.backup_dir, self.page_name)

            # send email to all subscribers
            results = [self._('Status of sending notification mails:')]
            for lang in subscribers.keys():
                emails = map(lambda u: u.email, subscribers[lang])
                names  = map(lambda u: u.name,  subscribers[lang])
                mailok, status = self._sendNotification(comment, emails, lang, oldversions)
                recipients = ", ".join(names)
                results.append(self._('[%(lang)s] %(recipients)s: %(status)s') % locals())

            return wiki_is_smarter_than_its_users + '<br>'.join(results)

        return wiki_is_smarter_than_its_users + self._('Nobody subscribed to this page, no mail sent.')


    def _user_variable(self):
        """If user has a profile return the user name from the profile
           else return the remote address or "<unknown>"

           If the user name contains spaces it is wiki quoted to allow
           links to the wiki user homepage (if one exists).
        """
        username = self.request.user.name
        if username and config.allow_extended_names and \
                username.count(' ') and Page(username).exists():
            username = '["%s"]' % username
        return user.getUserIdentification(self.request, username)


    def _expand_variables(self, text):
        """Expand @VARIABLE@ in `text`and return the expanded text."""
        #!!! TODO: Allow addition of variables via moin_config (and/or a text file)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", util.datetime.tmtuple())
        system_vars = {
            'PAGE': lambda s=self: s.page_name,
            'TIME': lambda t=now: "[[DateTime(%s)]]" % t,
            'DATE': lambda t=now: "[[Date(%s)]]" % t,
            'USERNAME': lambda s=self: s._user_variable(),
            'USER': lambda s=self: "-- %s" % (s._user_variable(),),
            'SIG': lambda s=self, t=now: "-- %s [[DateTime(%s)]]"
                % (s._user_variable(), t,),
        }

        if self.request.user.valid and self.request.user.name and self.request.user.email:
            system_vars['MAILTO'] = lambda u=self.request.user: \
                "[mailto:%s %s]" % (u.email, u.name)
        #!!! TODO: Use a more stream-lined re.sub algorithm
        for name, val in system_vars.items():
            text = text.replace('@' + name + '@', val())
        return text


    def _normalize_text(self, newtext, **kw):
        """Normalize CRLF to LF, and handle trailing whitespace."""
        # remove CRs (so Win32 and Unix users save the same text)
        newtext = newtext.replace("\r", "")

        # possibly strip trailing spaces
        if kw.get('stripspaces', 0):
            newtext = '\n'.join([line.rstrip() for line in newtext.splitlines()])

        # add final newline if not present in textarea, better for diffs
        # (does not include former last line when just adding text to
        # bottom; idea by CliffordAdams)
        if newtext and newtext[-1] != '\n':
            newtext = newtext + '\n'

        return newtext


    def _make_backup(self, newtext, **kw):
        """ Make a backup of text before saving and on previews, if user
            has a homepage. Return URL to backup if one is made.
        """
        # check for homepage
        pg = wikiutil.getHomePage(self.request)
        if not pg or not self.do_editor_backup:
            return None
    
        """ new code, acl-safe """
        if config.allow_subpages:
            delimiter = "/"
        else:
            delimiter = ""
        backuppage = PageEditor(pg.page_name + delimiter + "MoinEditorBackup", self.request)
        if config.acl_enabled:
            intro = "#acl %s:read,write,delete\n" % self.request.user.name
        else:
            intro = ""
        pagename = self.page_name
        date = self.request.user.getFormattedDateTime(time.time())
        intro += self._('## backup of page "%(pagename)s" submitted %(date)s\n') % locals()
        backuppage._write_file(intro + newtext)
        return backuppage.url()


    def _write_file(self, text):
        is_deprecated = text[:11].lower() == "#deprecated"

        # save to tmpfile
        tmp_filename = self._tmp_filename()
        tmp_file = open(tmp_filename, 'wb')
        tmp_file.write(text)
        tmp_file.close()
        page_filename = self._text_filename()

        if not os.path.isdir(config.backup_dir):
            os.mkdir(config.backup_dir, 0777 & config.umask)
            os.chmod(config.backup_dir, 0777 & config.umask)

        if os.path.isfile(page_filename) and not is_deprecated and self.do_revision_backup:
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


    def saveText(self, newtext, datestamp, **kw):
        """ Save new text for a page.

            Keyword parameters:
                stripspaces - strip whitespace from line ends (default: 0)
                notify - send email notice tp subscribers (default: 0)
                comment - comment field (when preview is true)
                action - action for editlog (default: SAVE)
        """
        newtext = self._normalize_text(newtext, **kw)
        backup_url = self._make_backup(newtext, **kw)

        #!!! need to check if we still retain the lock here
        #!!! datestamp check is not enough since internal operations use "0"

        # expand variables, unless it's a template or form page
        if not (wikiutil.isTemplatePage(self.page_name) or
                wikiutil.isFormPage(self.page_name)):
            newtext = self._expand_variables(newtext)

        msg = ""
        if not self.request.user.may.save(self, newtext, datestamp, **kw):
            msg = self._("""<b>You are not allowed to edit any pages.</b>""")
        elif not self.isWritable():
            msg = self._('<b>Page is immutable!</b>')
        elif not newtext:
            msg = self._("""<b>You cannot save empty pages.</b>""")
        elif datestamp != '0' and datestamp != str(os.path.getmtime(self._text_filename())):
            msg = self._("""<b>Sorry, someone else saved the page while you edited it.
<p>Please do the following: Use the back button of your browser, and cut&paste
your changes from there. Then go forward to here, and click EditText again.
Now re-add your changes to the current page contents.
<p><em>Do not just replace
the content editbox with your version of the page, because that would
delete the changes of the other person, which is excessively rude!</em></b>
""")

            if backup_url:
                msg += self._('<p><b>A backup of your changes is'
                    ' <a href="%(backup_url)s">here</a>.</b></p>') % locals()
        elif newtext == self.get_raw_body():
            msg = self._("""<b>You did not change the page content, not saved!</b>""")
        # CNC:2003-06-03
        elif config.acl_enabled:
            from wikiacl import parseACL
            acl = self.getACL(self.request)
            if not acl.may(self.request.user.name, "admin") \
               and parseACL(self.request, newtext) != acl:
                msg = self._("<b>You can't change ACLs on this page since "
                             "you have no admin rights on it!</b>")

        # save only if no error occured (msg is empty)
        if not msg:
            # set success msg
            msg = self._(
                "<b>Thank you for your changes.\n"
                "Your attention to detail is appreciated.</b>"
            )

            # write the page file
            mtime = self._write_file(newtext)
            if self._acl_cache.has_key(self.page_name):
                del self._acl_cache[self.page_name]

            # write the editlog entry
            log = editlog.makeLogStore(self.request)
            log.addEntry(self.page_name, None, mtime,
                kw.get('comment', ''), action=kw.get('action', 'SAVE'))

            # add event log entry
            self.request.getEventLogger().add('SAVEPAGE', {'pagename': self.page_name})

            # send notification mails
            if config.mail_smarthost and kw.get('notify', 0):
                msg = msg + "<p>" + self._notifySubscribers(kw.get('comment', ''))

        # remove lock (forcibly if we were allowed to break it by the UI)
        # !!! this is a little fishy, since the lock owner might not notice
        # we broke his lock ==> but datestamp checking during preview will
        self.lock.release(force=not msg) # XXX does "not msg" make any sense?

        return msg


#############################################################################
### PageLock - Lock pages
#############################################################################

#!!! race conditions throughout, need to lock file during queries & update
class PageLock:

    def __init__(self, pagename, request):
        self.page_name = pagename
        self.request = request
        self._ = request.getText

        # current time and user for later checks
        self.now = time.time()
        self.uid = request.user.valid and request.user.id or os.environ.get('REMOTE_ADDR', '')

        # get details of the locking preference, i.e. warning or lock, and timeout
        self.locktype = None
        self.timeout = 10 * 60 # default timeout in minutes

        if config.edit_locking:
            lockinfo = config.edit_locking.split()
            if 1 <= len(lockinfo) <= 2:
                self.locktype = lockinfo[0].lower()
                if len(lockinfo) > 1:
                    try:
                        self.timeout = int(lockinfo[1]) * 60
                    except ValueError:
                        pass


    def aquire(self):
        """ Begin an edit lock depending on the mode chosen in the config.

            A tuple is returned containing 2 values:
              * a bool indicating successful aquiry
              * a string giving a reason for failure or an informational msg
        """
        if not self.locktype:
            # we are not using edit locking, so always succeed
            return 1, ''

        #!!! race conditions, need to lock file during queries & update
        self._readLockFile()
        bumptime = self.request.user.getFormattedDateTime(self.now + self.timeout)
        timestamp = self.request.user.getFormattedDateTime(self.timestamp)
        owner = self.owner_html
        secs_valid = self.timestamp + self.timeout - self.now

        # do we own the lock, or is it stale?
        if self.owner is None or self.uid == self.owner or secs_valid < 0:
            # create or bump the lock
            self._writeLockFile()

            msg = []
            if self.owner is not None and -36000 < secs_valid < 0:
                mins_ago = secs_valid / -60
                msg.append(self._(
                    "The lock of %(owner)s timed out %(mins_ago)d minute(s) ago,"
                    " and you were granted the lock for this page."
                    ) % locals())

            if self.locktype == 'lock':
                msg.append(self._(
                    "Other users will be <b>blocked</b> from editing this page until %(bumptime)s."
                    ) % locals())
            else:
                msg.append(self._(
                    "Other users will be <b>warned</b> until %(bumptime)s that you are editing this page."
                    ) % locals())
            msg.append(self._(
                "Use the Preview button to extend the locking period."
                ))
            result = 1, '\n'.join(msg)
        else:
            mins_valid = (secs_valid+59) / 60
            if self.locktype == 'lock':
                # lout out user
                result = 0, self._(
                    "This page is currently <b>locked</b> for editing by %(owner)s until %(timestamp)s,"
                    " i.e. for %(mins_valid)d minute(s)."
                    ) % locals()
            else:
                # warn user about existing lock
                result = 1, self._(
                    'This page was opened for editing or last previewed at %(timestamp)s by %(owner)s.<br>\n'
                    '<strong class="highlight">'
                    'You should <em>refrain from editing</em> this page for at least another %(mins_valid)d minute(s),\n'
                    'to avoid editing conflicts.'
                    '</strong><br>\n'
                    'To leave the editor, press the Cancel button.'
                    ) % locals()

        return result


    def release(self, force=0):
        """ Release lock, if we own it (unless `force` is true).
        """
        if self.locktype:
            # check that we own the lock in order to delete it
            #!!! race conditions, need to lock file during queries & update
            self._readLockFile()
            if force or self.uid == self.owner:
                self._deleteLockFile()


    def _filename(self):
        return wikiutil.getPagePath(self.page_name, 'edit-lock')


    def _readLockFile(self):
        """ Load lock info if not yet loaded.
        """
        import cgi

        self.owner = None
        self.owner_html = cgi.escape(self._("<unknown>"))
        self.timestamp = 0

        if self.locktype:
            entry = editlog.loadLogEntry(self.request, self._filename())
            if entry:
                self.owner = entry.userid or entry.addr
                self.owner_html = entry.getEditor()
                self.timestamp = long(entry.ed_time)


    def _writeLockFile(self):
        """ Write new lock file.
        """
        lockfile = open(self._filename(), 'w')
        try:
            line = editlog.makeLogEntry(self.request,
                self.page_name, None, self.now, '', action="LOCK")
            lockfile.write(line)
        finally:
            lockfile.close()


    def _deleteLockFile(self):
        """ Delete the lock file unconditionally.
        """
        try:
            os.remove(self._filename())
        except OSError:
            pass

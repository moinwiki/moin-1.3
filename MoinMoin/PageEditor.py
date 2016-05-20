# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PageEditor class

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, time, codecs, re

from MoinMoin import caching, config, user, util, wikiutil, error
from MoinMoin.Page import Page
from MoinMoin.widget import html
from MoinMoin.widget.dialog import Status
from MoinMoin.logfile import editlog, eventlog
from MoinMoin.util import filesys
import MoinMoin.util.web
import MoinMoin.util.mail
import MoinMoin.util.datetime


#############################################################################
### Javascript code for editor page
#############################################################################

# This code is internal to allow I18N, else we'd use a .js file;
# we avoid the "--" operator to make this XHTML happy!
_countdown_js = """
<script type="text/javascript">
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
</script>
"""


#############################################################################
### PageEditor - Edit pages
#############################################################################
class PageEditor(Page):
    """Editor for a wiki page."""

    # exceptions for .saveText()

    class SaveError(error.Error):
        pass
    class AccessDenied(SaveError):
        pass
    class Immutable(AccessDenied):
        pass
    class NoAdmin(AccessDenied):
        pass
    class EmptyPage(SaveError):
        pass
    class Unchanged(SaveError):
        pass
    class EditConflict(SaveError):
        pass
    class CouldNotLock(SaveError):
        pass

    def __init__(self, request, page_name, **keywords):
        """
        Create page editor object.
        
        @param page_name: name of the page
        @param request: the request object
        @keyword do_revision_backup: if 0, suppress making a page backup per revision
        @keyword do_editor_backup: if 0, suppress making of HomePage/MoinEditorBackup per edit
        @keyword uid_override: override user id and name (default None)
        """
        Page.__init__(self, request, page_name, **keywords)
        
        # already done:
        #self.request = request
        #self.cfg = request.cfg
        
        self._ = request.getText

        self.do_revision_backup = keywords.get('do_revision_backup', 1)
        self.do_editor_backup = keywords.get('do_editor_backup', 1)
        self.uid_override = keywords.get('uid_override', None)

        self.lock = PageLock(self)

    def mergeEditConflict(self, origrev):
        """ Try to merge current page version with new version the user tried to save

        @param origrev: the original revision the user was editing
        @rtype: bool
        @return: merge success status
        """
        from MoinMoin.util import diff3
        allow_conflicts = 1

        # Get current editor text
        savetext = self.get_raw_body()
        
        # The original text from the revision the user was editing
        original_text = Page(self.request, self.page_name, rev=origrev).get_raw_body()
        
        # The current revision someone else saved
        saved_text = Page(self.request, self.page_name).get_raw_body()
        
        # And try to merge all into one with edit conflict separators
        verynewtext = diff3.text_merge(original_text, saved_text, savetext,
                                       allow_conflicts,
                                       "\n---- /!\ '''Edit conflict - other version:''' ----\n",
                                       "\n---- /!\ '''Edit conflict - your version:''' ----\n",
                                       "\n---- /!\ '''End of edit conflict''' ----\n")
        if verynewtext:
            self.set_raw_body(verynewtext)
            return True

        return False

    def sendEditor(self, **kw):
        """
        Send the editor form page.

        @keyword preview: if given, show this text in preview mode
        @keyword staytop: don't go to #preview
        @keyword comment: comment field (when preview is true)
        """
        from MoinMoin import i18n
        try:
            from MoinMoin.action import SpellCheck
        except ImportError:
            SpellCheck = None

        form = self.request.form
        _ = self._
        self.request.http_headers(self.request.nocache)

        msg = None
        conflict_msg = None
        edit_lock_message = None
        preview = kw.get('preview', None)
        emit_anchor = not kw.get('staytop', 0)

        from MoinMoin.formatter.text_html import Formatter
        self.request.formatter = Formatter(self.request, store_pagelinks=1)

        # check edit permissions
        if not self.request.user.may.write(self.page_name):
            msg = _('You are not allowed to edit this page.')
        elif not self.isWritable():
            msg = _('Page is immutable!')
        elif self.rev:
            # Trying to edit an old version, this is not possible via
            # the web interface, but catch it just in case...
            msg = _('Cannot edit old revisions!')
        else:
            # try to acquire edit lock
            ok, edit_lock_message = self.lock.aquire()
            if not ok:
                # failed to get the lock
                if preview is not None:
                    edit_lock_message = _('The lock you held timed out, be prepared for editing conflicts!'
                        ) + "<br>" + edit_lock_message
                else:
                    msg = edit_lock_message

        # Did one of the prechecks fail?
        if msg:
            self.send_page(self.request, msg=msg)
            return

        # Check for preview submit
        if preview is None:
            title = _('Edit "%(pagename)s"')
        else:
            title = _('Preview of "%(pagename)s"')
            self.set_raw_body(preview, modified=1)

        # send header stuff
        lock_timeout = self.lock.timeout / 60
        lock_page = wikiutil.escape(self.page_name, quote=1)
        lock_expire = _("Your edit lock on %(lock_page)s has expired!") % {'lock_page': lock_page}
        lock_mins = _("Your edit lock on %(lock_page)s will expire in # minutes.") % {'lock_page': lock_page}
        lock_secs = _("Your edit lock on %(lock_page)s will expire in # seconds.") % {'lock_page': lock_page}
                
        # get request parameters
        try:
            text_rows = int(form['rows'][0])
        except StandardError:
            text_rows = self.cfg.edit_rows
            if self.request.user.valid:
                text_rows = int(self.request.user.edit_rows)

        if preview is not None:
            # Propagate original revision
            rev = int(form['rev'][0])
            
            # Check for editing conflicts
            if not self.exists():
                # page does not exist, are we creating it?
                if rev:
                    conflict_msg = _('Someone else deleted this page while you were editing!')
            elif rev != self.current_rev():
                conflict_msg = _('Someone else changed this page while you were editing!')
                if self.mergeEditConflict(rev):
                    conflict_msg = _("""Someone else saved this page while you were editing!
Please review the page and save then. Do not save this page as it is!
Have a look at the diff of %(difflink)s to see what has been changed.""") % {
                        'difflink': self.link_to(self.request,
                                                 querystr='action=diff&rev=%d' % rev)
                        }
                    rev = self.current_rev()
            if conflict_msg:
                # We don't show preview when in conflict
                preview = None
                
        elif self.exists():
            # revision of existing page
            rev = self.current_rev()
        else:
            # page creation
            rev = 0

        # Page editing is done using user language
        self.request.setContentLanguage(self.request.lang)

        # Setup status message
        status = [kw.get('msg', ''), conflict_msg, edit_lock_message]
        status = [msg for msg in status if msg]
        status = ' '.join(status)
        status = Status(self.request, content=status)
        
        wikiutil.send_title(self.request,
            title % {'pagename': self.split_title(self.request),},
            page=self,
            pagename=self.page_name, msg=status,
            body_onload=self.lock.locktype and 'countdown()' or '', # broken / bug in Mozilla 1.5, when using #preview
            html_head=self.lock.locktype and (
                _countdown_js % {
                     'lock_timeout': lock_timeout,
                     'lock_expire': lock_expire,
                     'lock_mins': lock_mins,
                     'lock_secs': lock_secs,
                    }) or ''
        )
        
        self.request.write(self.request.formatter.startContent("content"))
        
        # get the text body for the editor field
        if form.has_key('template'):
            # "template" parameter contains the name of the template page
            template_page = wikiutil.unquoteWikiname(form['template'][0])
            if self.request.user.may.read(template_page):
                raw_body = Page(self.request, template_page).get_raw_body()
                if raw_body:
                    self.request.write(_("[Content of new page loaded from %s]") % (template_page,), '<br>')
                else:
                    self.request.write(_("[Template %s not found]") % (template_page,), '<br>')
            else:
                raw_body = ''
                self.request.write(_("[You may not read %s]") % (template_page,), '<br>')
        else:
            raw_body = self.get_raw_body()

        # send text above text area
        template_param = ''
        if form.has_key('template'):
            template_param = '&amp;template=' + form['template'][0]
        self.request.write('<p>')
        self.request.write(wikiutil.getSysPage(self.request, 'HelpOnFormatting').link_to(self.request))
        self.request.write(" | ", wikiutil.getSysPage(self.request, 'InterWiki').link_to(self.request))
        if preview is not None and emit_anchor:
            self.request.write(' | <a href="#preview">%s</a>' % _('Skip to preview'))
        self.request.write(' ')
        self.request.write(_('[current page size \'\'\'%(size)d\'\'\' bytes]') % {'size': self.size()})
        self.request.write('</p>')
        
        # send form
        self.request.write('<form id="editor" method="post" action="%s/%s#preview">' % (
            self.request.getScriptname(),
            wikiutil.quoteWikinameURL(self.page_name),
            ))

        # yet another weird workaround for broken IE6 (it expands the text
        # editor area to the right after you begin to type...). IE sucks...
        # http://fplanque.net/2003/Articles/iecsstextarea/
        self.request.write('<fieldset style="border:none;padding:0;">')
        
        self.request.write('<p>')
        self.request.write(unicode(html.INPUT(type="hidden", name="action", value="savepage")))

        # Save backto in a hidden input
        backto = form.get('backto', [None])[0]
        if backto:
            self.request.write(unicode(html.INPUT(type="hidden", name="backto", value=backto)))

        # Make backup on previews - but not for new empty pages
        if preview and raw_body:
            self._make_backup(raw_body)

        # Generate default content for new pages
        if not raw_body:
            raw_body = _('Describe %s here.') % (self.page_name,)

        # Send revision of the page our edit is based on
        self.request.write('<input type="hidden" name="rev" value="%d">' % (rev,))

        # Add textarea with page text

        # TODO: currently self.language is None at this point. We have
        # to do processing instructions parsing earlier, or move page
        # language into meta file.
        lang = self.language or self.request.cfg.default_lang

        self.request.write(
            u'<textarea id="editor-textarea" name="savetext" lang="%(lang)s" dir="%(dir)s"'
            u' rows="%(rows)d">' % {
            'lang': lang,
            'dir': i18n.getDirection(lang),
            'rows': text_rows,
            }
            )
        self.request.write(wikiutil.escape(raw_body))
        self.request.write(u'</textarea>')

        self.request.write('</p>')

        self.request.write("<p>", _("Optional comment about this change"),
            '<br><input id="editor-comment" type="text" name="comment" value="%s" maxlength="80"></p>' % (
                wikiutil.escape(kw.get('comment', ''), 1), ))

        # Category selection
        filter = re.compile(self.cfg.page_category_regex, re.UNICODE).search
        cat_pages = self.request.rootpage.getPageList(filter=filter)
        cat_pages.sort()
        cat_pages = [wikiutil.pagelinkmarkup(p) for p in cat_pages]
        cat_pages.insert(0, ('', _('<No addition>', formatted=False)))
        self.request.write("<p>", _('Make this page belong to category %(category)s') % {
            'category': unicode(util.web.makeSelection('category', cat_pages)),
        })

        # button bar
        button_spellcheck = (SpellCheck and
            '<input type="submit" name="button_spellcheck" value="%s">'
                % _('Check Spelling')) or ''

        save_button_text = _('Save Changes')
        cancel_button_text = _('Cancel')
        
        self.request.write("</p>")
            
        if self.cfg.page_license_enabled:
            self.request.write('<p><em>', _(
"""By hitting '''%(save_button_text)s''' you put your changes under the %(license_link)s.
If you don't want that, hit '''%(cancel_button_text)s''' to cancel your changes.""") % {
                'save_button_text': save_button_text,
                'cancel_button_text': cancel_button_text,
                'license_link': wikiutil.getSysPage(self.request, self.cfg.page_license_page).link_to(self.request),
            }, '</em></p>')

        self.request.write('''
<p>
<input type="submit" name="button_save" value="%s">
<input type="submit" name="button_preview" value="%s"> %s
<input type="submit" name="button_cancel" value="%s">
</p>
<p>
''' % (save_button_text, _('Preview'), button_spellcheck, cancel_button_text,))

        if self.cfg.mail_smarthost:
            self.request.write('''
<input type="checkbox" name="trivial" value="1" %(checked)s>
<label>%(label)s</label> ''' % {
                'checked': ('', 'checked')[form.get('trivial',['0'])[0] == '1'],
                'label': _("Trivial change"),
                })

        self.request.write('''
<input type="checkbox" name="rstrip" value="1" %(checked)s>
<label>%(label)s</label>
</p> ''' % {
            'checked': ('', 'checked')[form.get('rstrip',['0'])[0] == '1'],
            'label': _('Remove trailing whitespace from each line')
            })

        badwords_re = None
        if preview is not None:
            if SpellCheck and (
                    form.has_key('button_spellcheck') or
                    form.has_key('button_newwords')):
                badwords, badwords_re, msg = SpellCheck.checkSpelling(self, self.request, own_form=0)
                self.request.write("<p>%s</p>" % msg)
        self.request.write('</fieldset>')
        self.request.write("</form>")
        
        # QuickHelp originally by Georg Mischler <schorsch@lightingwiki.com>
        self.request.write('<hr>\n<dl>' + _(""" Emphasis:: [[Verbatim('')]]''italics''[[Verbatim('')]]; [[Verbatim(''')]]'''bold'''[[Verbatim(''')]]; [[Verbatim(''''')]]'''''bold italics'''''[[Verbatim(''''')]]; [[Verbatim('')]]''mixed ''[[Verbatim(''')]]'''''bold'''[[Verbatim(''')]] and italics''[[Verbatim('')]]; [[Verbatim(----)]] horizontal rule.
 Headings:: [[Verbatim(=)]] Title 1 [[Verbatim(=)]]; [[Verbatim(==)]] Title 2 [[Verbatim(==)]]; [[Verbatim(===)]] Title 3 [[Verbatim(===)]];   [[Verbatim(====)]] Title 4 [[Verbatim(====)]]; [[Verbatim(=====)]] Title 5 [[Verbatim(=====)]].
 Lists:: space and one of: * bullets; 1., a., A., i., I. numbered items; 1.#n start numbering at n; space alone indents.
 Links:: [[Verbatim(JoinCapitalizedWords)]]; [[Verbatim(["brackets and double quotes"])]]; url; [url]; [url label].
 Tables:: || cell text |||| cell text spanning 2 columns ||;    no trailing white space allowed after tables or titles.""")
 + '</dl>')

        if preview is not None:
            self.send_page(self.request, content_id='preview', content_only=1,
                           hilite_re=badwords_re)

        self.request.write(self.request.formatter.endContent()) # end content div
        self.request.theme.emit_custom_html(self.cfg.page_footer1)
        self.request.theme.emit_custom_html(self.cfg.page_footer2)


    def sendCancel(self, newtext, rev):
        """
        User clicked on Cancel button. If edit locking is active,
        delete the current lock file.
        
        @param newtext: the edited text (which has been cancelled)
        @param rev: not used!?
        """
        _ = self._
        self._make_backup(newtext)
        self.lock.release()

        backto = self.request.form.get('backto', [None])[0]
        page = backto and Page(self.request, backto) or self
        page.send_page(self.request, msg=_('Edit was cancelled.'))

    def deletePage(self, comment=None):
        """
        Delete the current version of the page (making a backup before deletion
        and keeping the backups, logs and attachments).
        
        @param comment: Comment given by user
        """
        # First save a final backup copy of the current page
        # (recreating the page allows access to the backups again)
        try:
            self.saveText(u"deleted\n", 0, comment=comment or u'')
        except self.SaveError, msg:
            # XXX Error handling
            pass
        # Then really delete it
        try:
            os.remove(self._text_filename())
        except OSError, er:
            import errno
            if er.errno != errno.ENOENT: raise er
        
        # reset page object
        self.reset()
        
        # delete pagelinks
        arena = self
        key = 'pagelinks'
        cache = caching.CacheEntry(self.request, arena, key)
        cache.remove()

        # forget in-memory page text
        self.set_raw_body(None)
        
        # clean the in memory acl cache
        self.clean_acl_cache()

        # clean the cache
        for formatter_name in self.cfg.caching_formats:
            arena = self
            key = formatter_name
            cache = caching.CacheEntry(self.request, arena, key)
            cache.remove()

    def _sendNotification(self, comment, emails, email_lang, revisions, trivial):
        """
        Send notification email for a single language.
        @param comment: editor's comment given when saving the page
        @param emails: list of email addresses
        @param email_lang: language of emails
        @param revisions: revisions of this page
        @param trivial: the change is marked as trivial
        @rtype: int
        @return: sendmail result
        """
        _ = lambda s, formatted=True, r=self.request, l=email_lang: r.getText(s, formatted=formatted, lang=l)

        mailBody = _("Dear Wiki user,\n\n"
            'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
            "The following page has been changed by %(editor)s:\n"
            "%(pagelink)s\n\n", formatted=False) % {
                'editor': self.uid_override or user.getUserIdentification(self.request),
                'pagelink': self.request.getQualifiedURL(self.url(self.request)),
                'sitename': self.cfg.sitename or self.request.getBaseURL(),
        }

        if comment:
            mailBody = mailBody + \
                _("The comment on the change is:\n%(comment)s\n\n", formatted=False) % {'comment': comment}

        # append a diff (or append full page text if there is no diff)
        if len(revisions) < 2:
            mailBody = mailBody + \
                _("New page:\n", formatted=False) + \
                self.get_raw_body()
        else:
            lines = wikiutil.pagediff(self.request, self.page_name, revisions[1],
                                      self.page_name, revisions[0])
            
            if lines:
                mailBody = mailBody + "%s\n%s\n" % (("-" * 78), '\n'.join(lines))
            else:
                mailBody = mailBody + _("No differences found!\n", formatted=False)
        
        return util.mail.sendmail(self.request, emails,
            _('[%(sitename)s] %(trivial)sUpdate of "%(pagename)s" by %(username)s', formatted=False) % {
                'trivial' : (trivial and _("Trivial ", formatted=False)) or "",
                'sitename': self.cfg.sitename or "Wiki",
                'pagename': self.page_name,
                'username': self.uid_override or user.getUserIdentification(self.request),
            },
            mailBody, mail_from=self.cfg.mail_from)


    def _notifySubscribers(self, comment, trivial):
        """
        Send email to all subscribers of this page.

        @param comment: editor's comment given when saving the page
        @param trivial: editor's suggestion that the change is trivial (Subscribers may ignore this)
        @rtype: string
        @return: message, indicating success or errors.
        """
        _ = self._
        subscribers = self.getSubscribers(self.request, return_users=1,
                                          trivial=trivial)
        if subscribers:
            # get a list of old revisions, and append a diff
            revisions = self.getRevList()

            # send email to all subscribers
            results = [_('Status of sending notification mails:')]
            for lang in subscribers.keys():
                emails = map(lambda u: u.email, subscribers[lang])
                names  = map(lambda u: u.name,  subscribers[lang])
                mailok, status = self._sendNotification(comment, emails, lang, revisions, trivial)
                recipients = ", ".join(names)
                results.append(_('[%(lang)s] %(recipients)s: %(status)s') % {
                    'lang': lang, 'recipients': recipients, 'status': status})

            # Return mail sent results. Ignore trivial - we don't have
            # to lie. If mail was sent, just tell about it.
            return '<p>\n%s\n</p> ' % '<br>'.join(results) 

        # No mail sent, no message.
        return ''


    def _user_variable(self):
        """
        If user has a profile return the user name from the profile
        else return the remote address or "<unknown>"

        If the user name contains spaces it is wiki quoted to allow
        links to the wiki user homepage (if one exists).
        
        @rtype: string
        @return: wiki freelink to user's homepage or remote address
        """
        username = self.request.user.name
        if username and self.cfg.allow_extended_names and \
                username.count(' ') and Page(self.request, username).exists():
            username = '["%s"]' % username
        return user.getUserIdentification(self.request, username)


    def _expand_variables(self, text):
        """
        Expand @VARIABLE@ in `text`and return the expanded text.
        
        @param text: current text of wikipage
        @rtype: string
        @return: new text of wikipage, variables replaced
        """
        #!!! TODO: Allow addition of variables via wikiconfig (and/or a text file)
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

        if self.request.user.valid and self.request.user.name:
            if self.request.user.email:
                system_vars['MAILTO'] = lambda u=self.request.user: \
                    "[mailto:%s %s]" % (u.email, u.name)
            # users can define their own vars via UserHomepage/MyDict
            uservarspagename = self.request.user.name + "/MyDict"
            dicts = self.request.dicts
            if dicts.has_dict(uservarspagename):
                userdict = dicts.dict(uservarspagename)
                for key in userdict.keys():
                    text = text.replace('@%s@' % key, userdict[key])
                    
        # TODO: Use a more stream-lined re.sub algorithm
        for name, val in system_vars.items():
            text = text.replace('@%s@' % name, val())
        return text

    def normalizeText(self, text, **kw):
        """ Normalize text

        Make sure text uses '\n' line endings, and has a trailing
        newline. Strip whitespace on end of lines if needed.

        You should normalize any text you enter into a page, for
        example, when getting new text from the editor, or when setting
        new text manually.
                
        @param text: text to normalize (unicode)
        @keyword stripspaces: if 1, strip spaces from text
        @rtype: unicode
        @return: normalized text
        """     
        if text:
            lines = text.splitlines()            
            # Strip trailing spaces if needed
            if kw.get('stripspaces', 0):
                lines = [line.rstrip() for line in lines]

            # Add final newline if not present, better for diffs (does
            # not include former last line when just adding text to
            # bottom; idea by CliffordAdams)
            if not lines[-1] == u'':
                # '' will make newline after join
                lines.append(u'')

            text = u'\n'.join(lines)
        return text

    def _make_backup(self, newtext, **kw):
        """ Make editor backup on user homepage

        Replace text of the user UserName/MoinEditorBackup with newtext.

        @param newtext: new text of the page
        @keyword: none used currently
        @rtype: unicode
        @return: url of page backup or None
        """
        # Backup only if set to backup and user has a home page.
        homepage = wikiutil.getHomePage(self.request)
        if not homepage or not self.do_editor_backup:
            return None
        
        _ = self._
        if config.allow_subpages:
            delimiter = "/"
        else:
            delimiter = ""
        backuppage = PageEditor(self.request,
                                homepage.page_name + delimiter + "MoinEditorBackup",
                                do_revision_backup=0)
        if self.cfg.acl_enabled:
            # We need All: at the end to prevent that the original page ACLs
            # make it possible to see preview saves (that maybe were never
            # really saved by the author).
            intro = u"#acl %s:read,write,delete All:\n" % self.request.user.name
        else:
            intro = ""
        pagename = self.page_name
        date = self.request.user.getFormattedDateTime(time.time())
        intro += _('## backup of page "%(pagename)s" submitted %(date)s') % {
            'pagename': pagename, 'date': date,} + u'\n'
        backuppage._write_file(intro + newtext)
        
        return backuppage.url(self.request)

    def _get_pragmas(self, text):
        pragmas = {}
        for line in text.split('\n'):
            if not line or line[0] != '#':
                # end of pragmas
                break
            
            if len(line) > 1 and line[1] == '#':
                # a comment within pragmas
                continue
            
            verb, args = (line[1:]+' ').split(' ', 1)
            pragmas[verb.lower()] = args.strip()
            
        return pragmas

    def copypage(self):
        """
        Copy a page from underlay directory to page directory
        """
        src = self.getPagePath(use_underlay=1, check_create=0)
        dst = self.getPagePath(use_underlay=0, check_create=0)
        if src and dst and src != dst and os.path.exists(src):
            try:
                os.rmdir(dst) # simply remove empty dst dirs
                # XXX in fact, we should better remove anything we regard as an
                # empty page, maybe also if there is also an edit-lock or
                # empty cache. revisions subdir...
            except:
                pass
            if not os.path.exists(dst):
                filesys.copytree(src, dst)
                self.reset() # reinit stuff

    def _write_file(self, text, action='SAVE', comment=u'', extra=u''):
        """ Write the text to the page file (and make a backup of old page).
        
        @param text: text to save for this page
        @rtype: int
        @return: mtime_usec of new page
        """
        _ = self._
        #is_deprecated = self._get_pragmas(text).has_key("deprecated")
        was_deprecated = self._get_pragmas(self.get_raw_body()).has_key("deprecated")

        self.copypage()

        # Write always on the standard directory, never change the
        # underlay directory copy!
        pagedir = self.getPagePath(use_underlay=0, check_create=0)

        revdir = os.path.join(pagedir, 'revisions')
        cfn = os.path.join(pagedir,'current')
        clfn = os.path.join(pagedir,'current-locked')
        
        # !!! these log objects MUST be created outside the locked area !!!

        # The local log should be the standard edit log, not the
        # underlay copy log!
        pagelog = self.getPagePath('edit-log', use_underlay=0, isfile=1)
        llog = editlog.EditLog(self.request, filename=pagelog,
                               uid_override=self.uid_override)
        # Open the global log
        glog = editlog.EditLog(self.request, uid_override=self.uid_override)
        
        if not os.path.exists(pagedir): # new page, create and init pagedir
            os.mkdir(pagedir)
            os.chmod(pagedir, 0777 & config.umask)
        if not os.path.exists(revdir):        
            os.mkdir(revdir)
            os.chmod(revdir, 0777 & config.umask)
            f = open(cfn, 'w')
            f.write('%08d\n' % 0)
            f.close()
            os.chmod(cfn, 0666 & config.umask)
            
        got_lock= False
        retry = 0
        while not got_lock and retry < 100:
            retry += 1
            try:
                filesys.rename(cfn, clfn)
                got_lock = True
            except OSError, err:
                got_lock = False
                if err.errno == 2: # there was no 'current' file
                    time.sleep(0.1)
                else:
                    raise self.CouldNotLock, _("Page could not get locked. Unexpected error (errno=%d).") % err.errno
        
        if not got_lock:
            raise self.CouldNotLock, _("Page could not get locked. Missing 'current' file?")
        
        # increment rev number of current(-locked) page
        f = open(clfn)
        revstr = f.read()
        f.close()
        rev = int(revstr)
        if not was_deprecated:
            if self.do_revision_backup or rev == 0:
                rev += 1
        revstr = '%08d' % rev
        f = open(clfn, 'w')
        f.write(revstr+'\n')
        f.close()
        
        # save to page file
        pagefile = os.path.join(revdir, revstr)
        f = codecs.open(pagefile, 'wb', config.charset)
        # Write the file using text/* mime type
        f.write(self.encodeTextMimeType(text))
        f.close()
        os.chmod(pagefile, 0666 & config.umask)
        mtime_usecs = wikiutil.timestamp2version(os.path.getmtime(pagefile))
        # set in-memory content
        self.set_raw_body(text)
        
        # reset page object
        self.reset()
        
        # write the editlog entry
        # for now simply make 2 logs, better would be some multilog stuff maybe
        if self.do_revision_backup:
            # do not globally log edits with no revision backup (like /MoinEditorBackup pages)
            # if somebody edits a deprecated page, log it in global log, but not local log
            glog.add(self.request, mtime_usecs, rev, action, self.page_name, None, extra, comment)
        if not was_deprecated and self.do_revision_backup:
            # if we did not create a new revision number, do not locally log it
            llog.add(self.request, mtime_usecs, rev, action, self.page_name, None, extra, comment)

        filesys.rename(clfn, cfn)

        # add event log entry
        elog = eventlog.EventLog(self.request)
        elog.add(self.request, 'SAVEPAGE', {'pagename': self.page_name}, 1, mtime_usecs)

        return mtime_usecs, rev


    def saveText(self, newtext, rev, **kw):
        """ Save new text for a page.

        @param newtext: text to save for this page
        @param rev: revision of the page
        @keyword trivial: trivial edit (default: 0)
        @keyword extra: extra info field (e.g. for SAVE/REVERT with revno)
        @keyword comment: comment field (when preview is true)
        @keyword action: action for editlog (default: SAVE)
        @rtype: unicode
        @return: error msg
        """
        _ = self._
        backup_url = self._make_backup(newtext, **kw)
        action = kw.get('action', 'SAVE')

        #!!! need to check if we still retain the lock here
        #!!! rev check is not enough since internal operations use "0"

        # expand variables, unless it's a template or form page
        if not (wikiutil.isTemplatePage(self.request, self.page_name) or
                wikiutil.isFormPage(self.request, self.page_name)):
            newtext = self._expand_variables(newtext)

        msg = ""
        if not self.request.user.may.save(self, newtext, rev, **kw):
            msg = _('You are not allowed to edit this page!')
            raise self.AccessDenied, msg
        elif not self.isWritable():
            msg = _('Page is immutable!')
            raise self.Immutable, msg
        elif not newtext:
            msg = _('You cannot save empty pages.')
            raise self.EmptyPage, msg
        elif rev != 0 and rev != self.current_rev():
            msg = _("""Sorry, someone else saved the page while you edited it.

Please do the following: Use the back button of your browser, and cut&paste
your changes from there. Then go forward to here, and click EditText again.
Now re-add your changes to the current page contents.

''Do not just replace
the content editbox with your version of the page, because that would
delete the changes of the other person, which is excessively rude!''
""")

            if backup_url:
                msg += "<p>%s</p>" % _(
                    'A backup of your changes is [%(backup_url)s here].') % {'backup_url': backup_url}
            raise self.EditConflict, msg
        elif newtext == self.get_raw_body():
            msg = _('You did not change the page content, not saved!')
            raise self.Unchanged, msg
        elif self.cfg.acl_enabled:
            from wikiacl import parseACL
            # Get current ACL and compare to new ACL from newtext. If
            # they are not the sames, the user must have admin
            # rights. This is a good place to update acl cache - instead
            # of wating for next request.
            acl = self.getACL(self.request)
            if (not self.request.user.may.admin(self.page_name) and
                parseACL(self.request, newtext) != acl and
                action != "SAVE/REVERT"):
                msg = _("You can't change ACLs on this page since you have no admin rights on it!")
                raise self.NoAdmin, msg
            
        # save only if no error occurred (msg is empty)
        if not msg:
            # set success msg
            msg = _("Thank you for your changes. Your attention to detail is appreciated.")
            
            # determine action for edit log 
            if action == 'SAVE' and not self.exists():
                action = 'SAVENEW'
            comment = kw.get('comment', u'')
            extra = kw.get('extra', u'')
            trivial = kw.get('trivial', 0)
            
            # write the page file
            mtime_usecs, rev = self._write_file(newtext, action, comment, extra)
            self.clean_acl_cache()
  
            # send notification mails
            if self.request.cfg.mail_smarthost:
                msg = msg + self._notifySubscribers(comment, trivial)
          
        # remove lock (forcibly if we were allowed to break it by the UI)
        # !!! this is a little fishy, since the lock owner might not notice
        # we broke his lock ==> but revision checking during preview will
        self.lock.release(force=not msg) # XXX does "not msg" make any sense?
  
        return msg
            
            
class PageLock:
    """
    PageLock - Lock pages
    """
    # TODO: race conditions throughout, need to lock file during queries & update
    def __init__(self, pageobj):
        """
        """
        self.pageobj = pageobj
        self.page_name = pageobj.page_name
        request = pageobj.request
        self.request = request
        self._ = self.request.getText
        self.cfg = self.request.cfg

        # current time and user for later checks
        self.now = int(time.time())
        self.uid = request.user.valid and request.user.id or request.remote_addr

        # get details of the locking preference, i.e. warning or lock, and timeout
        self.locktype = None
        self.timeout = 10 * 60 # default timeout in minutes

        if self.cfg.edit_locking:
            lockinfo = self.cfg.edit_locking.split()
            if 1 <= len(lockinfo) <= 2:
                self.locktype = lockinfo[0].lower()
                if len(lockinfo) > 1:
                    try:
                        self.timeout = int(lockinfo[1]) * 60
                    except ValueError:
                        pass


    def aquire(self):
        """
        Begin an edit lock depending on the mode chosen in the config.

        @rtype: tuple
        @return: tuple is returned containing 2 values:
              * a bool indicating successful aquiry
              * a string giving a reason for failure or an informational msg
        """
        if not self.locktype:
            # we are not using edit locking, so always succeed
            return 1, ''

        _ = self._
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
            if self.owner is not None and -10800 < secs_valid < 0:
                mins_ago = secs_valid / -60
                msg.append(_(
                    "The lock of %(owner)s timed out %(mins_ago)d minute(s) ago,"
                    " and you were granted the lock for this page."
                    ) % {'owner': owner, 'mins_ago': mins_ago})

            if self.locktype == 'lock':
                msg.append(_(
                    "Other users will be ''blocked'' from editing this page until %(bumptime)s."
                    ) % {'bumptime': bumptime})
            else:
                msg.append(_(
                    "Other users will be ''warned'' until %(bumptime)s that you are editing this page."
                    ) % {'bumptime': bumptime})
            msg.append(_(
                "Use the Preview button to extend the locking period."
                ))
            result = 1, '\n'.join(msg)
        else:
            mins_valid = (secs_valid+59) / 60
            if self.locktype == 'lock':
                # lout out user
                result = 0, _(
                    "This page is currently ''locked'' for editing by %(owner)s until %(timestamp)s,"
                    " i.e. for %(mins_valid)d minute(s)."
                    ) % {'owner': owner, 'timestamp': timestamp, 'mins_valid': mins_valid}
            else:
                # warn user about existing lock
### WIKIMARKUP-TODO
                result = 1, _(
                    'This page was opened for editing or last previewed at %(timestamp)s by %(owner)s.[[BR]]\n'
                    '\'\'\''
                    'You should \'\'refrain from editing\'\' this page for at least another %(mins_valid)d minute(s),\n'
                    'to avoid editing conflicts.'
                    '\'\'\'[[BR]]\n'
                    'To leave the editor, press the Cancel button.'
                    ) % {'timestamp': timestamp, 'owner': owner, 'mins_valid': mins_valid}

        return result


    def release(self, force=0):
        """ 
        Release lock, if we own it.
        
        @param force: if 1, unconditionally release the lock.
        """
        if self.locktype:
            # check that we own the lock in order to delete it
            #!!! race conditions, need to lock file during queries & update
            self._readLockFile()
            if force or self.uid == self.owner:
                self._deleteLockFile()


    def _filename(self):
        """get path and filename for edit-lock file"""
        return self.pageobj.getPagePath('edit-lock', isfile=1)


    def _readLockFile(self):
        """Load lock info if not yet loaded."""
        _ = self._
        self.owner = None
        self.owner_html = wikiutil.escape(_("<unknown>"))
        self.timestamp = 0

        if self.locktype:
            try:
                entry = editlog.EditLog(self.request, filename=self._filename()).next()
            except StopIteration:
                entry = None
                                                    
            if entry:
                self.owner = entry.userid or entry.addr
                self.owner_html = entry.getEditor(self.request)
                self.timestamp = wikiutil.version2timestamp(entry.ed_time_usecs)


    def _writeLockFile(self):
        """Write new lock file."""
        self._deleteLockFile()
        try:
            editlog.EditLog(self.request, filename=self._filename()).add(
               self.request, wikiutil.timestamp2version(self.now), 0, "LOCK", self.page_name)
        except IOError:
            pass

    def _deleteLockFile(self):
        """Delete the lock file unconditionally."""
        try:
            os.remove(self._filename())
        except OSError:
            pass


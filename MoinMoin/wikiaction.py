# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action Handlers

    Actions are triggered by the user clicking on special links on the page
    (like the icons in the title, or the "EditText" link at the bottom). The
    name of the action is passed in the "action" CGI parameter.

    The sub-package "MoinMoin.action" contains external actions, you can
    place your own extensions there (similar to extension macros). User
    actions that start with a capital letter will be displayed in a list
    at the bottom of each page.

    User actions starting with a lowercase letter can be used to work
    together with a user macro; those actions a likely to work only if
    invoked BY that macro, and are thus hidden from the user interface.

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import os, re, string, time, urllib
from MoinMoin import config, util, wikiutil
from MoinMoin.Page import Page
from MoinMoin.util import MoinMoinNoFooter, pysupport

#############################################################################
### Search
#############################################################################

def do_fullsearch(pagename, request, fieldname='value'):
    _ = request.getText
    start = time.clock()

    # send http headers
    request.http_headers()

    # get parameters
    if request.form.has_key(fieldname):
        needle = request.form[fieldname][0]
    else:
        needle = ''
    try:
        case = int(request.form['case'][0])
    except (KeyError, ValueError):
        case = 0
    try:
        context = int(request.form['context'][0])
    except (KeyError, ValueError):
        context = 0
    max_context = 10 # only show first `max_context` contexts

    # check for sensible search term
    if len(needle) < 1:
        Page(pagename).send_page(request,
             msg=_("Please use a more selective search term instead of '%(needle)s'!") % {'needle': needle})
        return

    # send title
    wikiutil.send_title(request, _('Full text search for "%s"') % (needle,))

    # search the pages
    pagecount, hits = wikiutil.searchPages(needle,
        literal=request.form.has_key('literal'),
        context=context, case=case)

    # print the result
    request.write('<dl class="searchresult">')
    hiddenhits = 0
    for (count, page_name, fragments) in hits:
        if not request.user.may.read(page_name):
            hiddenhits += 1
            continue
        request.write('<dt>' + Page(page_name).link_to(request, querystr=
            'action=highlight&amp;value=%s' % urllib.quote_plus(needle)))
        request.write(' . . . . ' + `count`)
        request.write(' ' + (_('match'), _('matches'))[count != 1])
        request.write('</dt><dd><p>\n')
        if context:
            out = []
            for hit in fragments[:max_context]:
                out.append('...%s<span>%s</span>%s...' % tuple(map(wikiutil.escape, hit)))
            request.write('<br>\n'.join(out))
            if len(fragments) > max_context:
                request.write('...')
        request.write('</p></dd>\n')
    request.write('</dl>')

    print_search_stats(request, len(hits)-hiddenhits, pagecount, start)
    wikiutil.send_footer(request, pagename, editable=0, showactions=0, form=request.form)


def do_titlesearch(pagename, request, fieldname='value'):
    _ = request.getText
    start = time.clock()

    request.http_headers()

    if request.form.has_key(fieldname):
        needle = request.form[fieldname][0]
    else:
        needle = ''

    # check for sensible search term
    if len(needle) < 1:
        Page(pagename).send_page(request,
             msg=_("Please use a more selective search term instead of '%(needle)s'!") % {'needle': needle})
        return

    wikiutil.send_title(request, _('Title search for "%s"') % (needle,))

    try:
        needle_re = re.compile(needle, re.IGNORECASE)
    except re.error:
        needle_re = re.compile(re.escape(needle), re.IGNORECASE)
    all_pages = wikiutil.getPageList(config.text_dir)
    hits = filter(needle_re.search, all_pages)
    hits.sort()

    hits = filter(request.user.may.read, hits)

    request.write('<ul>')
    for filename in hits:
        request.write('<li>%s</li>' % Page(filename).link_to(request))
    request.write('</ul>')

    print_search_stats(request, len(hits), len(all_pages), start)
    wikiutil.send_footer(request, pagename, editable=0, showactions=0, form=request.form)


def do_inlinesearch(pagename, request):
    text_title = request.form.get('text_title', [''])[0]
    text_full = request.form.get('text_full', [''])[0]
    
    if request.form.has_key('button_title.x'):
        if request.form['button_title.x'][0] == "0" and \
                text_full and not text_title:
            search = 'full'
        else:
            search = 'title'
    elif request.form.has_key('button_full.x'):
        search = 'full'
    elif request.form.has_key('text_full'):
        search = 'full'
    else:
        search = 'title'

    globals()["do_%ssearch" % search](pagename, request, fieldname = "text_" + search)


def print_search_stats(request, hits, pages, start):
    _ = request.getText
    request.write("<p>%s %s</p>" % (
        _("%(hits)d hits out of %(pages)d pages searched.") % {'hits': hits, 'pages': pages},
        _("Needed %(timer).1f seconds.") % {'timer': time.clock() - start + 0.05}))


def do_highlight(pagename, request):
    if request.form.has_key('value'):
        needle = request.form["value"][0]
    else:
        needle = ''

    try:
        needle_re = re.compile(needle, re.IGNORECASE)
    except re.error:
        needle = re.escape(needle)
        needle_re = re.compile(needle, re.IGNORECASE)

    Page(pagename).send_page(request, hilite_re=needle_re)


#############################################################################
### Misc Actions
#############################################################################

def do_diff(pagename, request):
    """ Handle "action=diff"
        checking for either a "date=backupdate" parameter
        or date1 and date2 parameters
    """
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    try:
        diff1_date = request.form['date1'][0]
        try:
            diff1_date = float(diff1_date)
        except StandardError:
            diff1_date = 0
    except KeyError:
        diff1_date = -1

    try:
        diff2_date = request.form['date2'][0]
        try:
            diff2_date = float(diff2_date)
        except StandardError:
            diff2_date = 0
    except KeyError:
        diff2_date = 0

    if diff1_date == -1 and diff2_date == 0:
        try:
            diff1_date = request.form['date'][0]
            try:
                diff1_date = float(diff1_date)
            except StandardError:
                diff1_date = -1
        except KeyError:
            diff1_date = -1
  
    # spacing flag?
    try:
        ignorews = int(request.form['ignorews'][0])
    except (KeyError, ValueError, TypeError):
        ignorews = 0

    _ = request.getText
    
    # get a list of old revisions, and back out if none are available
    oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
    if not oldversions:
        Page(pagename).send_page(request,
            msg=_("No older revisions available!"))
        return

    request.http_headers()
    wikiutil.send_title(request, _('Diff for "%s"') % (pagename,), pagename=pagename)
  
    if (diff1_date>0 and diff2_date>0 and diff1_date>diff2_date) or \
       (diff1_date==0 and diff2_date>0):
        diff1_date,diff2_date = diff2_date,diff1_date
        
    olddate1,oldcount1 = None,0
    olddate2,oldcount2 = None,0

    # get the filename of the version to compare to
    edit_count = 0
    for oldpage in oldversions:
        edit_count += 1
        try:
            date = os.path.getmtime(os.path.join(config.backup_dir, oldpage))
        except EnvironmentError:
            continue
        if date <= diff1_date: 
            olddate1,oldcount1 = date,edit_count
        if diff2_date and date >= diff2_date: 
            olddate2,oldcount2 = date,edit_count
        if (olddate1 and olddate2) or (olddate1 and not diff2_date):
            break

    if diff1_date == -1:
        first_oldpage = os.path.join(config.backup_dir, oldversions[0])
        first_olddate = os.path.getmtime(first_oldpage)
        oldpage = Page(pagename, date=str(int(first_olddate)))
        oldcount1 = oldcount1 - 1
    elif diff1_date == 0:
        oldpage = Page(pagename)
        # oldcount1 is still on init value 0
    else:
        if olddate1:
            oldpage = Page(pagename, date=str(int(olddate1)))
        else:
            oldpage = Page("$EmptyPage$") # XXX: ugly hack
            oldpage.set_raw_body("")    # avoid loading from disk
            
    if diff2_date == 0:
        newpage = Page(pagename)
        # oldcount2 is still on init value 0
    else:
        if olddate2:
            newpage = Page(pagename, date=str(int(olddate2)))
        else:
            newpage = Page("$EmptyPage$") # XXX: ugly hack
            newpage.set_raw_body("")    # avoid loading from disk

    edit_count = abs(oldcount1 - oldcount2)

    request.write('<p><strong>')
    request.write(_('Differences between versions dated %s and %s') % (
        oldpage.mtime_printable(request), newpage.mtime_printable(request)))
    if edit_count > 1:
        request.write(' ' + _('(spanning %d versions)') % (edit_count,))
    request.write('</strong></p>')
  
    if request.user.show_fancy_diff:
        from MoinMoin.util.diff import diff
        request.write(diff(request, oldpage.get_raw_body(), newpage.get_raw_body()))
        newpage.send_page(request, count_hit=0, content_only=1)
    else:
        lines = wikiutil.linediff(oldpage.get_raw_body().split('\n'), newpage.get_raw_body().split('\n'))
        if not lines:
            msg = _("No differences found!")
            if edit_count > 1:
                msg = msg + '<p>' + _('The page was saved %(count)d times, though!') % {
                    'count': edit_count}
            request.write(msg)
        else:
            if ignorews:
                request.write('(ignoring whitespace)' + '<p>')
            else:
                qstr = 'action=diff&amp;ignorews=1'
                if diff1_date: qstr = '%s&amp;date1=%s' % (qstr, diff1_date)
                if diff2_date: qstr = '%s&amp;date2=%s' % (qstr, diff2_date)
                request.write(Page(pagename).link_to(request,
                    text=_('Ignore changes in the amount of whitespace'),
                    querystr=qstr) + '<p>')

            request.write('<pre>')
            for line in lines:
                if line[0] == "@":
                    request.write('<hr>')
                request.write(wikiutil.escape(line)+'\n')
            request.write('</pre>')

    wikiutil.send_footer(request, pagename, showpage=1)


def do_info(pagename, request):
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    def general(page, pagename, request):
        _ = request.getText

        request.write('<h2>%s</h2>\n' % _('General Information'))
        
        # show page size
        request.write(("<p>%s</p>" % _("Page size: %d")) % page.size())

        # show SHA digest fingerprint
        import sha
        digest = sha.new(page.get_raw_body()).hexdigest().upper()
        request.write('<p>%(label)s <tt>%(value)s</tt></p>' % {
            'label': _("SHA digest of this page's content is:"),
            'value': digest,
            })

        # show attachments (if allowed)
        attachment_info = getHandler('AttachFile', 'info')
        if attachment_info: attachment_info(pagename, request)

        # show subscribers
        subscribers = page.getSubscribers(request,  include_self=1, return_users=1)
        if subscribers:
            request.write('<p>', _('The following users subscribed to this page:'))
            for lang in subscribers.keys():
                request.write('<br>[%s] ' % lang)
                for user in subscribers[lang]:
                    # do NOT disclose email addr, only WikiName
                    userhomepage = Page(user.name)
                    if userhomepage.exists():
                        request.write(userhomepage.link_to(request) + ' ')
                    else:
                        request.write(user.name + ' ')
            request.write('</p>')

        # show links
        links = page.getPageLinks(request)
        if links:
            request.write('<p>', _('This page links to the following pages:'), '<br>')
            for linkedpage in links:
                request.write("%s%s " % (Page(linkedpage).link_to(request), ",."[linkedpage == links[-1]]))
            request.write("</p>")


    def history(page, pagename, request):
        # show history as default
        from stat import ST_MTIME, ST_SIZE
        _ = request.getText

        request.write('<h2>%s</h2>\n' % _('Revision History'))

        # generate history list
        currentpage = os.path.join(config.text_dir, wikiutil.quoteFilename(pagename))
        revisions = [currentpage]
        versions = 1
        
        oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
        if oldversions:
            for file in oldversions:
                revisions.append(os.path.join(config.backup_dir, file))
                versions += 1

        # open log for this page
        from MoinMoin.logfile import editlog
        from MoinMoin.util.dataset import TupleDataset, Column

        log = editlog.EditLog()
        log.set_filter(pagename=pagename)
        log.to_end()
        line = log.previous()
        
        history = TupleDataset()
        history.columns = [
            Column('count', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size',  label=_('Size'), align='right'),
            Column('diff', label='<input type="submit"           value="%s">' % (_("Diff"))),
            # entfernt, nicht 4.01 compliant:          href="%s"   % page.url(request)
            Column('editor', label=_('Editor'), hidden=not config.show_hosts),
            Column('comment', label=_('Comment')),
            Column('action', label=_('Action')),
            ]

        may_revert = request.user.may.revert(pagename)

        count = 1
        for file in revisions:
            try:
                st = os.stat(file)
            except OSError:
                continue

            try:
                mtime = int(os.path.basename(file).split('.')[1])
            except IndexError:
                mtime = st[ST_MTIME]
            #print count, mtime, st[ST_MTIME], "<br>"

            while not line.ed_time or int(line.ed_time) > int(mtime):
                try:
                    line = log.previous()
                except StopIteration:
                    break
                
            if int(line.ed_time) != int(mtime):
                line = editlog.EditLogLine({})
                line.ed_time = 0
                line.comment = ''
                line.action = ''
                line.userid = ''
                line.hostname = ''
                line.addr = ''

            this_version = 1 + versions - count
            actions = ""

            if file == currentpage:
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('view'),
                    querystr=''))
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('raw'),
                    querystr='action=raw'))
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('print'),
                    querystr='action=print'))
                diff = '<input type="radio" name="date1" value="0"><input type="radio" name="date2" value="0" checked="checked">'
            else:
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('view'),
                    querystr='action=recall&amp;date=%d' % mtime))
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('raw'),
                    querystr='action=raw&amp;date=%d' % mtime))
                actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                    text=_('print'),
                    querystr='action=print&amp;date=%d' % mtime))
                if may_revert:
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('revert'),
                        querystr='action=revert&amp;date=%d&amp;version=%d' % (mtime, this_version)))
                if count==2:
                    checked=' checked="checked"'
                else:
                    checked=""
                diff = '<input type="radio" name="date1" value="%d"%s><input type="radio" name="date2" value="%d">' % (mtime,checked,mtime)
  
            comment = line.comment
            if line.action.find('/REVERT') != -1:
                datestamp = request.user.getFormattedDateTime(float(comment))
                comment = _("Revert to version dated %(datestamp)s.") % {'datestamp': datestamp}
    
            history.addRow((
                this_version,
                request.user.getFormattedDateTime(mtime),
                str(st[ST_SIZE]),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                actions,
            ))
            count += 1
            if count > 100: break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget
        from MoinMoin.formatter.text_html import Formatter

        request.write('<form method="GET" action="%s">\n' % (page.url(request)))
        request.write('<div id="pageinfo">')
        request.write('<input type="hidden" name="action" value="diff">\n')

        request.formatter = Formatter(request)
        history_table = DataBrowserWidget(request)
        history_table.setData(history)
        history_table.render()
        request.write('</div>')
        request.write('\n</form>\n')


    _ = request.getText
    page = Page(pagename)
    qpagename = wikiutil.quoteWikiname(pagename)

    request.http_headers()
    wikiutil.send_title(request, _('Info for "%s"') % (pagename,), pagename=pagename)

    historylink =  wikiutil.link_tag(request, '%s?action=info' % qpagename,
        _('Show "%(title)s"') % {'title': _('Revision History')})
    generallink =  wikiutil.link_tag(request, '%s?action=info&amp;general=1' % qpagename,
        _('Show "%(title)s"') % {'title': _('General Page Infos')})
    hitcountlink = wikiutil.link_tag(request, '%s?action=info&amp;hitcounts=1' % qpagename,
        _('Show chart "%(title)s"') % {'title': _('Page hits and edits')})
    
    request.write("<p>[%s]  [%s]  [%s]</p><hr>" % (historylink, generallink, hitcountlink))

    show_hitcounts = int(request.form.get('hitcounts', [0])[0]) != 0
    show_general = int(request.form.get('general', [0])[0]) != 0
    
    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(hitcounts.linkto(pagename, request, 'page=' + urllib.quote_plus(pagename)))
    elif show_general:
        general(page, pagename, request)
    else:
        history(page, pagename, request)
        
    wikiutil.send_footer(request, pagename, showpage=1)


def do_recall(pagename, request):
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return
    if request.form.has_key('date'):
        Page(pagename, date=request.form['date'][0]).send_page(request)
    else:
        Page(pagename).send_page(request)


def do_show(pagename, request):
    if request.form.has_key('date'):
        Page(pagename, date=request.form['date'][0]).send_page(request, count_hit=1)
    else:
        Page(pagename).send_page(request, count_hit=1)


def do_refresh(pagename, request):
    if request.form.has_key('arena') and request.form.has_key('key'):
        from MoinMoin import caching
        cache = caching.CacheEntry(request.form["arena"][0], request.form["key"][0])
        cache.remove()
    do_show(pagename, request)


def do_print(pagename, request):
    do_show(pagename, request)


def do_content(pagename, request):
    request.http_headers()
    page = Page(pagename)
    request.write('<!-- Transclusion of %s -->' % request.getQualifiedURL(page.url(request)))
    page.send_page(request, count_hit=0, content_only=1)
    raise MoinMoinNoFooter


def do_edit(pagename, request):
    if not request.user.may.edit(pagename):
        _ = request.getText
        Page(pagename).send_page(request,
            msg = _('You are not allowed to edit this page.'))
        return
    from MoinMoin.PageEditor import PageEditor
    PageEditor(pagename, request).sendEditor()


def do_revert(pagename, request):
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText

    if not request.user.may.revert(pagename):
        return Page(pagename).send_page(request,
            msg = _('You are not allowed to revert this page!'))

    date = request.form['date'][0]
    oldpg = Page(pagename, date=date)
    pg = PageEditor(pagename, request)

    try:
        savemsg = pg.saveText(oldpg.get_raw_body(), '0',
            stripspaces=0, notify=1, comment=date, action="SAVE/REVERT")
    except pg.SaveError:
        savemsg = _("An error occurred while reverting the page.")
    request.reset()
    pg.send_page(request, msg=savemsg)
    return None

def do_savepage(pagename, request):
    from MoinMoin.PageEditor import PageEditor

    _ = request.getText

    if not request.user.may.edit(pagename):
        Page(pagename).send_page(request,
            msg = _('You are not allowed to edit this page.'))
        return

    pg = PageEditor(pagename, request)
    savetext = request.form.get('savetext', [''])[0]
    datestamp = request.form.get('datestamp', [''])[0]
    comment = request.form.get('comment', [''])[0]
    category = request.form.get('category', [None])[0]
    try:
        rstrip = int(request.form['rstrip'][0])
    except (KeyError, ValueError):
        rstrip = 0
    try:
        notify = int(request.form['notify'][0])
    except (KeyError, ValueError):
        notify = 0

    if category:
        # strip trailing whitespace
        savetext = savetext.rstrip()

        # add category splitter if last non-empty line contains non-categories
        lines = filter(None, savetext.splitlines())
        if lines:
            categories = lines[-1].split()
            if categories and len(wikiutil.filterCategoryPages(categories)) < len(categories):
                savetext += '\n----\n'

        # add new category
        if savetext and savetext[-1] != '\n':
            savetext += ' '
        savetext += category

    # delete any unwanted stuff, replace CR, LF, TAB by whitespace
    control_chars = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' \
                    '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    remap_chars = string.maketrans('\t\r\n', '   ')
    comment = comment.translate(remap_chars, control_chars)

    if request.form.has_key('button_preview') or request.form.has_key('button_spellcheck') \
            or request.form.has_key('button_newwords'):
        pg.sendEditor(preview=savetext, comment=comment)
    elif request.form.has_key('button_cancel'):
        pg.sendCancel(savetext, datestamp)
    else:
        savetext = pg._normalize_text(savetext, stripspaces=rstrip)
        try:
            savemsg = pg.saveText(savetext, datestamp,
                                  stripspaces=rstrip, notify=notify,
                                  comment=comment)
        except pg.EditConflict, msg:
            allow_conflicts = 1
            from MoinMoin.util import diff3
            original_text = Page(pg.page_name, date=datestamp).get_raw_body()
            saved_text = pg.get_raw_body()
            verynewtext = diff3.text_merge(original_text, saved_text, savetext,
                 allow_conflicts,
                 '----- /!\ Edit conflict! Other version: -----\n',
                 '----- /!\ Edit conflict! Your version: -----\n',
                 '----- /!\ End of edit conflict -----\n')
            if verynewtext:
                msg = _("""Someone else saved this page while you were editing!
Please review the page and save then. Do not save this page as it is!
Have a look at the diff of %(difflink)s to see what has been changed."""
                ) % {'difflink':pg.link_to(request, querystr='action=diff&amp;date=' + datestamp)}
                request.form['datestamp'] = [os.path.getmtime(pg._text_filename())]                                
                pg.sendEditor(msg=msg, comment=request.form.get('comment', [''])[0],
                              preview=verynewtext, staytop=1)
                return
            else:
                savemsg = msg
        except pg.SaveError, msg:
            savemsg = msg
        request.reset()
        backto = request.form.get('backto', [None])[0]
        if backto:
            pg = Page(backto)
        pg.send_page(request, msg=savemsg)
        request.http_redirect(pg.url(request))


def do_subscribe(pagename, request):
    """ Add the current wiki page to the subscribed_page property in
        current user profile.
    """
    _ = request.getText

    if not request.user.may.read(pagename):
        msg = _("You are not allowed to subscribe to a page you can't read.")

    # check config
    elif not config.mail_smarthost:
        msg = _('''This wiki is not enabled for mail processing. '''
                '''Contact the owner of the wiki, who can either enable email, or remove the "Subscribe" icon.''')

    # check whether the user has a profile
    elif not request.user.valid:
        msg = _('''You didn't create a user profile yet. '''
                '''Select UserPreferences in the upper right corner to create a profile.''')

    # check whether the user has an email address
    elif not request.user.email:
        msg = _('''You didn't enter an email address in your profile. '''
                '''Select your name (UserPreferences) in the upper right corner and enter a valid email address.''')

    # check whether already subscribed
    elif request.user.isSubscribedTo([pagename]):
        msg = _('You are already subscribed to this page.') + \
              _('To unsubscribe, go to your profile and delete this page from the subscription list.')
        
    # subscribe to current page
    else:
        if request.user.subscribePage(pagename):
            request.user.save()
        msg = _('You have been subscribed to this page.') + \
              _('To unsubscribe, go to your profile and delete this page from the subscription list.')

    Page(pagename).send_page(request, msg=msg)


def do_userform(pagename, request):
    from MoinMoin import userform
    savemsg = userform.savedata(request)
    Page(pagename).send_page(request, msg=savemsg)


def do_bookmark(pagename, request):
    if request.form.has_key('time'):
        try:
            tm = int(request.form["time"][0])
        except StandardError:
            tm = time.time()
    else:
        tm = time.time()

    request.user.setBookmark(tm)
    Page(pagename).send_page(request)


def do_formtest(pagename, request):
    # test a user defined form
    from MoinMoin import wikiform
    wikiform.do_formtest(pagename, request)


# def do_macro(pagename, request):
#     """ Execute a helper action within a macro.
#     """

#     from MoinMoin import wikimacro
#     from MoinMoin.formatter.text_html import Formatter
#     from MoinMoin.parser.wiki import Parser
#     from MoinMoin.Page import Page
#     macro_name = request.form["macro"][0]
#     args = request.form.get('args', [''])[0]
    
#     parser = Parser('', request)
#     parser.formatter = Formatter(request)
#     parser.formatter.page = Page('dummy')
#     request.http_headers()
#     request.write(wikimacro.Macro(parser).execute(macro_name, args))
#     request.finish()
    
#############################################################################
### Special Actions
#############################################################################

def do_raw(pagename, request):
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    request.http_headers(["Content-type: text/plain;charset=%s" % config.charset])

    try:
        page = Page(pagename, date=request.form['date'][0])
    except KeyError:
        page = Page(pagename)

    request.write(page.get_raw_body())
    raise MoinMoinNoFooter


def do_format(pagename, request):
    # get the MIME type
    if request.form.has_key('mimetype'):
        mimetype = request.form['mimetype'][0]
    else:
        mimetype = "text/plain"

    # try to load the formatter
    Formatter = wikiutil.importPlugin("formatter",
        mimetype.translate(string.maketrans('/.', '__')), "Formatter")
    if Formatter is None:
        # default to plain text formatter
        del Formatter
        mimetype = "text/plain"
        from formatter.text_plain import Formatter

    #request.http_headers(["Content-Type: " + mimetype])
    request.http_headers(["Content-Type: " + 'text/plain'])

    Page(pagename, formatter = Formatter(request)).send_page(request)
    raise MoinMoinNoFooter


def do_chart(pagename, request):
    if request.user.may.read(pagename):
        chart_type = request.form['type'][0]
        func = pysupport.importName("MoinMoin.stats." + chart_type, "draw")
        func(pagename, request)
    raise MoinMoinNoFooter


def do_dumpform(pagename, request):
    data = util.dumpFormData(request.form)

    request.http_headers()
    request.write("<html><body>%s</body></html>" % data)
    raise MoinMoinNoFooter


def do_export(pagename, request):
    import shutil, cStringIO
    from MoinMoin.wikixml import wikiexport

    # Protect this with ACLs, when ready!

    # get parameters
    compression = request.form.get('compression', None)

    # prepare output stream
    fileid = time.strftime("%Y-%m-%d", request.user.getTime())
    filename = "wiki-export-%s.xml" % fileid 
    outbuff = cStringIO.StringIO()
    mimetype, out = 'text/xml', outbuff
    if compression == "gzip":
        import gzip
        mimetype, out = 'application/x-gzip', gzip.GzipFile(
            filename, "wb", 9, outbuff)
        filename = filename + '.gz'

    # create export document
    export = wikiexport.WikiExport(out, public=1)
    export.run()

    # send http headers
    headers = [
        "Content-Type: %s" % mimetype,
        "Content-Length: %d" % len(outbuff.getvalue()),
    ]
    if mimetype != 'text/xml':
        headers.append("Content-Disposition: attachment; filename=%s" % filename)
    request.http_headers(headers)

    # copy the body
    outbuff.reset()
    shutil.copyfileobj(outbuff, request, 8192)
    raise MoinMoinNoFooter


#############################################################################
### Dispatching
#############################################################################

def getPlugins():
    dir = os.path.join(config.plugin_dir, 'action')
    plugins = []
    if os.path.isdir(dir):
        plugins = pysupport.getPackageModules(os.path.join(dir, 'dummy'))
    return dir, plugins


def getHandler(action, identifier="execute"):
    # check for excluded actions
    if action in config.excluded_actions:
        return None

    # check for and possibly return builtin action
    handler = globals().get('do_' + action, None)
    if handler: return handler

    return wikiutil.importPlugin("action", action, identifier)


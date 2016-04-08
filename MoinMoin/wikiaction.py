# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action Handlers

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

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

    $Id: wikiaction.py,v 1.106 2003/11/09 21:00:52 thomaswaldmann Exp $
"""

# Imports
import cgi, os, re, string, sys, time, urllib
from MoinMoin import config, user, util, wikiutil, webapi
from MoinMoin.Page import Page
from MoinMoin.util import pysupport


#############################################################################
### Search
#############################################################################

def do_fullsearch(pagename, request, fieldname='value'):
    _ = request.getText
    start = time.clock()

    # send http headers
    webapi.http_headers(request)

    # get parameters
    if request.form.has_key(fieldname):
        needle = request.form[fieldname].value
    else:
        needle = ''
    try:
        case = int(request.form['case'].value)
    except (KeyError, ValueError):
        case = 0
    try:
        context = int(request.form['context'].value)
    except (KeyError, ValueError):
        context = 0
    max_context = 10 # only show first `max_context` contexts

    # check for sensible search term
    if len(needle) < 1:
        Page(pagename).send_page(request,
             msg=_("<b>Please use a more selective search term instead of '%(needle)s'!</b>") % locals())
        return

    # send title
    wikiutil.send_title(request, _('Full text search for "%s"') % (needle,))

    # search the pages
    pagecount, hits = wikiutil.searchPages(needle,
        literal=request.form.has_key('literal'),
        context=context, case=case)

    # print the result
    print "<UL>"
    hiddenhits = 0
    for (count, page_name, fragments) in hits:
        if not request.user.may.read(page_name):
            hiddenhits += 1
            continue
        print '<LI>' + Page(page_name).link_to(querystr=
            'action=highlight&value=%s' % urllib.quote_plus(needle))
        print ' . . . . ' + `count`
        print (_(' match'), _(' matches'))[count != 1]
        if context:
            for hit in fragments[:max_context]:
                print '<br>', '&nbsp;'*8, '<font color="#808080">...%s<b>%s</b>%s...</font>' \
                    % tuple(map(cgi.escape, hit))
            if len(fragments) > max_context:
                print '<br>', '&nbsp;'*8, '<font color="#808080">...</font>'
    print "</UL>"

    print_search_stats(request, len(hits)-hiddenhits, pagecount, start)
    wikiutil.send_footer(request, pagename, editable=0, showactions=0, form=request.form)


def do_titlesearch(pagename, request, fieldname='value'):
    _ = request.getText
    start = time.clock()

    webapi.http_headers(request)

    if request.form.has_key(fieldname):
        needle = request.form[fieldname].value
    else:
        needle = ''

    wikiutil.send_title(request, _('Title search for "%s"') % (needle,))

    try:
        needle_re = re.compile(needle, re.IGNORECASE)
    except re.error:
        needle_re = re.compile(re.escape(needle), re.IGNORECASE)
    all_pages = wikiutil.getPageList(config.text_dir)
    hits = filter(needle_re.search, all_pages)
    hits.sort()

    hits = filter(request.user.may.read, hits)

    print "<UL>"
    for filename in hits:
        print '<LI>' + Page(filename).link_to()
    print "</UL>"

    print_search_stats(request, len(hits), len(all_pages), start)
    wikiutil.send_footer(request, pagename, editable=0, showactions=0, form=request.form)


def do_inlinesearch(pagename, request):
    if request.form.has_key('button_title.x'):
        if request.form['button_title.x'].value == "0" and \
                request.form.has_key('text_full') and \
                not request.form.has_key('text_title'):
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
    print "<p>" + _("%(hits)d hits out of %(pages)d pages searched.") % locals()
    print _("Needed %(timer).1f seconds.") % {'timer': time.clock() - start + 0.05}


def do_highlight(pagename, request):
    if request.form.has_key('value'):
        needle = request.form["value"].value
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
    """ Handle "action=diff", checking for a "date=backupdate" parameter """
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    _ = request.getText
    webapi.http_headers(request)

    # try to get a specific date to compare to, or None for one-before-current
    try:
        diff_date = request.form['date'].value
        try:
            diff_date = float(diff_date)
        except StandardError:
            diff_date = None
    except KeyError:
        diff_date = None

    # spacing flag?
    try:
        ignorews = int(request.form['ignorews'].value)
    except (KeyError, ValueError, TypeError):
        ignorews = 0

    # get a list of old revisions, and back out if none are available
    oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
    if not oldversions:
        Page(pagename).send_page(request,
            msg=_("<b>No older revisions available!</b>"))
        return

    # get the filename of the version to compare to
    edit_count = 0
    if diff_date:
        for oldpagename in oldversions:
            edit_count = edit_count + 1
            try:
                date = os.path.getmtime(os.path.join(config.backup_dir, oldpagename))
            except EnvironmentError:
                continue
            if date <= diff_date: break
    else:
        # get the version before the current one
        edit_count = 1
        oldpagename = oldversions[0]

    if request.user.show_fancy_diff:
        from MoinMoin.util.diff import diff

        olddate = oldpagename.split('.', 1)[1]
        oldpage = Page(pagename, date=olddate)
        newpage = Page(pagename)
        new_date = newpage.exists() and os.path.getmtime(newpage._text_filename()) or time.time()

        # send page title
        wikiutil.send_title(request, _('Diff for "%s"') % (pagename,), pagename=pagename)

        # Show date info
        print _('<b>Differences between version dated %s and %s') % (
            request.user.getFormattedDateTime(os.path.getmtime(oldpage._text_filename())),
            request.user.getFormattedDateTime(new_date), )
        if edit_count != 1:
            print _(' (spanning %d versions)') % (edit_count,)
        print '</b><br>'

        request.write(diff(request, oldpage.get_raw_body(), newpage.get_raw_body()))
        newpage.send_page(request, count_hit=0, content_only=1)
        wikiutil.send_footer(request, pagename, showpage=1)

        return

    # call external diff command
    rc, page_file, backup_file, lines = wikiutil.pagediff(pagename, oldpagename, ignorews=ignorews)

    # check for valid diff
    if not lines:
        msg = _("<b>No differences found!</b>")
        if edit_count > 1:
            msg = msg + '<p>' + _('The page was saved %(count)d%(times)s, though!') % {
                'count': edit_count,
                'times': (_(' time'), _(' times'))[edit_count != 1]}
        if rc:
            msg = msg + '<p>' + _('The external diff utility returned with error code %(rc)s!') % locals()
        Page(pagename).send_page(request, msg=msg)
        return

    # send page title
    wikiutil.send_title(request, _('Diff for "%s"') % (pagename,), pagename=pagename)

    # options
    if not ignorews:
        qstr = 'action=diff&ignorews=1'
        if diff_date: qstr = '%s&date=%s' % (qstr, diff_date)
        print Page(pagename).link_to(
            text=_('Ignore changes in the amount of whitespace'),
            querystr=qstr), "<p>"

    # Show date info
    print _('<b>Differences between version dated %s and %s') % (
        request.user.getFormattedDateTime(os.path.getmtime(backup_file)),
        request.user.getFormattedDateTime(os.path.getmtime(page_file)))
    if edit_count != 1:
        print _(' (spanning %d versions)') % (edit_count,)
    print '</b>'

    # Remove header lines
    if lines[0][0:3] == "---":
        del lines[0]
    if lines[0][0:3] == "+++":
        del lines[0]

    if request.user.show_fancy_diff:
        print '<div class="diff-removed">' + _('Deletions are marked like this.') + '</div>'
        print '<div class="diff-added">' + _('Additions are marked like this.') + '</div>'

        # Show diff
        for line in lines:
            marker = line[0]
            line = cgi.escape(line[1:])
            while line and line[-1] in ['\r', '\n']:
                line = line[:-1]
            stripped = string.lstrip(line)
            if len(line) - len(stripped):
                line = "&nbsp;" * (len(line) - len(stripped)) + stripped
            if not line:
                line = "&nbsp;"

            if marker == "@":
                print '<hr style="color:#FF3333">'
            elif marker == "\\":
                if stripped == "No newline at end of file\n": continue
                print '<div><font size="1" face="Verdana">%s&nbsp;</font></div>' % (line,)
            elif marker == "+":
                print '<div class="diff-added">%s</div>' % (line,)
            elif marker == "-":
                print '<div class="diff-removed">%s</div>' % (line,)
            else:
                print '<div>%s</div>' % (line,)
    else:
        print '<pre>'
        for line in lines:
            marker = line[0]
            if marker == "@":
                print '<hr>'
            request.write(cgi.escape(line))
        print '</pre>'

    wikiutil.send_footer(request, pagename, showpage=1)


def do_info(pagename, request):
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    def history(page, pagename, request):
        from stat import ST_MTIME, ST_SIZE
        _ = request.getText

        # generate history list
        currentpage = os.path.join(config.text_dir, wikiutil.quoteFilename(pagename))
        revisions = [currentpage]

        oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
        if oldversions:
            for file in oldversions:
                revisions.append(os.path.join(config.backup_dir, file))
        # open log for this page
        from MoinMoin import editlog
        from MoinMoin.util.dataset import TupleDataset, Column

        log = editlog.EditLog(request)
        log.filter(pagename=pagename)

        history = TupleDataset()
        history.columns = [
            Column('count', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size',  label=_('Size'), align='right'),
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
                mtime = int(string.split(os.path.basename(file), '.')[1])
            except IndexError:
                mtime = st[ST_MTIME]
            ##print count, mtime, st[ST_MTIME], "<br>"

            log.find(ed_time=mtime)

            actions = ""
            if file != currentpage:
                actions = '%s&nbsp;%s' % (actions, page.link_to(
                    text=_('view'),
                    querystr='action=recall&date=%d' % mtime))
                if may_revert:
                    actions = '%s&nbsp;%s' % (actions, page.link_to(
                        text=_('revert'),
                        querystr='action=revert&date=%d' % mtime))
                actions = '%s&nbsp;%s' % (actions, page.link_to(
                    text=_('diff'),
                    querystr='action=diff&date=%d' % mtime))

            comment = log.comment
            if log.action.find('/REVERT') != -1:
                datestamp = request.user.getFormattedDateTime(float(comment))
                comment = _("Revert to version dated %(datestamp)s.") % locals()

            history.addRow((
                count,
                '&nbsp;' + request.user.getFormattedDateTime(st[ST_MTIME]),
                '&nbsp;' + str(st[ST_SIZE]),
                log.getEditor() or _("N/A"),
                cgi.escape(comment) or '&nbsp;',
                actions,
                ))
            count = count + 1
            if count > 100: break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget
        from MoinMoin.formatter.text_html import Formatter

        request.formatter = Formatter(request)
        history_table = DataBrowserWidget(request)
        history_table.setData(history)
        history_table.render()

    _ = request.getText
    page = Page(pagename)
    qpagename = wikiutil.quoteWikiname(pagename)

    default_view = ('<p>%s</p>' %
        wikiutil.link_tag('%s?action=info' % qpagename,
             _('Return to general page information')))

    webapi.http_headers(request)
    wikiutil.send_title(request, _('Info for "%s"') % (pagename,), pagename=pagename)

    # info generated at a cost is only displayed on demand
    show_hitcounts = int(request.form.getvalue('hitcounts', 0)) != 0
    show_history = int(request.form.getvalue('history', 0)) != 0

    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(default_view)
        request.write(hitcounts.linkto(pagename, request, 'page=' + urllib.quote_plus(pagename)))
    elif show_history:
        print '<h2>' + _('Revision History') + '</h2>\n'
        request.write(default_view)
        history(page, pagename, request)
    else:
        print '<h2>' + _('General Information') + '</h2>\n'

        # show SHA digest fingerprint
        import sha
        digest = string.upper(sha.new(page.get_raw_body()).hexdigest())
        print _("<p>SHA digest of this page's content is: <tt>%(digest)s</tt></p>") % locals()

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
                        request.write(userhomepage.link_to() + ' ')
                    else:
                        request.write(user.name + ' ')
            request.write('</p>')

        # show links
        links = page.getPageLinks(request)
        if links:
            print _('This page links to the following pages:<br>')
            for linkedpage in links:
                print "%s%s" % (Page(linkedpage).link_to(), ",."[linkedpage == links[-1]])
            print "<p>"

        # links to detailed info
        historylink =  wikiutil.link_tag('%s?action=info&history=1' % qpagename,
            _('Show "%(title)s"') % {'title': _('Revision History')})
        hitcountlink = wikiutil.link_tag('%s?action=info&hitcounts=1' % qpagename,
            _('Show chart "%(title)s"') % {'title': _('Page hits and edits')})
        request.write("<h2>%s</h2>\n<p>%s<br />%s<br /></p>" % (
            _('Detailed Information'), historylink, hitcountlink))

    wikiutil.send_footer(request, pagename, showpage=1)


def do_recall(pagename, request):
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return
    Page(pagename, date=request.form['date'].value).send_page(request)


def do_show(pagename, request):
    Page(pagename).send_page(request, count_hit=1)


def do_refresh(pagename, request):
    if request.form.has_key('arena') and request.form.has_key('key'):
        from MoinMoin import caching
        cache = caching.CacheEntry(request.form["arena"].value, request.form["key"].value)
        cache.remove()

    do_show(pagename, request)


def do_print(pagename, request):
    do_show(pagename, request)


def do_content(pagename, request):
    webapi.http_headers(request)
    page = Page(pagename)
    print '<!-- Transclusion of %s -->' % webapi.getQualifiedURL(page.url())
    page.send_page(request, count_hit=0, content_only=1)
    sys.exit(0)


def do_edit(pagename, request):
    if not request.user.may.edit(pagename):
        _ = request.getText
        Page(pagename).send_page(request,
            msg=_('<b>You are not allowed to edit this page.</b>'))
        return
    from MoinMoin.PageEditor import PageEditor
    PageEditor(pagename, request).sendEditor()


def do_revert(pagename, request):
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText

    if not request.user.may.revert(pagename):
        return Page(pagename).send_page(request,
            msg='<strong>%s</strong>' %
                _('You are not allowed to revert this page!'))

    date = request.form['date'].value
    oldpg = Page(pagename, date=date)
    pg = PageEditor(pagename, request)

    savemsg = pg.saveText(oldpg.get_raw_body(), '0',
        stripspaces=0, notify=1, comment=date, action="SAVE/REVERT")
    request.reset()
    pg.send_page(request, msg=savemsg)


def do_savepage(pagename, request):
    from MoinMoin.PageEditor import PageEditor

    _ = request.getText

    if not request.user.may.edit(pagename):
        Page(pagename).send_page(request,
            msg=_('<b>You are not allowed to edit this page.</b>'))
        return

    pg = PageEditor(pagename, request)
    savetext = request.form.getvalue('savetext', '')
    datestamp = request.form.getvalue('datestamp', '')
    comment = request.form.getvalue('comment', '')
    category = request.form.getvalue('category', None)
    try:
        rstrip = int(request.form['rstrip'].value)
    except (KeyError, ValueError):
        rstrip = 0
    try:
        notify = int(request.form['notify'].value)
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
    comment = string.translate(comment, remap_chars, control_chars)

    if request.form.has_key('button_preview') or request.form.has_key('button_spellcheck') \
            or request.form.has_key('button_newwords'):
        pg.sendEditor(preview=savetext, comment=comment)
    elif request.form.has_key('button_cancel'):
        pg.sendCancel(savetext, datestamp)
    else:
        savemsg = pg.saveText(savetext, datestamp,
            stripspaces=rstrip, notify=notify, comment=comment)
        request.reset()
        backto = request.form.getvalue('backto', None)
        if backto:
            pg = Page(backto)
        pg.send_page(request, msg=savemsg)
        ## webapi.http_redirect(request, pg.url())


def do_subscribe(pagename, request):
    """ Add the current wiki page to the subscribed_page property in
        current user profile.
    """
    _ = request.getText

    if not request.user.may.read(pagename):
        msg = _("<b>You are not allowed to subscribe to "
                "a page you can't read.</b>")

    # check config
    elif not config.mail_smarthost:
        msg = _('''
<b>This wiki is not enabled for mail processing.<br>
Contact the owner of the wiki, who can either enable email,
or remove the "Subscribe" icon.</b>
''')

    # check whether the user has a profile
    elif not request.user.valid:
        msg = _('''
<b>You didn't create a user profile yet.<br>
Select UserPreferences in the upper right corner to create a profile.</b>
''')

    # check whether the user has an email address
    elif not request.user.email:
        msg = _('''
<b>You didn't enter an email address in your profile.<br>
Select your name (UserPreferences) in the upper right corner and
enter a valid email address.</b>
''')

    # check whether already subscribed
    elif request.user.isSubscribedTo([pagename]):
        msg = _('<b>You are already subscribed to this page.</b>') + \
              _('''<br>
<b>To unsubscribe, go to your profile and delete this page
from the subscription list.</b>
''')
        
    # subscribe to current page
    else:
        if request.user.subscribePage(pagename):
            request.user.save()
        msg = _('<b>You have been subscribed to this page.</b>') + \
              _('''<br>
<b>To unsubscribe, go to your profile and delete this page
from the subscription list.</b>
''')

    Page(pagename).send_page(request, msg=msg)


def do_userform(pagename, request):
    from MoinMoin import userform
    savemsg = userform.savedata(pagename, request)
    Page(pagename).send_page(request, msg=savemsg)


def do_bookmark(pagename, request):
    if request.form.has_key('time'):
        try:
            tm = int(request.form["time"].value)
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


def do_macro(pagename, request):
    """ Execute a helper action within a macro.
    """
    from MoinMoin import wikimacro

    macro_name = request.form["macro"].value
    function = 'do_' + request.form["do"].value

    wikimacro.execute_external_macro(macro_name, function, (pagename, request))


#############################################################################
### Special Actions
#############################################################################

def do_raw(pagename, request):
    if not request.user.may.read(pagename):
        Page(pagename).send_page(request)
        return

    webapi.http_headers(request, ["Content-type: text/plain"])

    try:
        page = Page(pagename, date=request.form['date'].value)
    except KeyError:
        page = Page(pagename)

    request.write(page.get_raw_body())
    sys.exit(0)


def do_format(pagename, request):
    # get the MIME type
    if request.form.has_key('mimetype'):
        mimetype = request.form['mimetype'].value
    else:
        mimetype = "text/plain"

    # try to load the formatter
    Formatter = pysupport.importName("MoinMoin.formatter." +
        string.translate(mimetype, string.maketrans('/.', '__')), "Formatter")
    if Formatter is None:
        # default to plain text formatter
        del Formatter
        mimetype = "text/plain"
        from formatter.text_plain import Formatter

    #webapi.http_headers(request, ["Content-Type: " + mimetype])
    webapi.http_headers(request, ["Content-Type: " + 'text/plain'])

    Page(pagename, formatter = Formatter(request)).send_page(request)
    sys.exit(0)


def do_rss_rc(pagename, request):
    from MoinMoin.macro import RecentChanges
    RecentChanges.do_rss_rc(pagename, request)


def do_chart(pagename, request):
    if not request.user.may.read(pagename):
        sys.exit(0)

    chart_type = request.form['type'].value
    func = pysupport.importName("MoinMoin.stats." + chart_type, "draw")
    func(pagename, request)
    sys.exit(0)


def do_dumpform(pagename, request):
    data = util.dumpFormData(request.form)

    webapi.http_headers(request)
    print "<html><body>"
    print data
    print "</body></html>"
    sys.exit(0)


def do_export(pagename, request):
    import shutil, cStringIO
    from MoinMoin.wikixml import wikiexport

    # Protect this with ACLs, when ready!

    # get parameters
    compression = request.form.getvalue('compression', None)

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
    webapi.http_headers(request, headers)

    # copy the body
    outbuff.reset()
    shutil.copyfileobj(outbuff, sys.stdout, 8192)
    sys.exit(0)


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

    # try to load extension action
    from MoinMoin.action import extension_actions
    if action in extension_actions:
        # load extension action
        return pysupport.importName("MoinMoin.action." + action, identifier)

    # try plugins
    dir, plugins = getPlugins()
    if action in plugins:
        # load plugin action
        return pysupport.importPlugin(dir, "MoinMoin.plugin.action", action, identifier)

    # unknown action
    return None


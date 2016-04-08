"""
    MoinMoin - Action Handlers

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: action.py,v 1.8 2000/12/06 10:48:50 jhermann Exp $
"""

# Imports
import cgi, os, re, string, sys, time
from MoinMoin import config, user, util, wikiutil
from MoinMoin.Page import Page


#############################################################################
### Search
#############################################################################

def do_fullsearch(pagename, form):
    util.http_headers()

    if form.has_key('value'):
        needle = form["value"].value
    else:
        needle = ''

    wikiutil.send_title('Full text search for "%s"' % (needle,))

    try:
        needle_re = re.compile(needle, re.IGNORECASE)
    except:
        needle_re = re.compile(re.escape(needle), re.IGNORECASE)

    ##print "<pre>", needle, "</pre>", "<hr>"

    hits = []
    all_pages = wikiutil.getPageList(config.text_dir)
    for page_name in all_pages:
        body = Page(page_name).get_raw_body()
        if form.has_key('literal'):
            count = string.count(body, needle)
            ##print "#", count, "#" , "<pre>", body, "</pre>", "<hr>"
        else:
            count = len(needle_re.findall(body))
        if count:
            hits.append((count, page_name))

    # The default comparison for tuples compares elements in order,
    # so this sorts by number of hits
    hits.sort()
    hits.reverse()

    print "<UL>"
    for (count, page_name) in hits:
        print '<LI>' + Page(page_name).link_to()
        print ' . . . . ' + `count`
        print ['match', 'matches'][count != 1]
    print "</UL>"

    print_search_stats(len(hits), len(all_pages))


def do_titlesearch(pagename, form):
    # TODO: check needle is legal -- but probably we can just accept any RE

    util.http_headers()

    if form.has_key('value'):
        needle = form["value"].value
    else:
        needle = ''

    wikiutil.send_title('Title search for "%s"' % (needle,))
    
    needle_re = re.compile(needle, re.IGNORECASE)
    all_pages = wikiutil.getPageList(config.text_dir)
    hits = filter(needle_re.search, all_pages)

    print "<UL>"
    for filename in hits:
        print '<LI>' + Page(filename).link_to()
    print "</UL>"

    print_search_stats(len(hits), len(all_pages))


def print_search_stats(hits, searched):
    print "<p>%d hits " % (hits,)
    print " out of %d pages searched." % (searched,)


#############################################################################
### Misc Actions
#############################################################################

def do_diff(pagename, form):
    """ Handle "action=diff", checking for a "date=backupdate" parameter """
    util.http_headers()

    # send page title
    wikiutil.send_title('Diff for "%s"' % (pagename,), pagename=pagename)

    # get a list of old revisions, and back out if none are available
    try:
        oldpage = wikiutil.quoteFilename(pagename) + "." + os.path.basename(form['date'].value)
    except:
        oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
        if not oldversions:
            print "<b>No older revisions available!</b>"
            wikiutil.send_footer(pagename, showpage=1)
            return
        oldpage = oldversions[0]

    # build the diff command and execute it
    cmd = "diff -u %(backup)s %(page)s" % {
        "page": os.path.join(config.text_dir, wikiutil.quoteFilename(pagename)),
        "backup": os.path.join(config.backup_dir, oldpage)
    }
    diff = util.popen(cmd, "r")
    lines = diff.readlines()
    rc = diff.close()
    ##print "cmd =", cmd, "<br>"
    ##print "rc =", rc, "<br>"

    # check for valid diff
    if not lines:
        print "<b>No differences found!</b>"
        wikiutil.send_footer(pagename, showpage=1)
        return

    # Show date info
    print '<b>Differences between version dated',
    if lines[0][0:3] == "---":
        print string.split(lines[0], ' ', 2)[2],
        del lines[0]
    print 'and',
    if lines[0][0:3] == "+++":
        print string.split(lines[0], ' ', 2)[2],
        del lines[0]
    print '</b>'
    print '<div class="diffold">Deletions are marked like this.</div>'
    print '<div class="diffnew">Additions are marked like this.</div>'

    # Show diff
    for line in lines:
        marker = line[0]
        line = cgi.escape(line[1:])
        stripped = string.lstrip(line)
        if len(line) - len(stripped):
            line = "&nbsp;" * (len(line) - len(stripped)) + stripped

        if marker == "@":
            print '<hr style="color:#FF3333">'
        elif marker == "\\":
            if stripped == "No newline at end of file\n": continue
            print '<div><font size="1" face="Verdana">%s&nbsp;</font></div>' % (line,)
        elif marker == "+":
            print '<div class="diffnew">%s&nbsp;</div>' % (line,)
        elif marker == "-":
            print '<div class="diffold">%s&nbsp;</div>' % (line,)
        else:
            print '<div>%s</div>' % (line,)

    wikiutil.send_footer(pagename, showpage=1)


def do_info(pagename, form):
    from stat import *

    util.http_headers()

    wikiutil.send_title('Info for "%s"' % (pagename,), pagename=pagename)

    revisions = [os.path.join(config.text_dir, wikiutil.quoteFilename(pagename))]

    oldversions = wikiutil.getBackupList(config.backup_dir, pagename)
    if oldversions:
        for file in oldversions:
            revisions.append(os.path.join(config.backup_dir, file))

    print '<h2>Revision History</h2>\n'
    print '<table border="1" cellpadding="2" cellspacing="0">\n'
    print '<tr><th>#</th><th>Date</th><th>Size</th><th>Action</th></tr>\n'
    count = 1
    for file in revisions:
        st = os.stat(file)
        actions = ""
        if count > 1:
            actions = '%s&nbsp;<a href="%s/%s?action=recall&date=%s">view</a>' % (
                actions,
                util.getScriptname(),
                wikiutil.quoteWikiname(pagename),
                os.path.basename(file)[len(wikiutil.quoteFilename(pagename))+1:])
            actions = '%s&nbsp;<a href="%s/%s?action=diff&date=%s">diff</a>' % (
                actions,
                util.getScriptname(),
                wikiutil.quoteWikiname(pagename),
                os.path.basename(file)[len(wikiutil.quoteFilename(pagename))+1:])
        print '<tr><td align="right">%d</td><td>&nbsp;%s</td><td align="right">&nbsp;%d</td><td>&nbsp;%s</td></tr>\n' % (
            count,
            time.strftime(config.datetime_fmt, user.current.getTime(st[ST_MTIME])),
            st[ST_SIZE],
            actions)
        count = count + 1
        if count > 100: break
    print '</table>\n'
    
    wikiutil.send_footer(pagename, showpage=1)


def do_recall(pagename, form):
    Page(pagename, date=form['date'].value).send_page(form)


def do_show(pagename, form):
    Page(pagename).send_page(form)


def do_print(pagename, form):
    Page(pagename).send_page(form, None, 1)


def do_edit(pagename, form):
    Page(pagename).send_editor(form)


def do_savepage(pagename, form):
    pg = Page(pagename)
    savetext = ""
    datestamp = ""
    try:
        savetext = form['savetext'].value
        datestamp = form['datestamp'].value
    except:
        pass
    savemsg = pg.save_text(savetext, datestamp)
    pg.send_page(form, msg=savemsg)


def do_userform(pagename, form):
    savemsg=user.savedata(pagename, form)
    Page(pagename).send_page(form, msg=savemsg)


def do_bookmark(pagename, form):
    user.current.setBookmark()
    Page(pagename).send_page(form)


#############################################################################
### Special Actions
#############################################################################

def do_raw(pagename, form):
    util.http_headers(["Content-type: text/plain"])

    sys.stdout.write(Page(pagename).get_raw_body())
    sys.exit(0)


def do_format(pagename, form):
    # get the MIME type
    if form.has_key('mimetype'):
        mimetype = form['mimetype'].value
    else:
        mimetype = "text/plain"

    # try to load the formatter
    Formatter = util.importName("MoinMoin.formatter." +
        string.replace(mimetype, '/', '_'), "Formatter")
    if Formatter is None:
        # default to plain text formatter
        del Formatter
        mimetype = "text/plain"
        from formatter.text_plain import Formatter

    util.http_headers(["Content-Type: " + mimetype])
    print

    Page(pagename, formatter = Formatter()).send_page(form)
    sys.exit(0)


#############################################################################
### Dispatch Table
#############################################################################

handlers = { 'fullsearch':  do_fullsearch,
             'titlesearch': do_titlesearch,
             'edit':        do_edit,
             'diff':        do_diff,
             'info':        do_info,
             'recall':      do_recall,
             'show':        do_show,
             'print':       do_print,
             'raw':         do_raw,
             'format':      do_format,
             'savepage':    do_savepage,
             'userform':    do_userform,
             'bookmark':    do_bookmark,
}


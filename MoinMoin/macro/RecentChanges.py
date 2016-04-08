"""
    MoinMoin - RecentChanges Macro

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: RecentChanges.py,v 1.21 2001/04/03 20:28:52 jhermann Exp $
"""

# Imports
import re, string, time
from cStringIO import StringIO
from MoinMoin import config, editlog, user, wikiutil
from MoinMoin.Page import Page


def execute(macro, args):
    log = editlog.EditLog()

    tnow = time.time()
    daycount = 0
    ratchet_day = None
    done_words = {}
    msg = ""
    buf = StringIO()

    # add bookmark link if valid user
    bookmark = user.current.getBookmark()
    if user.current.valid:
        bm_display = user.current.text('(no bookmark set)')
        if bookmark:
            bm_display = user.current.text('(currently set to %s)') % (
                user.current.getFormattedDateTime(bookmark),)

        buf.write("%s %s<br>" % (
            wikiutil.link_tag(
                wikiutil.quoteWikiname(macro.formatter.page.page_name)
                    + "?action=bookmark&time=%d" % (tnow,),
                user.current.text("Update my bookmark timestamp")),
            bm_display,
        ))

    oldversions = wikiutil.getBackupList(config.backup_dir, None)

    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    while log.next():
        # skip already processed pages
        if done_words.has_key(log.pagename):
            continue

        # check for configured max size
        if config.max_macro_size and buf.tell() > config.max_macro_size*1024:
            msg = "<br><font size='-1'>[Size limited to %dK]</font>" % (config.max_macro_size,)
            break

        # year, month, day, DoW
        time_tuple = user.current.getTime(log.ed_time)
        day = tuple(time_tuple[0:3])
        if day <> ratchet_day:
            daycount = daycount + 1
            if daycount > 14: break

            set_bm = ''
            if user.current.valid:
                set_bm = '&nbsp;<font size="1" face="Verdana">[%s]</font>' % (
                    wikiutil.link_tag(
                        wikiutil.quoteWikiname(macro.formatter.page.page_name)
                            + "?action=bookmark&time=%d" % (log.ed_time,),
                        user.current.text("set bookmark")),)

            buf.write('<tr><td colspan="%d"><br/><font size="+1"><b>%s</b></font>%s</td></tr>\n'
                % (3+config.show_hosts, user.current.getFormattedDate(log.ed_time), set_bm))
            ratchet_day = day

        # remember we did print this page
        done_words[log.pagename] = 1

        # check whether this page is newer than the user's bookmark
        hilite = log.ed_time > (bookmark or log.ed_time)

        # check whether this is a new (no backup) page
        # !!! the backup dir needs to be reorganized, one subdir per page, and the versions
        # in the subdirs, i.e. data/backup/<pagename>/<timestamp>; this will do for now
        backup_re = re.compile(r'^%s\.\d+(\.\d+)?$' % (wikiutil.quoteFilename(log.pagename),))
        is_new = len(filter(backup_re.match, oldversions)) == 0
        page = Page(log.pagename)

        html_link = ''
        if hilite and not page.exists():
            # indicate page was deleted
            html_link = '<img border="0" hspace="3" width="60" height="12" src="%s/img/moin-deleted.gif" alt="[DELETED]">' % (
                config.url_prefix)
        elif is_new:
            # show "NEW" icon if page was created after the user's bookmark
            if hilite:
                if page.exists():
                    html_link = '<img border="0" hspace="3" width="31" height="12" src="%s/img/moin-new.gif" alt="[NEW]">' % (
                        config.url_prefix)
        elif hilite:
            # show "UPDATED" icon if page was edited after the user's bookmark
            img = '<img border="0" hspace="3" width="60" height="12" src="%s/img/moin-updated.gif" alt="[UPDATED]">' % (
                config.url_prefix)
            html_link = wikiutil.link_tag(
                wikiutil.quoteWikiname(log.pagename) + "?action=diff&date=" + str(bookmark), img)
        else:
            # show "DIFF" icon else
            img = '<img border="0" hspace="11" width="15" height="11" src="%s/img/moin-diff.gif" alt="[DIFF]">' % (
                config.url_prefix)
            html_link = wikiutil.link_tag(
                wikiutil.quoteWikiname(log.pagename) + "?action=diff", img)

        buf.write('<tr><td>%s&nbsp;</td><td>%s</td><td>&nbsp;' % (
            html_link, page.link_to(),))

        if config.changed_time_fmt:
            tdiff = int(tnow - log.ed_time) / 60
            if tdiff < 1440:
                buf.write(user.current.text("[%(hours)dh&nbsp;%(mins)dm&nbsp;ago]") % {
                    'hours': tdiff/60, 'mins': tdiff%60})
            else:
                buf.write(time.strftime(config.changed_time_fmt, time_tuple))
            buf.write("&nbsp;</td><td>&nbsp;")

        if config.show_hosts:
            buf.write(log.getEditor())

        buf.write('</td></tr>\n')

    buf.write('</table>')
    if msg: buf.write(msg)

    return buf.getvalue()


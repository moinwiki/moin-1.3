"""
    MoinMoin - RecentChanges Macro

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: RecentChanges.py,v 1.6 2000/12/05 23:32:53 jhermann Exp $
"""

# Imports
import string, time
from cStringIO import StringIO
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page


def execute(macro, args):
    lines = wikiutil.editlog_raw_lines()
    lines.reverse()

    tnow = time.time()
    daycount = 0
    ratchet_day = None
    done_words = {}
    users = {}
    msg = ""
    buf = StringIO()

    # add bookmark link if valid user
    bookmark = user.current.getBookmark()
    if user.current.valid:
        bm_display = '(no bookmark set)'
        if bookmark:
            bm_display = '(currently set to %s)' % (
                time.strftime(config.datetime_fmt, user.current.getTime(bookmark)),)

        buf.write("%s %s<br>" % (
            wikiutil.link_tag(
                wikiutil.quoteWikiname(macro.formatter.page.page_name) + "?action=bookmark",
                "Update my bookmark timestamp"),
            bm_display,
        ))

    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    for line in lines:
        # parse the editlog line
        fields = string.split(string.strip(line), '\t')
        while len(fields) < 5: fields.append('')
        page_name, addr, ed_time, hostname, userid = fields[:5]
        if not hostname:
            hostname = addr
        page_name = wikiutil.unquoteFilename(page_name)
        ed_time = float(ed_time)

        if done_words.has_key(page_name):
            continue

        # check for configured max size
        if config.max_macro_size and buf.tell() > config.max_macro_size*1024:
            msg = "<br><font size='-1'>[Size limited to %dK]</font>" % (config.max_macro_size,)
            break

        # year, month, day, DoW
        time_tuple = user.current.getTime(ed_time)
        day = tuple(time_tuple[0:3])
        if day <> ratchet_day:
            daycount = daycount + 1
            if daycount > 14: break

            buf.write('<tr><td colspan="%d"><br/><font size="+1"><b>%s</b></font></td></tr>\n'
                % (3+config.show_hosts, time.strftime(config.date_fmt, time_tuple)))
            ratchet_day = day

        done_words[page_name] = 1
        hilite = ed_time > (bookmark or ed_time)
        buf.write('<tr><td>&nbsp;&nbsp;%s[%s]%s&nbsp;</td><td>%s</td><td>&nbsp;' % (
            ('', '<b>')[hilite],
            wikiutil.link_tag(wikiutil.quoteWikiname(page_name) + "?action=diff", "diff"),
            ('', '</b>')[hilite],
            Page(page_name).link_to(),))

        if config.changed_time_fmt:
            tdiff = int(tnow - ed_time) / 60
            if tdiff < 1440:
                buf.write("[%dh&nbsp;%dm&nbsp;ago]" % (tdiff/60, tdiff%60))
            else:
                buf.write(time.strftime(config.changed_time_fmt, time_tuple))
            buf.write("&nbsp;</td><td>&nbsp;")

        if config.show_hosts:
            if userid:
                if not users.has_key(userid): users[userid] = user.User(userid)
                userdata = users[userid]
                if userdata.name:
                    pg = Page(userdata.name)
                    if pg.exists():
                        buf.write(pg.link_to())
                    else:
                        buf.write(userdata.name or hostname)
                else:
                    buf.write(hostname)
            else:
                buf.write(hostname)

        buf.write('</td></tr>\n')

    buf.write('</table>')
    if msg: buf.write(msg)

    return buf.getvalue()




"""
    MoinMoin - RecentChanges Macro

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: RecentChanges.py,v 1.59 2002/05/02 19:13:07 jhermann Exp $
"""

# Imports
import cgi, re, string, sys, time, cStringIO
from MoinMoin import config, editlog, user, util, wikiutil, wikixml
from MoinMoin.Page import Page
from MoinMoin.i18n import _

_MAX_DAYS = 14
_MAX_PAGENAME_LENGTH = 35

#############################################################################
### RecentChanges Macro
#############################################################################

def execute(macro, args, **kw):
    abandoned = kw.get('abandoned', 0)
    log = LogIterator(macro.request, reverse=abandoned)

    tnow = time.time()
    msg = ""
    buf = cStringIO.StringIO()

    # add rss link
    if wikixml.ok and not abandoned:
        img = macro.formatter.image(width=36, height=14, hspace=2, align="right",
            border=0, src=config.url_prefix+"/img/moin-rss.gif", alt="[RSS]")
        buf.write(macro.formatter.url(
            wikiutil.quoteWikiname(macro.formatter.page.page_name) + "?action=rss_rc",
            img, unescaped=1))

    # add bookmark link if valid user
    if abandoned:
        bookmark = None
    else:
        bookmark = macro.request.user.getBookmark()
        if macro.request.user.valid:
            bm_display = _('(no bookmark set)')
            if bookmark:
                bm_display = _('(currently set to %s)') % (
                    macro.request.user.getFormattedDateTime(bookmark),)

            buf.write("%s %s<br>" % (
                wikiutil.link_tag(
                    wikiutil.quoteWikiname(macro.formatter.page.page_name)
                        + "?action=bookmark&time=%d" % (tnow,),
                    _("Update my bookmark timestamp"),
                    formatter=macro.formatter),
                bm_display,
            ))

    oldversions = wikiutil.getBackupList(config.backup_dir, None)

    # get the most recent date each page was edited
    if abandoned:
        # !!! TODO: add existing pages that do not appear in the edit log at all
        last_edit = {}
        while log.next():
            last_edit[log.pagename] = log.ed_time
        log.reset()

    buf.write('<table border=0 cellspacing=2 cellpadding=0>')
    while log.getNextChange():
        if abandoned and log.ed_time < last_edit[log.pagename]:
            continue

        # check for configured max size
        if config.max_macro_size and buf.tell() > config.max_macro_size*1024:
            msg = "<br><font size='-1'>[Size limited to %dK]</font>" % (config.max_macro_size,)
            break

        if log.dayChanged():
            if log.daycount > _MAX_DAYS: break

            set_bm = ''
            if macro.request.user.valid and not abandoned:
                set_bm = '&nbsp;<font size="1" face="Verdana">[%s]</font>' % (
                    wikiutil.link_tag(
                        wikiutil.quoteWikiname(macro.formatter.page.page_name)
                            + "?action=bookmark&time=%d" % (log.ed_time,),
                        _("set bookmark"), formatter=macro.formatter),)

            buf.write('<tr><td colspan="%d"><br/><font size="+1"><b>%s</b></font>%s</td></tr>\n'
                % (4+config.show_hosts, macro.request.user.getFormattedDate(log.ed_time), set_bm))

        # check whether this page is newer than the user's bookmark
        hilite = log.ed_time > (bookmark or log.ed_time)

        # check whether this is a new (no backup) page
        # !!! the backup dir needs to be reorganized, one subdir per page, and the versions
        # in the subdirs, i.e. data/backup/<pagename>/<timestamp>; this will do for now
        backup_re = re.compile(r'^%s\.\d+(\.\d+)?$' % (wikiutil.quoteFilename(log.pagename),))
        is_new = len(filter(backup_re.match, oldversions)) == 0
        page = Page(log.pagename)

        html_link = ''
        if not page.exists():
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
                wikiutil.quoteWikiname(log.pagename) + "?action=diff&date=" + str(bookmark),
                img, formatter=macro.formatter, pretty_url=1)
        else:
            # show "DIFF" icon else
            img = '<img border="0" hspace="11" width="15" height="11" src="%s/img/moin-diff.gif" alt="[DIFF]">' % (
                config.url_prefix)
            html_link = wikiutil.link_tag(
                wikiutil.quoteWikiname(log.pagename) + "?action=diff",
                img, formatter=macro.formatter, pretty_url=1)

        # print name of page, with a link to it
        force_split = len(page.page_name) > _MAX_PAGENAME_LENGTH
        buf.write('<tr valign="top"><td>%s&nbsp;</td><td>%s</td><td>&nbsp;' % (
            html_link, page.link_to(text=page.split_title(force=force_split)),))

        # print time of change
        if config.changed_time_fmt:
            tdiff = int(tnow - log.ed_time) / 60
            if tdiff < 1440:
                buf.write(_("[%(hours)dh&nbsp;%(mins)dm&nbsp;ago]") % {
                    'hours': int(tdiff/60), 'mins': tdiff%60})
            else:
                buf.write(time.strftime(config.changed_time_fmt, log.time_tuple))
            buf.write("&nbsp;</td><td>&nbsp;")

        changelog   = log.changes[log.pagename]
        changecount = len(changelog)

        # print editor name or IP
        if config.show_hosts:
            if changecount > 1:
                counters = {}
                for idx in range(len(changelog)):
                    name = changelog[idx][0]
                    if not counters.has_key(name): counters[name] = []
                    counters[name].append(idx+1)
                poslist = map(None,  counters.values(), counters.keys())
                poslist.sort()
                ##buf.write(repr(counters.items()))
                hardspace = ''
                for positions, name in poslist:
                    buf.write("%s%s[%s]<br>" % (
                        hardspace, name, util.rangelist(positions)))
                    hardspace = '&nbsp;'
            else:
                buf.write(log.getEditor())

        if changecount > 1:
            ##buf.write(repr(changelog))
            comments = ''
            for idx in range(changecount):
                comment = changelog[idx][1]
                if comment:
                    comments = '%s%s<tt>#%02d</tt>&nbsp;<b>%s</b>' % (
                        comments, comments and '<br>' or '', idx+1,
                        cgi.escape(comment))

            buf.write('&nbsp;</td><td nowrap align="right">&nbsp;%s&nbsp;&nbsp;'
                      '</td><td width="70%%">%s&nbsp;' %
                (_('%(changecount)s changes') % locals(), comments) )
        else:
            buf.write("&nbsp;</td><td></td><td><b>%s</b>&nbsp;" %
                cgi.escape(changelog[0][1]))

        buf.write('</td></tr>\n')

    buf.write('</table>')
    if msg: buf.write(msg)

    return macro.formatter.rawHTML(buf.getvalue())


#############################################################################
### LogIterator
#############################################################################

class LogIterator(editlog.EditLog):

    def __init__(self, request, **kw):
        apply(editlog.EditLog.__init__, (self,), kw)
        self.request = request
        self.changes = {}
        self.daycount = 0
        self.ratchet_day = None
        self.unique = kw.get('unique', 1)

    def getNextChange(self):
        if not self.next(): return 0
        if not self.unique: return 1

        # skip already processed pages
        while self.changes.has_key(self.pagename):
            if not self.next(): return 0

        # we see this page for the first time, collect changes in this day
        thispage = self.pagename
        self.changes[thispage] = []
        offset = 0
        ratchet_day = None
        while 1:
            time_tuple = self.request.user.getTime(self.ed_time)
            day = tuple(time_tuple[0:3])
            if not ratchet_day: ratchet_day = day
            if day != ratchet_day: break

            # store comments for this page
            if self.pagename == thispage:
                comment = self.comment
                if self.action[:3] == 'ATT':
                    import urllib
                    filename = urllib.unquote(comment)
                    if self.action == 'ATTNEW':
                        comment = _("Upload of attachment '%(filename)s'.") % locals()
                    elif self.action == 'ATTDEL':
                        comment = _("Attachment '%(filename)s' deleted.") % locals()
                    elif self.action == 'ATTDRW':
                        comment = _("Drawing '%(filename)s' saved.") % locals()
                self.changes[thispage].append((self.getEditor(), comment))
            # peek for the next one
            if not self.peek(offset): break
            offset = offset + 1

        # restore correct data
        return self.peek(-1)

    def dayChanged(self):
        self.time_tuple = self.request.user.getTime(self.ed_time)
        self.day = tuple(self.time_tuple[0:3])
        if self.day != self.ratchet_day:
            self.daycount = self.daycount + 1
            self.ratchet_day = self.day
            return 1
        return 0


#############################################################################
### RSS Handling
#############################################################################
if wikixml.ok:

    from MoinMoin.wikixml.util import RssGenerator

    def rss(pagename, request):
        """ Send recent changes as an RSS document
        """
        from MoinMoin import webapi
        import os, new

        # get params
        items_limit = 100
        try:
            max_items = int(request.form['items'].value)
            max_items = min(max_items, items_limit) # not more than `items_limit`
        except (KeyError, ValueError):
            # not more than 15 items in a RSS file by default
            max_items = 15
        try:
            unique = int(request.form.getvalue('unique', 0))
        except ValueError:
            unique = 0
        try:
            diffs = int(request.form.getvalue('diffs', 0))
        except ValueError:
            diffs = 0

        # prepare output
        out = cStringIO.StringIO()
        handler = RssGenerator(out)

        # get data
        interwiki = webapi.getBaseURL()
        if interwiki[-1] != "/": interwiki = interwiki + "/"

        logo = re.search(r'src="([^"]*)"', config.logo_string)
        if logo: logo = webapi.getQualifiedURL(logo.group(1))

        log = LogIterator(request, unique=unique)
        logdata = []
        counter = 0
        Bag = new.classobj('Bag', (), {})
        while log.getNextChange():
            if log.dayChanged() and log.daycount > _MAX_DAYS: break
            if log.action != 'SAVE': continue
            logdata.append(new.instance(Bag, {
                'ed_time': log.ed_time,
                'time': log.time_tuple,
                'pagename': log.pagename,
                'hostname': log.hostname,
                'editor': log.getEditorData(),
                'comment': log.comment,
            }))

            counter = counter + 1
            if counter >= max_items: break
        del log

        # start SAX stream
        handler.startDocument()
        handler._out.write(
            '<!--\n'
            '    Add an "items=nnn" URL parameter to get more than the default 15 items.\n'
            '    You cannot get more than %d items though.\n'
            '    \n'
            '    Add "unique=1" to get a list of changes where page names are unique,\n'
            '    i.e. where only the latest change of each page is reflected.\n'
            '    \n'
            '    Add "diffs=1" to add change diffs to the description of each items.\n'
            '-->\n' % items_limit
        )

        # emit channel description
        handler.startNode('channel', {
            (handler.xmlns['rdf'], 'about'): webapi.getBaseURL(),
        })
        handler.simpleNode('title', config.sitename)
        handler.simpleNode('link', interwiki + wikiutil.quoteWikiname(pagename))
        handler.simpleNode('description', 'RecentChanges at %s' % config.sitename)
        if logo:
            handler.simpleNode('image', None, {
                (handler.xmlns['rdf'], 'resource'): logo,
            })
        if config.interwikiname:
            handler.simpleNode(('wiki', 'interwiki'), config.interwikiname)

        handler.startNode('items')
        handler.startNode(('rdf', 'Seq'))
        for item in logdata:
            link = "%s%s#%04d%02d%02d%02d%02d%02d" % ((interwiki,
                wikiutil.quoteWikiname(item.pagename),) + item.time[:6])
            handler.simpleNode(('rdf', 'li'), None, attr={
                (handler.xmlns['rdf'], 'resource'): unicode(link, config.charset),
            })
        handler.endNode(('rdf', 'Seq'))
        handler.endNode('items')
        handler.endNode('channel')

        # emit logo data
        if logo:
            handler.startNode('image', attr={
                (handler.xmlns['rdf'], 'about'): logo,
            })
            handler.simpleNode('title', config.sitename)
            handler.simpleNode('link', interwiki)
            handler.simpleNode('url', logo)
            handler.endNode('image')

        # emit items
        for item in logdata:
            page = Page(item.pagename)
            link = interwiki + wikiutil.quoteWikiname(item.pagename)
            rdflink = "%s#%04d%02d%02d%02d%02d%02d" % ((link,) + item.time[:6])
            handler.startNode('item', attr={
                (handler.xmlns['rdf'], 'about'): rdflink,
            })

            # general attributes
            handler.simpleNode('title', item.pagename)
            handler.simpleNode('link', link)
            handler.simpleNode(('dc', 'date'), util.W3CDate(item.time))

            # description
            desc_text = item.comment
            if diffs:
                # !!! TODO: rewrite / extend wikiutil.pagediff
                # searching for the matching pages doesn't really belong here
                # also, we have a problem to get a diff between two backup versions
                # so it's always a diff to the current version for now
                oldversions = wikiutil.getBackupList(config.backup_dir, item.pagename)

                for idx in range(len(oldversions)):
                    oldpage = oldversions[idx]
                    try:
                        date = os.path.getmtime(os.path.join(config.backup_dir, oldpage))
                    except EnvironmentError:
                        continue
                    if date <= item.ed_time:
                        if idx+1 < len(oldversions):
                            rc, page_file, backup_file, lines = wikiutil.pagediff(item.pagename, oldversions[idx+1], ignorews=1)
                            if len(lines) > 20: lines = lines[20:] + ['...\n']
                            desc_text = desc_text + '<pre>\n' + string.join(lines, '') + '</pre>'
                        break
            if desc_text:
                handler.simpleNode('description', desc_text)

            # contributor
            edattr = {}
            if config.show_hosts:
                edattr[(handler.xmlns['wiki'], 'host')] = unicode(item.hostname, config.charset)
            if isinstance(item.editor, Page):
                edname = item.editor.page_name
                edattr[(None, 'link')] = interwiki + wikiutil.quoteWikiname(edname)
            else:
                edname = item.editor
                ##edattr[(None, 'link')] = link + "?action=info"
            handler.startNode(('dc', 'contributor'))
            handler.startNode(('rdf', 'Description'), attr=edattr)
            handler.simpleNode(('rdf', 'value'), edname)
            handler.endNode(('rdf', 'Description'))
            handler.endNode(('dc', 'contributor'))

            # wiki extensions
            handler.simpleNode(('wiki', 'version'), "%04d-%02d-%02d %02d:%02d:%02d" % item.time[:6])
            handler.simpleNode(('wiki', 'status'), ('deleted', 'updated')[page.exists()])
            handler.simpleNode(('wiki', 'diff'), link + "?action=diff")
            handler.simpleNode(('wiki', 'history'), link + "?action=info")
            # handler.simpleNode(('wiki', 'importance'), ) # ( major | minor ) 
            # handler.simpleNode(('wiki', 'version'), ) # ( #PCDATA ) 

            handler.endNode('item')

        # end SAX stream
        handler.endDocument()

        # send the generated XML document
        webapi.http_headers(request, ["Content-Type: " + 'text/xml'] + webapi.nocache)
        sys.stdout.write(out.getvalue())

        sys.exit(0)


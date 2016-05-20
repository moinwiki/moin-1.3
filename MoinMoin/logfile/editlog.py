"""
    MoinMoin edit log class

    @license: GNU GPL, see COPYING for details.
"""

import os.path
from logfile import LogFile
from MoinMoin import wikiutil, user, config
from MoinMoin.Page import Page

class EditLogLine:
    """
    Has the following attributes

    ed_time_usecs
    rev
    action
    pagename
    addr
    hostname
    userid
    extra
    comment
    """
    def __init__(self, usercache):
        self._usercache = usercache

    def __cmp__(self, other):
        try:
            return cmp(self.ed_time_usecs, other.ed_time_usecs)
        except AttributeError:
            return cmp(self.ed_time_usecs, other)

    def getEditorData(self, request):
        """ Return a tuple of type id and string or Page object
            representing the user that did the edit.

            The type id is one of 'ip' (DNS or numeric IP), 'user' (user name)
            or 'homepage' (Page instance of user's homepage).
        """
        result = ('ip', (request.cfg.show_hosts and self.hostname) or '')
        if self.userid:
            if not self._usercache.has_key(self.userid):
                self._usercache[self.userid] = user.User(request, self.userid)
            userdata = self._usercache[self.userid]
            if userdata.name:
                pg = wikiutil.getHomePage(request, username=userdata.name)
                if pg:
                    result = ('homepage', pg)
                else:
                    result = ('user', userdata.name)

        return result


    def getEditor(self, request):
        """ Return a HTML-safe string representing the user that did the edit.
        """
        kind, editor = self.getEditorData(request)
        if kind == 'homepage':
            return '<span title="%s">%s</span>' % (wikiutil.escape(self.hostname),
                                                   editor.link_to(request))
        elif kind == 'ip':
            idx = editor.find('.')
            if idx==-1:
                idx = len(editor)
            return '<span title="%s">%s</span>' % (wikiutil.escape(
                (request.cfg.show_hosts and ("%s=%s" % (self.addr,editor))) or ''), wikiutil.escape(editor[:idx]))
        else:
            return '<span title="%s">%s</span>' % (wikiutil.escape(
                (request.cfg.show_hosts and self.hostname) or ''), wikiutil.escape(editor))


class EditLog(LogFile):

    def __init__(self, request, filename=None, buffer_size=65536, **kw):
        if filename == None:
            rootpagename = kw.get('rootpagename', None)
            if rootpagename:
                filename = Page(request, rootpagename).getPagePath('edit-log', isfile=1)
            else:
                filename = request.rootpage.getPagePath('edit-log', isfile=1)
        LogFile.__init__(self, filename, buffer_size)
        self._NUM_FIELDS = 9
        self._usercache = {}
        
        # Used by antispam in order to show an internal name instead
        # of a confusing userid
        self.uid_override = kw.get('uid_override', None)

    def add(self, request, mtime, rev, action, pagename, host=None, extra=u'', comment=u''):
            """ Generate a line for the editlog.
    
            If `host` is None, it's read from request vars.
            """
            import socket
            
            if host is None:
                host = request.remote_addr
                
            try:
                hostname = socket.gethostbyaddr(host)[0]
            except socket.error:
                hostname = host

            remap_chars = {u'\t': u' ', u'\r': u' ', u'\n': u' ',}
            comment = comment.translate(remap_chars)
            user_id = request.user.valid and request.user.id or ''

            if self.uid_override != None:
                user_id = ''
                hostname = self.uid_override
                host = ''
            
            line = u"\t".join((str(long(mtime)), # has to be long for py 2.2.x
                               "%08d" % rev,
                               action,
                               wikiutil.quoteWikinameFS(pagename),
                               host,
                               hostname,
                               user_id,
                               extra,
                               comment,
                               )) + "\n"
            self._add(line)

    def parser(self, line):
        """ Parser edit log line into fields """
        fields = line.strip().split('\t')
        # Pad empty fields
        missing = self._NUM_FIELDS - len(fields)
        if missing:
            fields.extend([''] * missing)
        result = EditLogLine(self._usercache)
        (result.ed_time_usecs, result.rev, result.action,
         result.pagename, result.addr, result.hostname, result.userid,
         result.extra, result.comment,) = fields[:self._NUM_FIELDS]
        if not result.hostname:
            result.hostname = result.addr
        result.pagename = wikiutil.unquoteWikiname(result.pagename.encode('ascii'))
        result.ed_time_usecs = long(result.ed_time_usecs or '0') # has to be long for py 2.2.x
        return result
    
    def set_filter(self, **kw):
        expr = "1"
        for field in ['pagename', 'addr', 'hostname', 'userid']:
            if kw.has_key(field):
                expr = "%s and x.%s == %s" % (expr, field, `kw[field]`)
                
        if kw.has_key('ed_time_usecs'):
            expr = "%s and long(x.ed_time_usecs) == %s" % (expr, long(kw['ed_time_usecs'])) # must be long for py 2.2.x

        self.filter = eval("lambda x: " + expr)
    


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Page class

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import StringIO, os, re, urllib, os.path, random, codecs
from MoinMoin import config, caching, user, util, wikiutil
from MoinMoin.logfile import eventlog
from MoinMoin.util import filesys, web

# There are many places accessing ACLs even without actually sending
# the page. This cache ensures that we don't have to parse ACLs for
# some page twice.
_acl_cache = {}

# Header regular expression, used to get header boundaries
header_re = re.compile(r'(^#+.*(?:\n\s*)+)+', re.UNICODE | re.MULTILINE)


class Page:
    """Page - Manage an (immutable) page associated with a WikiName.
       To change a page's content, use the PageEditor class.
    """

    def __init__(self, request, page_name, **keywords):
        """
        Create page object.

        Note that this is a 'lean' operation, since the text for the page
        is loaded on demand. Thus, things like `Page(name).link_to()` are
        efficient.

        @param page_name: WikiName of the page
        @keyword date: date of older revision
        @keyword formatter: formatter instance
        """
        self.request = request
        self.cfg = request.cfg
        self.page_name = page_name
        self.rev = keywords.get('rev', 0)
        self._raw_body = None
        self._raw_body_modified = 0
        self.hilite_re = None
        self.language = None
        
        if keywords.has_key('formatter'):
            self.formatter = keywords.get('formatter')
            self.default_formatter = 0
        else:
            self.default_formatter = 1


    def split_title(self, request, force=0):
        """
        Return a string with the page name split by spaces, if
        the user wants that.
        
        @param request: the request object
        @param force: if != 0, then force splitting the page_name
        @rtype: unicode
        @return: pagename of this page, splitted into space separated words
        """
        if not force and not request.user.wikiname_add_spaces:
            return self.page_name
    
        # look for the end of words and the start of a new word,
        # and insert a space there
        # XXX CFG cache that!
        SPLIT_RE = re.compile('([%s])([%s])' % (config.chars_lower,
                                                config.chars_upper))
        splitted = SPLIT_RE.sub(r'\1 \2', self.page_name)
        return splitted

    def get_rev(self, pagedir=None, rev=0):
        """ 
        get a revision of the page in this path
        @param pagedir: the path to the pagedir
        @param rev: int revision to get (default is 0 and means the current
                    revision (in this case, the real revint is returned)
        @return: (str pagefilename, int realrevint, bool exists)
        """
        if pagedir is None:
            pagedir = self.getPagePath(check_create=0)
            
        if rev == 0:
            revfilename = os.path.join(pagedir, 'current')
            try:
                revfile = open(revfilename)
                revstr = revfile.read().strip()
                revfile.close()
            except:
                revstr = '99999999' # XXX
            rev = int(revstr)
        else:
            revstr = '%08d' % rev
        
        pagefile = os.path.join(pagedir, 'revisions', revstr)
        exists = os.path.exists(pagefile)
        return pagefile, rev, exists

    def current_rev(self):
        pagefile, rev, exists = self.get_rev()
        return rev
    
    def getPagePath(self, *args, **kw):
        """
        Get full path to a page-specific storage area. `args` can
        contain additional path components that are added to the base path.

        @param args: additional path components
        @keyword force_pagedir: force using a specific pagedir, default 'auto'
                                'auto' = automatically choose page dir
                                'underlay' = use underlay page dir
                                'standard' = use standard page dir
        @keyword check_create: if true, ensures that the path requested really exists
                               (if it doesn't, create all directories automatically).
                               (default true)
        @keyword isfile: is the last component in args a filename? (default is false)
        @rtype: string
        @return: the full path to the storage area
        """
        force_pagedir = kw.get('force_pagedir', 'auto')
        check_create = kw.get('check_create', 1)
        qpagename = wikiutil.quoteWikinameFS(self.page_name)
        data_dir = self.cfg.data_dir
        # underlay is used to store system and help pages in a separate place
        underlay_dir = self.cfg.data_underlay_dir
        if underlay_dir:
            underlaypath = os.path.join(underlay_dir, "pages", qpagename)
        else:
            force_pagedir = 'standard'
        
        # self is a NORMAL page
        if not self is self.request.rootpage:
            kw['check_create'] = 0 # we don't want to create empty page dirs:
            path = self.request.rootpage.getPagePath("pages", qpagename, **kw)
            if force_pagedir == 'auto': 
                pagefile, rev, exists = self.get_rev(path)
                if not exists:
                    pagefile, rev, exists = self.get_rev(underlaypath)
                    if exists:                         
                        path = underlaypath
            elif force_pagedir == 'underlay':
                path = underlaypath
            # no need to check 'standard' case, we just use path in that case!
        
        # self is rootpage
        else:
            # our current rootpage is not a toplevel, but under another page
            if self.page_name:
                # this assumes flat storage of pages and sub pages on same level
                path = os.path.join(data_dir, "pages", qpagename)
                if force_pagedir == 'auto':
                    pagefile, rev, exists = self.get_rev(path)
                    if not exists:
                        pagefile, rev, exists = self.get_rev(underlaypath)
                        if exists:                         
                            path = underlaypath
                elif force_pagedir == 'underlay':
                    path = underlaypath
                # no need to check 'standard' case, we just use path in that case!
            
            # our current rootpage is THE virtual rootpage, really at top of all
            else:
                # this is the location of the virtual root page
                path = data_dir
                # 'auto' doesn't make sense here. maybe not even 'underlay':
                if force_pagedir == 'underlay':
                    path = underlay_dir
                # no need to check 'standard' case, we just use path in that case!
                
        fullpath = os.path.join(*((path,) + args))
        
        if check_create:
            if kw.get('isfile', 0):
                dirname, filename = os.path.split(fullpath)
            else:
                dirname = fullpath
            if not os.path.exists(dirname):
                filesys.makeDirs(dirname)
        
        return fullpath

    def _text_filename(self, **kw):
        """
        The name of the page file, possibly of an older page.
        
        @keyword rev: page revision, overriding self.rev
        @rtype: string
        @return: complete filename (including path) to this page
        """
        if hasattr(self, '_text_filename_force'):
            return self._text_filename_force
        rev = kw.get('rev', 0)
        if not rev and self.rev:
            rev = self.rev
        fname, rev, exists = self.get_rev(None, rev)
        return fname

    def _tmp_filename(self):
        """
        The name of the temporary file used while saving.
        
        @rtype: string
        @return: temporary filename (complete path + filename)
        """
        rnd = random.randint(0,1000000000)
        tmpname = os.path.join(self.cfg.data_dir, ('#%s.%d#' % (wikiutil.quoteWikinameFS(self.page_name), rnd)))
        return tmpname

    # XXX TODO clean up the mess, rewrite _last_edited, last_edit, lastEditInfo for new logs,
    # XXX TODO do not use mtime() calls any more
    def _last_edited(self, request):
        from MoinMoin.logfile import editlog
        try:
            logfile = editlog.EditLog(request, self.getPagePath('edit-log', check_create=0, isfile=1))
            logfile.to_end()
            log = logfile.previous()
        except StopIteration:
            log = None
        return log

    def last_edit(self, request):
        """
        Return the last edit.
        This is used by wikirpc(2).py.
        
        @param request: the request object
        @rtype: dict
        @return: timestamp and editor information
        """
        if not self.exists():
            return None

        result = None
        if not self.rev:
            log = self._last_edited(request)
            if log:
                editordata = log.getEditorData(request)
                editor = editordata[1]
                if editordata[0] == 'homepage':
                    editor = editordata[1].page_name
                result = {
                    'timestamp': log.ed_time_usecs,
                    'editor': editor,
                }
                del log
        if not result:
            version = self.mtime_usecs()
            result = {
                'timestamp': version,
                'editor': '?',
            }

        return result

    def lastEditInfo(self, request=None):
        """ Return the last edit info.
        
        @param request: the request object
        @rtype: dict
        @return: timestamp and editor information
        """
        if not self.exists():
            return {}
        if request is None:
            request = self.request

        # Try to get data from log
        log = self._last_edited(request)
        if log:
            editor = log.getEditor(request)
            time = wikiutil.version2timestamp(log.ed_time_usecs)
            del log
        # Or from the file system
        else:
            editor = ''
            time = os.path.getmtime(self._text_filename())

        # Use user time format
        time = request.user.getFormattedDateTime(time)
        return {'editor': editor, 'time': time}

    def isWritable(self):
        """ Can this page be changed?
        
        @rtype: bool
        @return: true, if this page is writable or does not exist
        """
        return os.access(self._text_filename(), os.W_OK) or not self.exists()

    def isUnderlayPage(self, includeDeleted=True):
        """ Does this page live in the underlay dir?

        Return true even if the data dir has a copy of this page. To
        check for underlay only page, use ifUnderlayPage() and not
        isStandardPage()

        @param includeDeleted: include deleted pages
        @rtype: bool
        @return: true if page lives in the underlay dir
        """
        return self.exists(domain='underlay', includeDeleted=includeDeleted)

    def isStandardPage(self, includeDeleted=True):
        """ Does this page live in the data dir?

        Return true even if this is a copy of an underlay page. To check
        for data only page, use isStandardPage() and not isUnderlayPage().

        @param includeDeleted: include deleted pages
        @rtype: bool
        @return: true if page lives in the data dir
        """
        return self.exists(domain='standard', includeDeleted=includeDeleted)
                
    def exists(self, rev=0, domain=None, includeDeleted=False):
        """ Does this page exist?

        This is the lower level method for checking page existence. Use
        the higher level methods isUnderlayPagea and isStandardPage for
        cleaner code.
        
        @param rev: revision to look for. Default check current
        @param domain: where to look for the page. Default look in all,
            available values: 'underlay', 'standard'
        @param includeDeleted: ignore page state, just check its pagedir
        @rtype: bool
        @return: true, if page exists
        """
        # Edge cases
        if domain == 'underlay' and not self.request.cfg.data_underlay_dir:
            return False

        if includeDeleted:
            # Look for page directory, ignore page state
            if domain is None:
                domains = ['underlay', 'standard']
            else:
                domains = [domain]
            for domain in domains:
                pagedir = self.getPagePath(force_pagedir=domain, check_create=0)
                if os.path.exists(pagedir):
                    return True
            return False
        else:
            # Look for non-deleted pages only, using get_rev
            if not rev and self.rev:
                rev = self.rev
            if domain is not None:
                domain = self.getPagePath(force_pagedir=domain, check_create=0)
            d, d, exists = self.get_rev(domain, rev)
            return exists

    def size(self, rev=0):
        """ Get Page size.
        
        @rtype: int
        @return: page size, 0 for non-existent pages.
        """
        if rev == self.rev: # same revision as self
            if self._raw_body is not None:
                return len(self._raw_body)

        try:
            return os.path.getsize(self._text_filename(rev=rev))
        except EnvironmentError, e:
            import errno
            if e.errno == errno.ENOENT: return 0
            raise
             
    def mtime_usecs(self):
        """
        Get modification timestamp of this page.
        
        @rtype: int
        @return: mtime of page (or 0 if page does not exist)
        """

        from MoinMoin.logfile import editlog

        mtime = 0

        current_wanted = (self.rev == 0) # True if we search for the current revision
        wanted_rev = "%08d" % self.rev

        try:
            logfile = editlog.EditLog(self.request, rootpagename=self.page_name)
            for line in logfile.reverse():
                if (current_wanted and line.rev != 99999999) or line.rev == wanted_rev:
                    mtime = line.ed_time_usecs
                    break
        except StopIteration:
            logfile = None

        return mtime

    def mtime_printable(self, request):
        """
        Get printable modification timestamp of this page.
        
        @rtype: string
        @return: formatted string with mtime of page
        """
        t = self.mtime_usecs()
        if not t:
            result = "0" # TODO: i18n, "Ever", "Beginning of time"...?
        else:
            result = request.user.getFormattedDateTime(wikiutil.version2timestamp(t))
        return result

    def getPageList(self, user=None, rootpagename=None):
        ''' List user readable pages under rootpage

        The default behavior is listing all the pages readable by the
        current user. If you want to get a page list for another user,
        specify the user name.

        If you want to get the full page list, without user filtering,
        call with user="". Use this only if really needed, and do not
        display pages the user can not read.

        Filter those annoying /MoinEditorBackup pages.
        
        @param user: the user requesting the pages
        @param rootpage: we get the page list of rootpage/pages, and default
                         to data_dir/pages
        @rtype: list of unicode
        @return: user readable wiki page names
        '''
        # Check input
        if user is None:
            user = self.request.user           
        if rootpagename is not None:
            rootpage = Page(self.request, rootpagename)
        else:
            rootpage = self.request.rootpage
            
        # Get pages in pages directory
        dir = rootpage.getPagePath('pages')
        pages = self.listPages(dir, user)
        
        # Merge with underlay pages
        underlay_dir = self.cfg.data_underlay_dir
        if underlay_dir is not None:
            dir = os.path.join(underlay_dir, 'pages')
            underlay = self.listPages(dir, user)
            pages.update(underlay)
                    
        return pages.keys()

    def getPageDict(self, user=None, rootpagename=None):
        """
        Return a dictionary of page objects for all pages,
        with the page name as the key.

        Invoke getPageList then create a dict from the page list. See
        getPageList docstring for more details.
                
        @param user: the user requesting the pages
        @rtype: dict {unicode: Page}
        @return: user readable pages
        """
        pages = {}
        for name in self.getPageList(user, rootpagename):
            pages[name] = Page(self.request, name)
        return pages

    def getlines(self):
        lines = self.get_raw_body().split('\n')
        return lines
    
    def get_raw_body(self):
        """
        Load the raw markup from the page file.
        
        @rtype: string
        @return: raw page contents of this page
        """
        if self._raw_body is None:
            # try to open file
            try:
                file = codecs.open(self._text_filename(), 'rb', config.charset)
            except IOError, er:
                import errno
                if er.errno == errno.ENOENT:
                    # just doesn't exist, return empty text (note that we
                    # never store empty pages, so this is detectable and also
                    # safe when passed to a function expecting a string)
                    return ""
                else:
                    raise er

            # read file content and make sure it is closed properly
            try:
                text = file.read()
                text = self.decodeTextMimeType(text)
                self.set_raw_body(text)
            finally:
                file.close()

        return self._raw_body

    def set_raw_body(self, body, modified=0):
        """ Set the raw body text (prevents loading from disk).

        TODO: this should not be a public function, as Page is immutable.

        @param body: raw body text
        @param modified: 1 means that we internally modified the raw text and
                         that it is not in sync with the page file on disk.
                         This is used e.g. by PageEditor when previewing the page.
        """
        self._raw_body = body
        self._raw_body_modified = modified

    def url(self, request, querystr=None, escape=1):
        """ Return complete URL for this page, including scriptname

        @param request: the request object
        @param querystr: the query string to add after a "?" after the url
            (str or dict, see util.web.makeQueryString)
        @param escpae: escape url for html, to be backward compatible
            with old code (bool)
        @rtype: str
        @return: complete url of this page, including scriptname
        """
        url = '%s/%s' % (request.getScriptname(),
                     wikiutil.quoteWikinameURL(self.page_name))
        
        if querystr:
            querystr = web.makeQueryString(querystr)

            # TODO: remove in 1.4
            # Escape query string to be compatible with old 3rd party code
            # New code should call with escape=0 to prevent the warning.
            if escape:
                import warnings
                warnings.warn("In moin 1.4 query string in url will not be escaped."
                              " See http://moinmoin.wikiwikiweb.de/ApiChanges")
                querystr = wikiutil.escape(querystr)          

            url = '%s?%s' % (url, querystr)

        return url
        
    def link_to(self, request, text=None, querystr=None, anchor=None, **kw):
        """
        Return HTML markup that links to this page.
        See wikiutil.link_tag() for possible keyword parameters.

        @param request: the request object
        @param text: inner text of the link - it gets automatically escaped
        @param querystr: the query string to add after a "?" after the url
        @param anchor: if specified, make a link to this anchor
        @keyword on: opening/closing tag only
        @keyword attachment_indicator: if 1, add attachment indicator after link tag
        @keyword css_class: css class to use
        @rtype: string
        @return: formatted link
        """
        if not text:
            text = self.split_title(request)

        # Create url, excluding scriptname
        url = wikiutil.quoteWikinameURL(self.page_name)
        if querystr:
            querystr = web.makeQueryString(querystr)
            # makeQueryString does not escape any more
            querystr = wikiutil.escape(querystr)
            url = "%s?%s" % (url, querystr)

        # Add anchor
        if anchor:
            url = "%s#%s" % (url, urllib.quote_plus(anchor.encode(config.charset)))

        # Add css class for non exisiting page
        if not self.exists():
            kw['css_class'] = 'nonexistent'

        link = wikiutil.link_tag(request, url, wikiutil.escape(text),
                                 formatter=getattr(self, 'formatter', None), **kw)

        # Create a link to attachments if any exist
        if kw.get('attachment_indicator', 0):
            from MoinMoin.action import AttachFile
            link += AttachFile.getIndicator(request, self.page_name)           

        return link

    def getSubscribers(self, request, **kw):
        """
        Get all subscribers of this page.

        @param request: the request object
        @keyword include_self: if 1, include current user (default: 0)
        @keyword return_users: if 1, return user instances (default: 0)
        @keyword trivial: if 1, only include users who want trivial changes (default: 0)
        @rtype: dict
        @return: lists of subscribed email addresses in a dict by language key
        """
        include_self = kw.get('include_self', 0)
        return_users = kw.get('return_users', 0)
        trivial = kw.get('trivial', 0)

        # extract categories of this page
        pageList = self.getCategories(request)
        
        # add current page name for list matching
        pageList.append(self.page_name)

        if self.cfg.SecurityPolicy:
            UserPerms = self.cfg.SecurityPolicy
        else:
            from security import Default as UserPerms

        # get email addresses of the all wiki user which have a profile stored;
        # add the address only if the user has subscribed to the page and
        # the user is not the current editor
        # Also, if the change is trivial (send email isn't ticked) only send email to users
        # who want_trivial changes (typically Admins on public sites)
        userlist = user.getUserList(request)
        subscriber_list = {}
        for uid in userlist:
            if uid == request.user.id and not include_self: continue # no self notification
            subscriber = user.User(request, uid)

            # This is a bit wrong if return_users=1 (which implies that the caller will process
            # user attributes and may, for example choose to send an SMS)
            # So it _should_ be "not (subscriber.email and return_users)" but that breaks at the moment.
            if not subscriber.email: continue # skip empty email addresses
            if trivial and not subscriber.want_trivial: continue # skip uninterested subscribers

            if not UserPerms(subscriber).read(self.page_name): continue

            if subscriber.isSubscribedTo(pageList):
                lang = subscriber.language or 'en'
                if not subscriber_list.has_key(lang): subscriber_list[lang] = []
                if return_users:
                    subscriber_list[lang].append(subscriber)
                else:
                    subscriber_list[lang].append(subscriber.email)

        return subscriber_list
  

    def send_page(self, request, msg=None, **keywords):
        """
        Output the formatted page.

        @param request: the request object
        @param msg: if given, display message in header area
        @keyword content_only: if 1, omit page header and footer
        @keyword content_id: set the id of the enclosing div
        @keyword count_hit: if 1, add an event to the log
        """
        from MoinMoin import i18n
        request.clock.start('send_page')
        _ = request.getText

        # determine modes
        print_mode = request.form.has_key('action') and request.form['action'][0] == 'print'
        if print_mode:
            media = request.form.has_key('media') and request.form['media'][0] or 'print'
        else:
            media = 'screen'
        content_only = keywords.get('content_only', 0)
        content_id = keywords.get('content_id', 'content')
        do_cache = keywords.get('do_cache', 1)
        if request.form.has_key('highlight'):
            self.hilite_re = request.form['highlight'][0]
        else:
            self.hilite_re = None
        if msg is None: msg = ""

        # count hit?
        if keywords.get('count_hit', 0):
            eventlog.EventLog(request).add(request, 'VIEWPAGE', {'pagename': self.page_name})

        # load the text
        body = self.get_raw_body()

        # if necessary, load the default formatter
        if self.default_formatter:
            from MoinMoin.formatter.text_html import Formatter
            self.formatter = Formatter(request, store_pagelinks=1)
        self.formatter.setPage(self)
        if self.hilite_re: self.formatter.set_highlight_re(self.hilite_re)
        request.formatter = self.formatter
        
        # default is wiki markup
        pi_format = self.cfg.default_markup or "wiki"
        pi_formatargs = ''
        pi_redirect = None
        pi_refresh = None
        pi_formtext = []
        pi_formfields = []
        wikiform = None

        # check for XML content
        if body and body[:5] == '<?xml':
            pi_format = "xslt"

        # check processing instructions
        while body and body[0] == '#':
            # extract first line
            try:
                line, body = body.split('\n', 1)
            except ValueError:
                line = body
                body = ''

            # end parsing on empty (invalid) PI
            if line == "#":
                body = line + '\n' + body
                break

            # skip comments (lines with two hash marks)
            if line[1] == '#': continue

            # parse the PI
            verb, args = (line[1:]+' ').split(' ', 1)
            verb = verb.lower()
            args = args.strip()

            # check the PIs
            if verb == "format":
                # markup format
                pi_format, pi_formatargs = (args+' ').split(' ',1)
                pi_format = pi_format.lower()
                pi_formatargs = pi_formatargs.strip()
            elif verb == "refresh":
                if self.cfg.refresh:
                    try:
                        mindelay, targetallowed = self.cfg.refresh
                        args = args.split()
                        if len(args) >= 1:
                            delay = max(int(args[0]), mindelay)
                        if len(args) >= 2:
                            target = args[1]
                        else:
                            target = self.page_name
                        if target.find('://') >= 0:
                            if targetallowed == 'internal':
                                raise ValueError
                            elif targetallowed == 'external':
                                url = target
                        else:
                            url = Page(request, target).url(request)
                        pi_refresh = {'delay': delay, 'url': url, }
                    except (ValueError,):
                        pi_refresh = None
            elif verb == "redirect":
                # redirect to another page
                # note that by including "action=show", we prevent
                # endless looping (see code in "request") or any
                # cascaded redirection
                pi_redirect = args
                if request.form.has_key('action') or request.form.has_key('redirect') or content_only: continue

                request.http_redirect('%s/%s?action=show&redirect=%s' % (
                    request.getScriptname(),
                    wikiutil.quoteWikinameURL(pi_redirect),
                    urllib.quote_plus(self.page_name.encode(config.charset), ''),))
                return
            elif verb == "deprecated":
                # deprecated page, append last backup version to current contents
                # (which should be a short reason why the page is deprecated)
                msg = '%s<strong>%s</strong><br>%s' % (
                    self.formatter.smiley('/!\\'),
                    _('The backupped content of this page is deprecated and will not be included in search results!'),
                    msg)

                revisions = self.getRevList()
                if len(revisions) >= 2: # XXX shouldn't that be ever the case!? Looks like not.
                    oldpage = Page(request, self.page_name, date=revisions[1])
                    body += oldpage.get_raw_body()
                    del oldpage
            elif verb == "pragma":
                # store a list of name/value pairs for general use
                try:
                    key, val = args.split(' ', 1)
                except (ValueError, TypeError):
                    pass
                else:
                    request.setPragma(key, val)
            elif verb == "form":
                # ignore form PIs on non-form pages
                if not wikiutil.isFormPage(request, self.page_name):
                    continue

                # collect form definitions
                if not wikiform:
                    from MoinMoin import wikiform
                    # TODO: form probably can work with action=""
                    pi_formtext.append('<table border="1" cellspacing="1" cellpadding="3">\n'
                        '<form method="POST" action="%s">\n'
                        '<input type="hidden" name="action" value="formtest">\n' % self.url(request))
                pi_formtext.append(wikiform.parseDefinition(request, args, pi_formfields))
            elif verb == "acl":
                # We could build it here, but there's no request.
                pass
            elif verb == "language":
                # Page language. Check if args is a known moin language
                if args in i18n.wikiLanguages():
                    self.language = args
                    request.setContentLanguage(self.language)
            else:
                # unknown PI ==> end PI parsing, and show invalid PI as text
                body = line + '\n' + body
                break

        # Save values for later use
        self.pi_format = pi_format

        # start document output
        doc_leader = self.formatter.startDocument(self.page_name)
        if not content_only:
            # send the document leader
            request.http_headers()
            request.write(doc_leader)

            # send the page header
            if self.default_formatter:

                def quote_whitespace(x):
                    if x.find(" ")!=-1:
                        return "'%s'" % x
                    else:
                        return x
                page_needle = quote_whitespace(self.page_name)
                if config.allow_subpages and page_needle.count('/'):
                    #parts = page_needle.split('/')
                    #for level in range(1, len(parts)):
                    #    page_needle += (" !" + quote_whitespace(
                    #        "/".join(parts[:level])) + " " +
                    #                    quote_whitespace(
                    #        "/" + "/".join(parts[level:])))   
                    page_needle = '/' + page_needle.split('/')[-1]
                    
                link = '%s/%s?action=fullsearch&amp;value=%s&amp;literal=1&amp;case=1&amp;context=40' % (
                    request.getScriptname(),
                    wikiutil.quoteWikinameURL(self.page_name),
                    urllib.quote_plus(page_needle.encode(config.charset), ''))
                title = self.split_title(request)
                if self.rev:
                    msg = "<strong>%s</strong><br>%s" % (
                        _('Revision %(rev)d as of %(date)s') % {
                            'rev': self.rev,
                            'date': self.mtime_printable(request)
                        }, msg)
                
                # This redirect message is very annoying.
                # Less annoying now without the warning sign.
                if request.form.has_key('redirect'):
                    redir = request.form['redirect'][0]
                    msg = '<strong>%s</strong><br>%s' % (
                        _('Redirected from page "%(page)s"') % {'page':
                            wikiutil.link_tag(request, wikiutil.quoteWikinameURL(redir) + "?action=show", redir)},
                        msg)
                if pi_redirect:
                    msg = '<strong>%s</strong><br>%s' % (
                        _('This page redirects to page "%(page)s"') % {'page': pi_redirect},
                        msg)

                
                # Page trail
                trail = None
                if not print_mode and request.user.valid and request.user.show_page_trail:
                    request.user.addTrail(self.page_name)
                    trail = request.user.getTrail()
                
                wikiutil.send_title(request, title,  page=self, link=link, msg=msg,
                                    pagename=self.page_name, print_mode=print_mode,
                                    media=media, pi_refresh=pi_refresh,
                                    allow_doubleclick=1, trail=trail,
                                    )

                # user-defined form preview?
                # Todo: check if this is also an RTL form - then add ui_lang_attr
                if pi_formtext:
                    pi_formtext.append('<input type="hidden" name="fieldlist" value="%s">\n' %
                        "|".join(pi_formfields))
                    pi_formtext.append('</form></table>\n')
                    pi_formtext.append(_(
                        '~-If you submit this form, the submitted values'
                        ' will be displayed.\nTo use this form on other pages, insert a\n'
                        '[[BR]][[BR]]\'\'\'{{{    [[Form("%(pagename)s")]]}}}\'\'\'[[BR]][[BR]]\n'
                        'macro call.-~\n'
                    ) % {'pagename': self.page_name})
                    request.write(''.join(pi_formtext))

        # try to load the parser
        Parser = wikiutil.importPlugin("parser", self.pi_format, "Parser",
                                       self.cfg.data_dir)
        if Parser is None:
            # default to plain text formatter (i.e. show the page source)
            del Parser
            from parser.plain import Parser
        
        # start wiki content div
        request.write(self.formatter.startContent(content_id))
        
        # new page?
        if not self.exists() and self.default_formatter and not content_only:
            self._emptyPageText(request)
        elif not request.user.may.read(self.page_name):
            request.write("<strong>%s</strong><br>" % _("You are not allowed to view this page."))
        else:
            # parse the text and send the page content
            self.send_page_content(request, Parser, body, format_args=pi_formatargs, do_cache=do_cache)

            # check for pending footnotes
            if getattr(request, 'footnotes', None):
                from MoinMoin.macro.FootNote import emit_footnotes
                request.write(emit_footnotes(request, self.formatter))

        # end wiki content div
        request.write(self.formatter.endContent())
        
        # end document output
        doc_trailer = self.formatter.endDocument()
        if not content_only:
            # send the page footer
            if self.default_formatter:
                wikiutil.send_footer(request, self.page_name, print_mode=print_mode)

            request.write(doc_trailer)
        
        # cache the pagelinks
        if do_cache and self.default_formatter and self.exists():
            arena = self
            key = 'pagelinks'
            cache = caching.CacheEntry(request, arena, key)
            if cache.needsUpdate(self._text_filename()):
                links = self.formatter.pagelinks
                links.sort()
                cache.update('\n'.join(links), True)

        request.clock.stop('send_page')

    def getFormatterName(self):
        """ Return a formatter name, used in the caching system

        @rtype: string
        @return: formatter name as used in caching
        """
        if not hasattr(self, 'formatter'):
            return ''
        
        name = str(self.formatter.__class__)
        name = name.replace('MoinMoin.formatter.', '').replace('.Formatter', '')
        return name

    def canUseCache(self, parser=None):
        """ Is caching available for this request?

        This make sure we can try to use the caching system for this
        request, but it does not make sure that this will
        succeed. Themes can use this to decide if a Refresh action
        should be displayed.

        @param parser: the parser used to render the page
        @rtype: bool
        @return: if this page can use caching
        """
        if (not self.rev and
            not self.hilite_re and
            not self._raw_body_modified and
            self.getFormatterName() in self.cfg.caching_formats):
            # Everything is fine, now check the parser:
            if not parser:
                parser = wikiutil.importPlugin("parser", self.pi_format, "Parser",
                                               self.cfg.data_dir)
            return getattr(parser, 'caching', False)

        return False

    def send_page_content(self, request, Parser, body, needsupdate=0,
                          format_args='', do_cache=1):
        # XXX CFG remove request param? self.request ?
        """
        Output the formatted wiki page, using caching, if possible.

        @param request: the request object
        @param Parser: the Parser
        @param body: text of the wiki page
        @param needsupdate: if 1, force update of the cached compiled page
        """
        formatter_name = self.getFormatterName()

        # if we should not or can not use caching
        if not (do_cache and self.canUseCache(Parser)):
            # parse the text and send the page content
            Parser(body, request, format_args=format_args).format(self.formatter)
            return

        #try cache
        _ = request.getText
        from MoinMoin import wikimacro
        arena = self
        key = formatter_name
        cache = caching.CacheEntry(request, arena, key)
        code = None

        if cache.needsUpdate(self._text_filename(), self.getPagePath('attachments', check_create=0)):
            needsupdate = 1

        # load cache
        if not needsupdate:
            try:
                import marshal
                code = marshal.loads(cache.content())
            except: #bad marshal data, catch ANY exception
                needsupdate = 1

        # render page
        if needsupdate:
            from MoinMoin.formatter.text_python import Formatter
            formatter = Formatter(request, ["page"], self.formatter)

            import marshal
            buffer = StringIO.StringIO()
            request.redirect(buffer)
            parser = Parser(body, request)
            parser.format(formatter)
            request.redirect()
            text = buffer.getvalue()
            buffer.close()
            src = formatter.assemble_code(text)
            ##request.write(src) # debug 
            code = compile(src.encode(config.charset),
                           self.page_name.encode(config.charset), 'exec')
            cache.update(marshal.dumps(code))
            
        # send page
        formatter = self.formatter
        parser = Parser(body, request)
        macro_obj = wikimacro.Macro(parser)

        try:
            exec code
        except 'CacheNeedsUpdate': # if something goes wrong, try without caching
           self.send_page_content(request, Parser, body, needsupdate=1)
           cache = caching.CacheEntry(request, arena, key)
            
        # Save my cache modification time, this info might be used by
        # themes - but only after the page content was sent.
        self.cache_mtime = cache.mtime()

        # TODO: move this into theme (currently used only by classic)
        qpage = wikiutil.quoteWikinameURL(self.page_name)
        url = "%s?action=refresh&amp;arena=Page.py&amp;key=%s" % (qpage, key)        
        link = wikiutil.link_tag(request, url, _("RefreshCache", formatted=False))
        date = self.request.user.getFormattedDateTime(cache.mtime())
        fragment = link + ' ' +  _('(cached %s)') % date
        self.request.add2footer('RefreshCache', fragment)

    def _emptyPageText(self, request):
        """
        Output the default page content for new pages.
 
        @param request: the request object
        """
        missingpage = wikiutil.getSysPage(request, 'MissingPage')
        missingpagefn = missingpage._text_filename()
        missingpage.page_name = self.page_name
        missingpage._text_filename_force = missingpagefn
        missingpage.send_page(request, content_only=1, do_cache=0)


    def getRevList(self):
        """
        Get a page revision list of this page, including the current version,
        sorted by revision number in descending order (current page first).

        @rtype: list of ints
        @return: page revisions
        """
        revisions = []
        if self.page_name:
            rev_dir = self.getPagePath('revisions', check_create=0)
            if os.path.isdir(rev_dir):
                for rev in os.listdir(rev_dir):
                    try:
                        revint = int(rev)
                        revisions.append(revint)
                    except ValueError:
                        pass
                revisions.sort()
                revisions.reverse()
        return revisions


    def olderrevision(self, rev=0):
        """
        Get revision of the next older page revision than rev.
        rev == 0 means this page objects revision (that may be an old
        revision already!)
        """
        if rev == 0:
            rev = self.rev
        revisions = self.getRevList()
        d = None
        for r in revisions:
            if r < rev:
                older = r
                break
        return older

    def getPageText(self, start=0, length=None):
        """ Convenience function to get the page text, skipping the header

        @rtype: unicode
        @return: page text, excluding the header
        """
        body = self.get_raw_body() or ''
        header = header_re.search(body)
        if header:
            start += header.end()

        # Return length characters from start of text
        if length is None:
            return body[start:]
        else:
            return body[start:start + length]

    def getPageHeader(self, start=0, length=None):
        """ Convenience function to get the page header

        @rtype: unicode
        @return: page header
        """
        body = self.get_raw_body() or ''
        header = header_re.search(body)
        if header:
            text = header.group()           
            # Return length characters from start of text
            if length is None:
                return text[start:]
            else:
                return text[start:start + length]
        return ''

    def getPageLinks(self, request):
        """
        Get a list of the links on this page.
        
        @param request: the request object
        @rtype: list
        @return: page names this page links to
        """
        if not self.exists(): return []

        arena = self
        key = 'pagelinks'
        cache = caching.CacheEntry(request, arena, key)
        if cache.needsUpdate(self._text_filename()):
            # this is normally never called, but is here to fill the cache
            # in existing wikis; thus, we do a "null" send_page here, which
            # is not efficient, but reduces code duplication
            # !!! it is also an evil hack, and needs to be removed
            # !!! by refactoring Page to separate body parsing & send_page
            request.redirect(StringIO.StringIO())
            try:
                try:
                    request.mode_getpagelinks = 1
                    Page(request, self.page_name).send_page(request, content_only=1)
                except:
                    import traceback
                    traceback.print_exc()
                    cache.update('')
            finally:
                request.mode_getpagelinks = 0
                request.redirect()
                if hasattr(request, '_fmt_hd_counters'):
                    del request._fmt_hd_counters
        return filter(None, cache.content(True).split('\n'))


    def getCategories(self, request):
        """
        Get categories this page belongs to.

        @param request: the request object
        @rtype: list
        @return: categories this page belongs to
        """
        return wikiutil.filterCategoryPages(request, self.getPageLinks(request))

    def getParentPage(self):
        """ Return parent page or None

        @rtype: Page
        @return: parent page or None
        """
        if config.allow_subpages and self.page_name:
            pos = self.page_name.rfind('/')
            if pos > 0:
                parent = Page(self.request, self.page_name[:pos])
                if parent.exists():
                    return parent
        return None

    def getACL(self, request):
        """
        Get ACLs of this page.

        @param request: the request object
        @rtype: dict
        @return: ACLs of this page
        """
        if not self.cfg.acl_enabled:
            import wikiacl
            return wikiacl.AccessControlList(request)
        # mtime check for forked long running processes
        fn = self._text_filename()
        acl = None
        if os.path.exists(fn):
            mtime = os.path.getmtime(fn)
        else:
            mtime = 0
        key = (request.cfg.siteid, self.page_name)
        global _acl_cache
        if _acl_cache.has_key(key):
            (omtime, acl) = _acl_cache[key]
            if omtime < mtime:
                acl = None
        if acl is None:
            import wikiacl
            body = ''
            if self.exists():
                body = self.get_raw_body()
            else:
                # if the page isn't there any more, use the ACLs of the last backup
                revisions = self.getRevList()
                if len(revisions) > 1:
                    oldpage = Page(request, self.page_name, date=revisions[1])
                    body = oldpage.get_raw_body()
            acl = wikiacl.parseACL(request, body)
            _acl_cache[key] = (mtime, acl)
        return acl

    def clean_acl_cache(self):
        """
        Clean ACL cache entry of this page (used by PageEditor on save)
        """
        key = (self.cfg.siteid, self.page_name)
        global _acl_cache
        if _acl_cache.has_key(key):
            del _acl_cache[key]

    # Helpers ----------------------------------------------------------

    def listPages(self, dir, user):
        """ List page names in dir 
        
        Return a dict and not a list, so its easy to merge different page list 
        efficiently.        
        TODO: when we require Python 2.3.4, use a set instead of a dict.
        
        To not filter pages by user.may.read, call with user=''
        
        Filter those annoying /MoinEditorBackup pages.
        
        @param dir: directory to list
        @param user: user we prepare the page list for
        @rtyp: dictionary {pagename: 1, ...}
        @return: dictionary of page names
        """
        import dircache
        pages = {}
        for name in dircache.listdir(dir):
            # Filter non-pages in quoted wiki names
            # List all pages in pages directory - assume flat namespace
            # Assume that all items in the pages directory are pages. If we
            # add non-pages, we should filter them here!
            if name.startswith('.') or name.startswith('#') or name == 'CVS':
                continue
            
            # Filter deleted pages
            pagedir = os.path.join(dir, name)
            d, d, exists = self.get_rev(pagedir)
            if not exists:
                continue
            
            # Unquote - from this point name is Unicode
            name = wikiutil.unquoteWikiname(name)
            
            # Filter meta-pages like editor backups
            if name.endswith(u'/MoinEditorBackup'):
                continue           
            
            # Filter out page user may not read
            if user and not user.may.read(name):
                continue  
                         
            pages[name] = 1
        
        return pages

    # Text format -------------------------------------------------------

    def encodeTextMimeType(self, text):
        """ Encode text from moin internal representation to text/* mime type

        Make sure text uses CRLF line ends, keep trailing newline.
        
        @param text: text to encode (unicode)
        @rtype: unicode
        @return: encoded text
        """ 
        if text:
            lines = text.splitlines()
            # Keep traling newline
            if text.endswith(u'\n') and not lines[-1] == u'':
                lines.append(u'')
            text = u'\r\n'.join(lines)
        return text

    def decodeTextMimeType(self, text):
        """ Decode text from text/* mime type to moin internal representation

        @param text: text to decode (unicode). Text must use CRLF!
        @rtype: unicode
        @return: text using internal representation
        """ 
        text = text.replace(u'\r', u'')
        return text



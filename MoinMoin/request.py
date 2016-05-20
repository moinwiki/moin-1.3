# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Data associated with a single Request

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>
    @copyright: 2003-2004 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, time, sys, types, cgi
from MoinMoin import config, wikiutil, user, error
from MoinMoin.util import MoinMoinNoFooter, IsWin9x, FixScriptName

# this needs sitecustomize.py in python path to work!
# use our encoding as default encoding:
## sys.setappdefaultencoding(config.charset)
# this is the default python uses without this hack:
## sys.setappdefaultencoding("ascii")
# we could maybe use this to find places where implicit encodings are used:
## sys.setappdefaultencoding("undefined")

# Timing ---------------------------------------------------------------

class Clock:
    """ Helper class for code profiling
        we do not use time.clock() as this does not work across threads
    """

    def __init__(self):
        self.timings = {'total': time.time()}

    def start(self, timer):
        self.timings[timer] = time.time() - self.timings.get(timer, 0)

    def stop(self, timer):
        self.timings[timer] = time.time() - self.timings[timer]

    def value(self, timer):
        return "%.3f" % (self.timings[timer],)

    def dump(self):
        outlist = []
        for timing in self.timings.items():
            outlist.append("%s = %.3fs" % timing)
        outlist.sort()
        return outlist



# Request Base ----------------------------------------------------------

class RequestBase:
    """ A collection for all data associated with ONE request. """

    # Header set to force misbehaved proxies and browsers to keep their
    # hands off a page
    # Details: http://support.microsoft.com/support/kb/articles/Q234/0/67.ASP
    nocache = [
        "Pragma: no-cache",
        "Cache-Control: no-cache",
        "Expires: -1",
    ]

    def __init__(self, properties={}):
        self.failed = 0
        self._available_actions = None
        self._known_actions = None

        # Pages meta data that we collect in one request
        self.pages = {}
                    
        self.sent_headers = 0
        self.user_headers = []
        self.page = None

        # Fix dircaching problems on Windows 9x
        if IsWin9x():
            import dircache
            dircache.reset()

        # Check for dumb proxy requests
        # TODO relying on request_uri will not work on all servers, especially
        # not on external non-Apache servers
        self.forbidden = False
        if self.request_uri.startswith('http://'):
            self.makeForbidden()

        # Init
        else:
            self.writestack = []
            self.clock = Clock()
            # order is important here!
            self._load_multi_cfg()
            
            # Set decode charsets.  Input from the user is always in
            # config.charset, which is the page charsets. Except
            # path_info, which may use utf-8, and handled by decodePagename.
            self.decode_charsets = [config.charset]
            
            # hierarchical wiki - set rootpage
            from MoinMoin.Page import Page
            #path = self.getPathinfo()
            #if path.startswith('/'):
            #    pages = path[1:].split('/')
            #    if 0: # len(path) > 1:
            #        ## breaks MainPage/SubPage on flat storage
            #        rootname = u'/'.join(pages[:-1])
            #    else:
            #        # this is the usual case, as it ever was...
            #        rootname = u""
            #else:
            #    # no extra path after script name
            #    rootname = u""

            rootname = u''
            self.rootpage = Page(self, rootname, is_rootpage=1)

            self.user = user.User(self)
            ## self.dicts = self.initdicts()

            from MoinMoin import i18n

            # Set theme - forced theme, user theme or wiki default
            if self.cfg.theme_force:
                theme_name = self.cfg.theme_default
            else:
                theme_name = self.user.theme_name
            self.loadTheme(theme_name)
            
            self.args = None
            self.form = None
            self.logger = None
            self.pragma = {}
            self.mode_getpagelinks = 0
            self.no_closing_html_code = 0

            self.__dict__.update(properties)

            self.i18n = i18n
            self.lang = i18n.requestLanguage(self) 
            # Language for content. Page content should use the wiki
            # default lang, but generated content like search results
            # should use the user language.
            self.content_lang = self.cfg.default_lang
            self.getText = lambda text, i18n=self.i18n, request=self, lang=self.lang, **kv: i18n.getText(text, request, lang, kv.get('formatted', True))

            self.opened_logs = 0

            self.reset()
        
    def __getattr__(self, name):
        "load things on demand"
        if name == "dicts":
            self.dicts = self.initdicts()
            return self.dicts
        raise AttributeError

    def _load_multi_cfg(self):
        # protect against calling multiple times
        if not hasattr(self, 'cfg'):
            from MoinMoin import multiconfig
            self.cfg = multiconfig.getConfig(self.url)
            
    def parse_accept_charset(self, accept_charset):
        """ Parse http accept charset header

        Set self.accepted_charsets to an ordered list based on
        http_accept_charset. 
        
        Reference: http://www.w3.org/Protocols/rfc2616/rfc2616.txt

        @param accept_charset: HTTP_ACCEPT_CHARSET string
        @rtype: list of strings
        @return: sorted list of accepted charsets
        """        
        charsets = []
        if accept_charset:
            accept_charset = accept_charset.lower()
            # Add iso-8859-1 if needed
            if (not '*' in accept_charset and
                accept_charset.find('iso-8859-1') < 0):
                accept_charset += ',iso-8859-1'

            # Make a list, sorted by quality value, using Schwartzian Transform
            # Create list of tuples (value, name) , sort, extract names  
            for item in accept_charset.split(','):
                if ';' in item:
                    name, qval = item.split(';')
                    qval = 1.0 - float(qval.split('=')[1])
                else:
                    name, qval = item, 0
                charsets.append((qval, name))                 
            charsets.sort()
            # Remove *, its not clear what we should do with it later
            charsets = [name for qval, name in charsets if name != '*']

        return charsets
        
    def _setup_vars_from_std_env(self, env):
        """ Sets the common Request members by parsing a standard
            HTTPD environment (as created as environment by most common
            webservers. To be used by derived classes.

            @param env: the environment to use
        """
        self.http_accept_language = env.get('HTTP_ACCEPT_LANGUAGE', 'en')
        self.server_name = env.get('SERVER_NAME', 'localhost')
        self.server_port = env.get('SERVER_PORT', '80')
        self.http_host = env.get('HTTP_HOST','localhost')
        # Make sure http referer use only ascii (IE again)
        self.http_referer = unicode(env.get('HTTP_REFERER', ''), 'ascii',
                                    'replace').encode('ascii', 'replace')
        self.saved_cookie = env.get('HTTP_COOKIE', '')
        self.script_name = env.get('SCRIPT_NAME', '')

        self.request_uri = env.get('REQUEST_URI', '')
        path_info = env.get('PATH_INFO', '')

        query_string = env.get('QUERY_STRING', '')
        self.query_string = self.decodePagename(query_string)
        server_software = env.get('SERVER_SOFTWARE', '')

        # Handle the strange charset semantics on *Windows*
        # path_info is transformed into the system code page by the webserver
        # Additionally, paths containing dots let most webservers choke.

        #  Fig. I - Broken environment variables in different environments:
        #         path_info script_name
        # Apache1     X          X      PI does not contain dots
        # Apache2     X          X      PI is not encoded correctly
        # IIS         X          X (is fixed somewhere else)
        # Other       ?          -      ? := Possible and even RFC-compatible.
        #                               - := Hopefully not.
        
        # Fix the script_name if run on Windows/Apache
        if os.name == 'nt' and server_software.find('Apache/') != -1:
            self.script_name = FixScriptName(self.script_name)

        # Check if we can use Apache's request_uri variable in order to
        # gather the correct user input
        if (os.name != 'posix' and self.request_uri != ''):
            import urllib
            path_info = urllib.unquote(self.request_uri.replace(
                self.script_name, '', 1).replace('?' + query_string, '', 1))
        
        # Decode according to filesystem semantics if we cannot gather the
        # request_uri
        elif os.name == 'nt':
            path_info = wikiutil.decodeWindowsPath(path_info).encode("utf-8")

        self.path_info = self.decodePagename(path_info)
        self.request_method = env.get('REQUEST_METHOD', None)

        self.remote_addr = env.get('REMOTE_ADDR', '')
        self.http_user_agent = env.get('HTTP_USER_AGENT', '')
        self.is_ssl = env.get('SSL_PROTOCOL', '') != '' \
            or env.get('SSL_PROTOCOL_VERSION', '') != '' \
            or env.get('HTTPS', 'off') == 'on'

        # We cannot rely on request_uri being set. In fact,
        # it is just an addition of Apache to the CGI specs.
        if self.request_uri == '':
            import urllib
            if self.server_port.strip() and self.server_port != '80':
                port = ':' + str(self.server_port)
            else:
                port = ''
            self.url = (self.server_name + port + self.script_name +
                        urllib.quote(self.path_info.replace(
                            self.script_name, '', 1).encode("utf-8"))
                        + '?' + self.query_string)
        else:
            self.url = self.server_name + self.request_uri
        
        ac = env.get('HTTP_ACCEPT_CHARSET', '')
        self.accepted_charsets = self.parse_accept_charset(ac)
        
        self.auth_username = None

        # need config here, so check:
        self._load_multi_cfg()

        if self.cfg.auth_http_enabled:
            auth_type = env.get('AUTH_TYPE','')
            if auth_type in ['Basic', 'Digest', 'NTLM', ]:
                username = env.get('REMOTE_USER','')
                if auth_type == 'NTLM':
                    # converting to standard case so that the user can even enter wrong case
                    # (added since windows does not distinguish between e.g. "Mike" and "mike")
                    username = username.split('\\')[-1] # split off domain e.g. from DOMAIN\user
                    # this "normalizes" the login name from {meier, Meier, MEIER} to Meier
                    # put a comment sign in front of next line if you don't want that:
                    username = username.title()
                self.auth_username = username
                                    
##        f=open('/tmp/env.log','a')
##        f.write('---ENV\n')
##        f.write('script_name = %s\n'%(self.script_name))
##        f.write('path_info   = %s\n'%(self.path_info))
##        f.write('server_name = %s\n'%(self.server_name))
##        f.write('server_port = %s\n'%(self.server_port))
##        f.write('http_host   = %s\n'%(self.http_host))
##        f.write('------\n')
##        f.write('%s\n'%(repr(env)))
##        f.write('------\n')
##        f.close()
  
    def reset(self):
        """ Reset request state.

        Called after saving a page, before serving the updated
        page. Solves some practical problems with request state
        modified during saving.

        """
        # This is the content language and has nothing to do with
        # The user interface language. The content language can change
        # during the rendering of a page by lang macros
        self.current_lang = self.cfg.default_lang

        self._footer_fragments = {}
        self._all_pages = None
        # caches unique ids
        self._page_ids = {}
        # keeps track of pagename/heading combinations
        # parsers should use this dict and not a local one, so that
        # macros like TableOfContents in combination with Include
        # can work
        self._page_headings = {}

        if hasattr(self, "_fmt_hd_counters"):
            del self._fmt_hd_counters

    def loadTheme(self, theme_name):
        """ Load the Theme to use for this request.

        @param theme_name: the name of the theme
        @type theme_name: str
        @returns: 0 on success, 1 if user theme could not be loaded,
                  2 if a hard fallback to modern theme was required.
        @rtype: int
        @return: success code
        """
        fallback = 0
        Theme = wikiutil.importPlugin(self.cfg, 'theme', theme_name, 'Theme')
        if Theme is None:
            fallback = 1
            Theme = wikiutil.importPlugin(self.cfg, 'theme',
                                          self.cfg.theme_default, 'Theme')
            if Theme is None:
                fallback = 2
                from MoinMoin.theme.modern import Theme
        self.theme = Theme(self)

        return fallback

    def setContentLanguage(self, lang):
        """ Set the content language, used for the content div

        Actions that generate content in the user language, like search,
        should set the content direction to the user language before they
        call send_title!
        """
        self.content_lang = lang
        self.current_lang = lang

    def add2footer(self, key, htmlcode):
        """ Add a named HTML fragment to the footer, after the default links
        """
        self._footer_fragments[key] = htmlcode


    def getPragma(self, key, defval=None):
        """ Query a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        return self.pragma.get(key.lower(), defval)


    def setPragma(self, key, value):
        """ Set a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        self.pragma[key.lower()] = value

    def getPathinfo(self):
        """ Return the remaining part of the URL. """
        return self.path_info

    def getScriptname(self):
        """ Return the scriptname part of the URL ('/path/to/my.cgi'). """
        if self.script_name == '/':
            return ''
        return self.script_name

    def getKnownActions(self):
        """ Create a dict of avaiable actions

        Return cached version if avaiable. TODO: when we have a wiki
        object in long running process, we should get it from it.
       
        @rtype: dict
        @return: dict of all known actions
        """
        if self._known_actions is None:
            from MoinMoin import wikiaction
            # Add built in  actions from wikiaction
            actions = [name[3:] for name in wikiaction.__dict__
                       if name.startswith('do_')]

            # Add plugins           
            dummy, plugins = wikiaction.getPlugins(self)
            actions.extend(plugins)

            # Add extensions
            from MoinMoin.action import extension_actions
            actions.extend(extension_actions)           
           
            # TODO: Use set when we require Python 2.3
            actions = dict(zip(actions, [''] * len(actions)))            
            self._known_actions = actions

        # Return a copy, so clients will not change the dict.
        return self._known_actions.copy()        

    def getAvailableActions(self, page):
        """ Get list of avaiable actions for this request

        The dict does not contain actions that starts with lower
        case. Themes use this dict to display the actions to the user.

        @param page: current page, Page object
        @rtype: dict
        @return: dict of avaiable actions
        """
        if self._available_actions is None:
            # Add actions for existing pages only!, incliding deleted pages.
            # Fix *OnNonExistingPage bugs.
            if not (page.exists(includeDeleted=1) and
                    self.user.may.read(page.page_name)):
                return []

            # Filter non ui actions (starts with lower case letter)
            actions = self.getKnownActions()
            for key in actions.keys():
                if key[0].islower():
                    del actions[key]

            # Filter wiki excluded actions
            for key in self.cfg.excluded_actions:
                if key in actions:
                    del actions[key]                

            # Filter actions by page type, acl and user state
            excluded = []
            if ((page.isUnderlayPage() and not page.isStandardPage()) or
                not self.user.may.write(page.page_name)):
                # Prevent modification of underlay only pages, or pages
                # the user can't write to
                excluded = [u'RenamePage', u'DeletePage',] # AttachFile must NOT be here!
            elif not self.user.valid:
                # Prevent rename and delete for non registered users
                excluded = [u'RenamePage', u'DeletePage']
            for key in excluded:
                if key in actions:
                    del actions[key]                

            self._available_actions = actions

        # Return a copy, so clients will not change the dict.
        return self._available_actions.copy()
    
    def redirect(self, file=None):
        if file: # redirect output to "file"
            self.writestack.append(self.write)
            self.write = file.write
        else: # restore saved output file
            self.write = self.writestack.pop()

    def reset_output(self):
        """ restore default output method
            destroy output stack
            (useful for error messages)
        """
        if self.writestack:
            self.write = self.writestack[0]
            self.writestack = []

    def log(self, msg):
        """ Log to stderr, which may be error.log """
        msg = msg.strip()
        # Encode unicode msg
        if isinstance(msg, unicode):
            msg = msg.encode(config.charset)
        # Add time stamp
        msg = '[%s] %s\n' % (time.asctime(), msg)
        sys.stderr.write(msg)
    
    def write(self, *data):
        """ Write to output stream.
        """
        raise NotImplementedError

    def encode(self, data):
        """ encode data (can be both unicode strings and strings),
            preparing for a single write()
        """
        wd = []
        for d in data:
            try:
                if isinstance(d, type(u'')):
                    # if we are REALLY sure, we can use "strict"
                    d = d.encode(config.charset, 'replace') 
                wd.append(d)
            except UnicodeError:
                print >>sys.stderr, "Unicode error on: %s" % repr(d)
        return ''.join(wd)
    
    def decodePagename(self, name):
        """ Decode path, possibly using non ascii characters

        Does not change the name, only decode to Unicode.

        First split the path to pages, then decode each one. This enables
        us to decode one page using config.charset and another using
        utf-8. This situation happens when you try to add to a name of
        an existing page.

        See http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2.1
        
        @param name: page name, string
        @rtype: unicode
        @return decoded page name
        """
        # Split to pages and decode each one
        pages = name.split('/')
        decoded = []
        for page in pages:
            # Recode from utf-8 into config charset. If the path
            # contains user typed parts, they are encoded using 'utf-8'.
            if config.charset != 'utf-8':
                try:
                    page = unicode(page, 'utf-8', 'strict')
                    # Fit data into config.charset, replacing what won't
                    # fit. Better have few "?" in the name then crash.
                    page = page.encode(config.charset, 'replace')
                except UnicodeError:
                    pass
                
            # Decode from config.charset, replacing what can't be decoded.
            page = unicode(page, config.charset, 'replace')
            decoded.append(page)

        # Assemble decoded parts
        name = u'/'.join(decoded)
        return name

    def normalizePagename(self, name):
        """ Normalize page name 

        Convert '_' to spaces - allows using nice URLs with spaces, with no
        need to quote.

        Prevent creating page names with invisible characters or funny
        whitespace that might confuse the users or abuse the wiki, or
        just does not make sense.

        Restrict even more group pages, so they can be used inside acl
        lines.
        
        @param name: page name, unicode
        @rtype: unicode
        @return: decoded and sanitized page name
        """
        # Replace underscores with spaces
        name = name.replace(u'_', u' ')

        # Strip invalid characters
        name = config.page_invalid_chars_regex.sub(u'', name)

        # Split to pages and normalize each one
        pages = name.split(u'/')
        normalized = []
        for page in pages:            
            # Ignore empty or whitespace only pages
            if not page or page.isspace():
                continue

            # Cleanup group pages.
            # Strip non alpha numeric characters, keep white space
            if wikiutil.isGroupPage(self, page):
                page = u''.join([c for c in page
                                 if c.isalnum() or c.isspace()])

            # Normalize white space. Each name can contain multiple 
            # words separated with only one space. Split handle all
            # 30 unicode spaces (isspace() == True)
            page = u' '.join(page.split())
            
            normalized.append(page)            
        
        # Assemble components into full pagename
        name = u'/'.join(normalized)
        return name
        
    def read(self, n):
        """ Read n bytes from input stream.
        """
        raise NotImplementedError

    def flush(self):
        """ Flush output stream.
        """
        raise NotImplementedError

    def initdicts(self):
        from MoinMoin import wikidicts
        dicts = wikidicts.GroupDict(self)
        dicts.scandicts()
        return dicts
        
    def isForbidden(self):
        """ check for web spiders and refuse anything except viewing """
        forbidden = 0
        # we do not have a parsed query string here
        # so we can just do simple matching
        if ((self.query_string != '' or self.request_method != 'GET') and
            self.query_string != 'action=rss_rc' and not
            # allow spiders to get attachments and do 'show'
            (self.query_string.find('action=AttachFile') >= 0 and self.query_string.find('do=get') >= 0) and not
            (self.query_string.find('action=show') >= 0)
            ):
            from MoinMoin.util import web
            forbidden = web.isSpiderAgent(self)

        if not forbidden and self.cfg.hosts_deny:
            ip = self.remote_addr
            for host in self.cfg.hosts_deny:
                if ip == host or host[-1] == '.' and ip.startswith(host):
                    forbidden = 1
                    break
        return forbidden


    def setup_args(self, form=None):
        return {}

    def _setup_args_from_cgi_form(self, form=None):
        """ Setup args from a FieldStorage form
        
        Create the args from a standard cgi.FieldStorage to be used by
        derived classes, or from given form.

        All values are decoded using config.charset.

        @keyword form: a cgi.FieldStorage
        @rtype: dict
        @return dict with form keys, each contains a list of values
        """
        decode = wikiutil.decodeUserInput

        # Use cgi.FieldStorage by default
        if form is None:
            form = cgi.FieldStorage()

        args = {}
        # Convert form keys to dict keys, each key contains a list of
        # values.
        for key in form.keys():
            values = form[key]
            if not isinstance(values, types.ListType):
                values = [values]
            fixedResult = []
            for i in values:
                if isinstance(i, cgi.MiniFieldStorage):
                    data = decode(i.value, self.decode_charsets)
                elif isinstance(i, cgi.FieldStorage):
                    data = i.value
                    if i.filename:
                        # multiple uploads to same form field are stupid!
                        args[key+'__filename__'] = decode(i.filename, self.decode_charsets)
                    else:
                        # we do not have a file upload, so we decode:
                        data = decode(data, self.decode_charsets)
                # Append decoded value
                fixedResult.append(data)
            
            args[key] = fixedResult
            
        return args

    def getBaseURL(self):
        """ Return a fully qualified URL to this script. """
        return self.getQualifiedURL(self.getScriptname())


    def getQualifiedURL(self, uri=None):
        """ Return a full URL starting with schema, server name and port.

            *uri* -- append this server-rooted uri (must start with a slash)
        """
        if uri and uri[:4] == "http":
            return uri

        schema, stdport = (('http', '80'), ('https', '443'))[self.is_ssl]
        host = self.http_host
        if not host:
            host = self.server_name
            port = self.server_port
            if port != stdport:
                host = "%s:%s" % (host, port)

        result = "%s://%s" % (schema, host)
        if uri:
            result = result + uri

        return result


    def getUserAgent(self):
        """ Get the user agent. """
        return self.http_user_agent

    def makeForbidden(self):
        self.forbidden = True
        self.http_headers([
            'Status: 403 FORBIDDEN',
            'Content-Type: text/plain'
        ])
        self.write('You are not allowed to access this!\r\n')
        self.setResponseCode(403)
        return self.finish()
        
    def run(self):
        # __init__ may have failed
        if self.failed or self.forbidden:
            return
        
        if self.isForbidden():
            self.makeForbidden()
            if self.forbidden:
                return

        self.open_logs()
        _ = self.getText
        self.clock.start('run')

        # Imports
        from MoinMoin.Page import Page

        if self.query_string == 'action=xmlrpc':
            from MoinMoin.wikirpc import xmlrpc
            xmlrpc(self)
            return self.finish()
        
        if self.query_string == 'action=xmlrpc2':
            from MoinMoin.wikirpc import xmlrpc2
            xmlrpc2(self)
            return self.finish()

        # parse request data
        try:
            self.args = self.setup_args()
            self.form = self.args    
            action = self.form.get('action',[None])[0]

            # Get pagename
            # The last component in path_info is the page name, if any
            path = self.getPathinfo()
            if path.startswith('/'):
                pagename = self.normalizePagename(path)
            else:
                pagename = None
        except: # catch and print any exception
            self.reset_output()
            self.http_headers()
            self.print_exception()
            return self.finish()

        try:
            # Handle request. We have these options:
            
            # 1. If user has a bad user name, delete its bad cookie and
            # send him to UserPreferences to make a new account.
            if not user.isValidName(self, self.user.name):
                msg = _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""") % self.user.name
                self.deleteCookie()
                page = wikiutil.getSysPage(self, 'UserPreferences')
                page.send_page(self, msg=msg)

            # 2. Or jump to page where user left off
            elif not pagename and not action and self.user.remember_last_visit:
                pagetrail = self.user.getTrail()
                if pagetrail:
                    # Redirect to last page visited
                    url = Page(self, pagetrail[-1]).url(self)
                else:
                    # Or to localized FrontPage
                    url = wikiutil.getFrontPage(self).url(self)
                self.http_redirect(url)
                return self.finish()
            
            # 3. Or save drawing
            elif (self.form.has_key('filepath') and
                self.form.has_key('noredirect')):
                # looks like user wants to save a drawing
                from MoinMoin.action.AttachFile import execute
                # TODO: what if pagename is None?
                execute(pagename, self)
                raise MoinMoinNoFooter           

            # 4. Or handle action
            elif action:
                # Use localized FrontPage if pagename is empty
                if not pagename:
                    self.page = wikiutil.getFrontPage(self)
                else:
                    self.page = Page(self, pagename)

                # Complain about unknown actions
                if not action in self.getKnownActions():
                    self.http_headers()
                    self.write(u'<html><body><h1>Unknown action %s</h1></body>' % wikiutil.escape(action))

                # Disallow non available actions
                elif (action[0].isupper() and
                      not action in self.getAvailableActions(self.page)):
                    # Send page with error
                    msg = _("You are not allowed to do %s on this page.") % wikiutil.escape(action)
                    if not self.user.valid:
                        # Suggest non valid user to login
                        login = wikiutil.getSysPage(self, 'UserPreferences')
                        login = login.link_to(self, _('Login'))
                        msg += _(" %s and try again.", formatted=0) % login
                    self.page.send_page(self, msg=msg)

                # Try action
                else:
                    from MoinMoin.wikiaction import getHandler
                    handler = getHandler(self, action)
                    handler(self.page.page_name, self)

            # 5. Or redirect to another page
            elif self.form.has_key('goto'):
                self.http_redirect(Page(self, self.form['goto'][0]).url(self))
                return self.finish()

            # 6. Or (at last) visit pagename
            else:
                if not pagename:
                    # Get pagename from the query string
                    pagename = self.normalizePagename(self.query_string)
                    
                # pagename could be empty after normalization e.g. '///' -> ''
                if not pagename:
                    pagename = wikiutil.getFrontPage(self).page_name

                # Visit pagename
                if self.cfg.allow_extended_names:
                    self.page = Page(self, pagename)
                    self.page.send_page(self, count_hit=1)
                else:
                    # TODO: kill this. Why disable allow extended names?
                    from MoinMoin.parser.wiki import Parser
                    import re
                    word_match = re.match(Parser.word_rule, pagename)
                    if word_match:
                        word = word_match.group(0)
                        self.page = Page(self, word)
                        self.page.send_page(self, count_hit=1)
                    else:
                        self.http_headers()
                        err = u'<p>%s "<pre>%s</pre>"' % (
                            _("Can't work out query"), pagename)
                        self.write(err)

            # generate page footer (actions that do not want this footer
            # use raise util.MoinMoinNoFooter to break out of the
            # default execution path, see the "except MoinMoinNoFooter"
            # below)

            self.clock.stop('run')
            self.clock.stop('total')

            # Close html code
            if not self.no_closing_html_code:
                if (self.cfg.show_timings and
                    self.form.get('action', [None])[0] != 'print'):
                    self.write('<ul id="timings">\n')
                    for t in self.clock.dump():
                        self.write('<li>%s</li>\n' % t)
                    self.write('</ul>\n')

                self.write('</body>\n</html>\n\n')
            
        except MoinMoinNoFooter:
            pass

        except error.FatalError, err:
            self.fail(err)
            
        except: # catch and print any exception
            saved_exc = sys.exc_info()
            self.reset_output()
            self.http_headers()
            self.write(u"\n<!-- ERROR REPORT FOLLOWS -->\n")
            try:
                from MoinMoin.support import cgitb
            except:
                # no cgitb, for whatever reason
                self.print_exception(*saved_exc)
            else:
                try:
                    cgitb.Hook(file=self).handle(saved_exc)
                    # was: cgitb.handler()
                except:
                    self.print_exception(*saved_exc)
                    self.write("\n\n<hr>\n")
                    self.write("<p><strong>Additionally, cgitb raised this exception:</strong></p>\n")
                    self.print_exception()
            del saved_exc

        return self.finish()

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL """
        if url.find("://") == -1:
            url = self.getQualifiedURL(url)

        self.http_headers(["Status: 302", "Location: %s" % url])

    def setResponseCode(self, code, message=None):
        pass

    def fail(self, err):
        """ Fail with nice error message when we can't continue

        Log the error, then try to print nice error message.

        @param err: MoinMoin.error.FatalError instance or subclass.
        """
        self.failed = 1 # save state for self.run()
        self.log(err.asLog())
        self.http_headers()
        self.write(err.asHTML())    
        return self.finish()
            
    def print_exception(self, type=None, value=None, tb=None, limit=None):
        if type is None:
            type, value, tb = sys.exc_info()
        import traceback
        self.write("<h2>request.print_exception handler</h2>\n")
        self.write("<h3>Traceback (most recent call last):</h3>\n")
        list = traceback.format_tb(tb, limit) + \
               traceback.format_exception_only(type, value)
        self.write("<pre>%s<strong>%s</strong></pre>\n" % (
            wikiutil.escape("".join(list[:-1])),
            wikiutil.escape(list[-1]),))
        del tb

    def open_logs(self):
        pass

    def makeUniqueID(self, base):
        """
        Generates a unique ID using a given base name. Appends a
        running count to the base.

        @param base: the base of the id
        @type base: unicode

        @returns: an unique id
        @rtype: unicode
        """
        if not isinstance(base, types.UnicodeType):
            base=unicode(str(base),'ascii','ignore')
        count = self._page_ids.get(base,-1) + 1
        self._page_ids[base] = count
        if count==0:
            return base
        return u'%s_%04d' % (base, count)

    def httpDate(self, when=None, rfc='1123'):
        """ Returns http date string, according to rfc2068

        See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-3.3

        Http 1.1 server should use only rfc1123 date, but cookies
        expires field should use older rfc850 date.

        @param when: seconds from epoch, as returned by time.time()
        @param rfc: either '1123' or '850'
        @rtype: string
        @return: http date
        """
        if when is None:
            when = time.time()
        if rfc not in ['1123', '850']:
            raise ValueError("%s: Invalid rfc value" % rfc)

        import locale
        t = time.gmtime(when)
        
        # TODO: make this a critical section for persistent environments
        # Should acquire lock here
        loc=locale.setlocale(locale.LC_TIME, 'C')
        if rfc == '1123':
            date = time.strftime("%A, %d %b %Y %H:%M:%S GMT", t)
        else:
            date = time.strftime("%A, %d-%b-%Y %H:%M:%S GMT", t)
        locale.setlocale(locale.LC_TIME, loc)
        # Should release lock here
        
        return date
    
    def disableHttpCaching(self):
        """ Prevent caching of pages that should not be cached

        This is important to prevent caches break acl by providing one
        user pages meant to be seen only by another user, when both users
        share the same caching proxy.
        """
        # Run only once
        if hasattr(self, 'http_caching_disabled'):
            return
        self.http_caching_disabled = 1

        # Set Cache control header for http 1.1 caches
        # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.3
        # and http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.9
        self.setHttpHeader('Cache-Control: no-cache="set-cookie"')
        self.setHttpHeader('Cache-Control: private')
        self.setHttpHeader('Cache-Control: max-age=0')       

        # Set Expires for http 1.0 caches (does not support Cache-Control)
        yearago = time.time() - (3600 * 24 * 365)
        self.setHttpHeader('Expires: %s' % self.httpDate(when=yearago))

        # Set Pragma for http 1.0 caches
        # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.32
        self.setHttpHeader('Pragma: no-cache')
       
    def setCookie(self):
        """ Set cookie for the current user
        
        cfg.cookie_lifetime and the user 'remember_me' setting set the
        lifetime of the cookie. lifetime in int hours, see table:
        
        value   cookie lifetime
        ----------------------------------------------------------------
         = 0    forever, ignoring user 'remember_me' setting
         > 0    n hours, or forever if user checked 'remember_me'
         < 0    -n hours, ignoring user 'remember_me' setting

        TODO: do we really need this cookie_lifetime setting?
        """
        # Calculate cookie maxage and expires
        lifetime = int(self.cfg.cookie_lifetime) * 3600 
        forever = 10*365*24*3600 # 10 years
        now = time.time()
        if not lifetime:
            maxage = forever
        elif lifetime > 0:
            if self.user.remember_me:
                maxage = forever
            else:
                maxage = lifetime
        elif lifetime < 0:
            maxage = (-lifetime)
        expires = now + maxage
        
        # Set the cookie
        from Cookie import SimpleCookie
        c = SimpleCookie()
        c['MOIN_ID'] = self.user.id
        c['MOIN_ID']['max-age'] = maxage
        c['MOIN_ID']['path'] = self.getScriptname()
        # Set expires for older clients
        c['MOIN_ID']['expires'] = self.httpDate(when=expires, rfc='850')        
        self.setHttpHeader(c.output())

        # Update the saved cookie, so other code works with new setup
        self.saved_cookie = c.output()

        # IMPORTANT: Prevent caching of current page and cookie
        self.disableHttpCaching()

    def deleteCookie(self):
        """ Delete the user cookie by sending expired cookie with null value

        According to http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.2
        Deleted cookie should have Max-Age=0. We also have expires
        attribute, which is probably needed for older browsers.

        Finally, delete the saved cookie and create a new user based on
        the new settings.
        """
        # Set cookie
        from Cookie import SimpleCookie
        c = SimpleCookie()
        c['MOIN_ID'] = ''
        c['MOIN_ID']['path'] = self.getScriptname()
        c['MOIN_ID']['max-age'] = 0
        # Set expires to one year ago for older clients
        yearago = time.time() - (3600 * 24 * 365)
        c['MOIN_ID']['expires'] = self.httpDate(when=yearago, rfc='850')
        self.setHttpHeader(c.output())

        # Update saved cookie and set new unregistered user
        self.saved_cookie = ''
        self.auth_username = ''
        self.user = user.User(self)

        # IMPORTANT: Prevent caching of current page and cookie        
        self.disableHttpCaching()

    def finish(self):
        """ General cleanup on end of request
        
        Delete circular references - all object that we create using
        self.name = class(self)
        This helps Python to collect these objects and keep our
        memory footprint lower
        """
        try:
            del self.user
            del self.theme
            del self.dicts
        except:
            pass

# CGI ---------------------------------------------------------------

class RequestCGI(RequestBase):
    """ specialized on CGI requests """

    def __init__(self, properties={}):
        try:
            self._setup_vars_from_std_env(os.environ)
            #sys.stderr.write("----\n")
            #for key in os.environ.keys():    
            #    sys.stderr.write("    %s = '%s'\n" % (key, os.environ[key]))
            RequestBase.__init__(self, properties)

            # force input/output to binary
            if sys.platform == "win32":
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

        except error.FatalError, err:
            self.fail(err)
            
    def open_logs(self):
        # create log file for catching stderr output
        if not self.opened_logs:
            sys.stderr = open(os.path.join(self.cfg.data_dir, 'error.log'), 'at')
            self.opened_logs = 1

    def setup_args(self, form=None):
        return self._setup_args_from_cgi_form(form)
        
    def read(self, n=None):
        """ Read from input stream.
        """
        if n is None:
            return sys.stdin.read()
        else:
            return sys.stdin.read(n)

    def write(self, *data):
        """ Write to output stream.
        """
        sys.stdout.write(self.encode(data))

    def flush(self):
        sys.stdout.flush()
        
    def finish(self):
        RequestBase.finish(self)
        # flush the output, ignore errors caused by the user closing the socket
        try:
            sys.stdout.flush()
        except IOError, ex:
            import errno
            if ex.errno != errno.EPIPE: raise

    # Accessors --------------------------------------------------------
    
    def getPathinfo(self):
        """ Return the remaining part of the URL. """
        pathinfo = self.path_info

        # Fix for bug in IIS/4.0
        if os.name == 'nt':
            scriptname = self.getScriptname()
            if pathinfo.startswith(scriptname):
                pathinfo = pathinfo[len(scriptname):]

        return pathinfo

    # Headers ----------------------------------------------------------
    
    def setHttpHeader(self, header):
        self.user_headers.append(header)


    def http_headers(self, more_headers=[]):
        # Send only once
        if getattr(self, 'sent_headers', None):
            return
        
        self.sent_headers = 1
        have_ct = 0

        # send http headers
        for header in more_headers + getattr(self, 'user_headers', []):
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1
            if type(header) is unicode:
                header = header.encode('ascii')
            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))


# Twisted -----------------------------------------------------------

class RequestTwisted(RequestBase):
    """ specialized on Twisted requests """

    def __init__(self, twistedRequest, pagename, reactor, properties={}):
        try:
            self.twistd = twistedRequest
            self.http_accept_language = self.twistd.getHeader('Accept-Language')
            self.reactor = reactor
            self.saved_cookie = self.twistd.getHeader('Cookie')
            self.server_protocol = self.twistd.clientproto
            self.server_name = self.twistd.getRequestHostname().split(':')[0]
            self.server_port = str(self.twistd.getHost()[2])
            self.is_ssl = self.twistd.isSecure()
            if self.server_port != ('80', '443')[self.is_ssl]:
                self.http_host = self.server_name + ':' + self.server_port
            else:
                self.http_host = self.server_name
            self.script_name = "/" + '/'.join(self.twistd.prepath[:-1])
            path_info = '/' + '/'.join([pagename] + self.twistd.postpath)
            self.path_info = self.decodePagename(path_info)
            self.request_method = self.twistd.method
            self.remote_host = self.twistd.getClient()
            self.remote_addr = self.twistd.getClientIP()
            self.http_user_agent = self.twistd.getHeader('User-Agent')
            self.request_uri = self.twistd.uri
            self.url = self.http_host + self.request_uri # was: self.server_name + self.request_uri

            ac = self.twistd.getHeader('Accept-Charset') or ''
            self.accepted_charsets = self.parse_accept_charset(ac)

            qindex = self.request_uri.find('?')
            if qindex != -1:
                query_string = self.request_uri[qindex+1:]
                self.query_string = self.decodePagename(query_string)
            else:
                self.query_string = ''
            self.outputlist = []
            self.auth_username = None

            # need config here, so check:
            self._load_multi_cfg()
            
            if self.cfg.auth_http_enabled and self.cfg.auth_http_insecure:
                self.auth_username = self.twistd.getUser()
            # TODO password check, twisted does NOT do that for us
            # this maybe requires bigger or critical changes, so we delay that
            # to 1.4's new auth stuff

            RequestBase.__init__(self, properties)
            #print "request.RequestTwisted.__init__: received_headers=\n" + str(self.twistd.received_headers)

        except error.FatalError, err:
            self.fail(err)
            
    def setup_args(self, form=None):
        args = {}
        for key,values in self.twistd.args.items():
            if key[-12:] == "__filename__":
                args[key] = wikiutil.decodeUserInput(values, self.decode_charsets)
                continue
            if not isinstance(values, types.ListType):
                values = [values]
            fixedResult = []
            for v in values:
                if not self.twistd.args.has_key(key+"__filename__"):
                    v = wikiutil.decodeUserInput(v, self.decode_charsets)
                fixedResult.append(v)
            args[key] = fixedResult
        return args
        
    def read(self, n=None):
        """ Read from input stream.
        """
        # XXX why is that wrong?:
        #rd = self.reactor.callFromThread(self.twistd.read)
        
        # XXX do we need self.reactor.callFromThread with that?
        # XXX if yes, why doesn't it work?
        self.twistd.content.seek(0, 0)
        if n is None:
            rd = self.twistd.content.read()
        else:
            rd = self.twistd.content.read(n)
        #print "request.RequestTwisted.read: data=\n" + str(rd)
        return rd
    
    def write(self, *data):
        """ Write to output stream.
        """
        #print "request.RequestTwisted.write: data=\n" + wd
        self.reactor.callFromThread(self.twistd.write, self.encode(data))

    def flush(self):
        pass # XXX is there a flush in twisted?

    def finish(self):
        RequestBase.finish(self)
        self.reactor.callFromThread(self.twistd.finish)

    def open_logs(self):
        return
        # create log file for catching stderr output
        if not self.opened_logs:
            sys.stderr = open(os.path.join(self.cfg.data_dir, 'error.log'), 'at')
            self.opened_logs = 1

    # Headers ----------------------------------------------------------

    def setHttpHeader(self, header):
        self.user_headers.append(header)

    def __setHttpHeader(self, header):
        if type(header) is unicode:
            header = header.encode('ascii')
        key, value = header.split(':',1)
        value = value.lstrip()
        if key.lower()=='set-cookie':
            key, value = value.split('=',1)
            self.twistd.addCookie(key, value)
        else:
            self.twistd.setHeader(key, value)
        #print "request.RequestTwisted.setHttpHeader: %s" % header

    def http_headers(self, more_headers=[]):
        if getattr(self, 'sent_headers', None):
            return
        self.sent_headers = 1
        have_ct = 0

        # set http headers
        for header in more_headers + self.user_headers:
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1
            self.__setHttpHeader(header)

        if not have_ct:
            self.__setHttpHeader("Content-type: text/html;charset=%s" % config.charset)

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL """
        if url.count("://") == 0:
            # no https method??
            url = "http://%s:%s%s" % (self.server_name, self.server_port, url)

        if isinstance(url, type(u'')):
            url = url.encode('ascii')
        self.twistd.redirect(url)
        # calling finish here will send the rest of the data to the next
        # request. leave the finish call to run()
        #self.twistd.finish()
        raise MoinMoinNoFooter

    def setResponseCode(self, code, message=None):
        self.twistd.setResponseCode(code, message)
        
# CLI ------------------------------------------------------------------

class RequestCLI(RequestBase):
    """ specialized on command line interface and script requests """

    def __init__(self, url='CLI', pagename='', properties={}):
        self.http_accept_language = ''
        self.saved_cookie = ''
        self.path_info = self.decodePagename('/' + pagename)
        self.query_string = ''
        self.remote_addr = '127.0.0.127'
        self.is_ssl = 0
        self.auth_username = None
        self.http_user_agent = 'CLI/Script'
        self.outputlist = []
        self.url = url
        self.accepted_charsets = ['utf-8']
        self.decode_charsets = self.accepted_charsets
        self.request_method = 'GET'
        self.request_uri = '/' + pagename # TODO check
        self.server_name = 'localhost'
        self.server_port = '80'
        self.http_host = 'localhost'
        self.http_referer = ''
        self.script_name = ''
        RequestBase.__init__(self, properties)
        self.cfg.caching_formats = [] # don't spoil the cache

    def read(self, n=None):
        """ Read from input stream.
        """
        if n is None:
            return sys.stdin.read()
        else:
            return sys.stdin.read(n)

    def write(self, *data):
        """ Write to output stream.
        """
        sys.stdout.write(self.encode(data))

    def flush(self):
        sys.stdout.flush()
        
    def finish(self):
        RequestBase.finish(self)
        # flush the output, ignore errors caused by the user closing the socket
        try:
            sys.stdout.flush()
        except IOError, ex:
            import errno
            if ex.errno != errno.EPIPE: raise

    def isForbidden(self):
        """ check for web spiders and refuse anything except viewing """
        return 0

    # Accessors --------------------------------------------------------

    def getScriptname(self):
        """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
        return '.'

    def getQualifiedURL(self, uri = None):
        """ Return a full URL starting with schema, server name and port.

            *uri* -- append this server-rooted uri (must start with a slash)
        """
        return uri

    def getBaseURL(self):
        """ Return a fully qualified URL to this script. """
        return self.getQualifiedURL(self.getScriptname())

    # Headers ----------------------------------------------------------

    def setHttpHeader(self, header):
        pass

    def http_headers(self, more_headers=[]):
        pass

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL """
        raise Exception("Redirect not supported for command line tools!")


# StandAlone Server ----------------------------------------------------

class RequestStandAlone(RequestBase):
    """
    specialized on StandAlone Server (MoinMoin.server.standalone) requests
    """

    def __init__(self, sa, properties={}):
        """
        @param sa: stand alone server object
        @param properties: ...
        """
        try:
            self.sareq = sa
            self.wfile = sa.wfile
            self.rfile = sa.rfile
            self.headers = sa.headers
            self.is_ssl = 0

            # Split path and query string and unquote path
            # query is unquoted by setup_args
            import urllib
            if '?' in sa.path:
                path, query = sa.path.split('?', 1)
            else:
                path, query = sa.path, ''
            path = urllib.unquote(path)

            #HTTP headers
            self.env = {} 
            for hline in sa.headers.headers:
                key = sa.headers.isheader(hline)
                if key:
                    hdr = sa.headers.getheader(key)
                    self.env[key] = hdr

            #accept = []
            #for line in sa.headers.getallmatchingheaders('accept'):
            #    if line[:1] in string.whitespace:
            #        accept.append(line.strip())
            #    else:
            #        accept = accept + line[7:].split(',')
            #
            #env['HTTP_ACCEPT'] = ','.join(accept)

            co = filter(None, sa.headers.getheaders('cookie'))

            self.http_accept_language = sa.headers.getheader('Accept-Language')
            self.server_name = sa.server.server_name
            self.server_port = str(sa.server.server_port)
            self.http_host = sa.headers.getheader('host')
            # Make sure http referer use only ascii
            referer = sa.headers.getheader('referer') or ''
            self.http_referer = unicode(referer, 'ascii',
                                        'replace').encode('ascii', 'replace')
            self.saved_cookie = ', '.join(co) or ''
            self.script_name = ''
            self.request_method = sa.command
            self.request_uri = sa.path
            self.remote_addr = sa.client_address[0]
            self.http_user_agent = sa.headers.getheader('user-agent') or ''
            # next must be http_host as server_name == reverse_lookup(IP)
            if self.http_host:
                self.url = self.http_host + self.request_uri
            else:
                self.url = "localhost" + self.request_uri

            ac = sa.headers.getheader('Accept-Charset') or ''
            self.accepted_charsets = self.parse_accept_charset(ac)

            # Decode path_info and query string, they may contain non-ascii
            self.path_info = self.decodePagename(path) 
            self.query_string = self.decodePagename(query)        

            # from standalone script:
            # XXX AUTH_TYPE
            # XXX REMOTE_USER
            # XXX REMOTE_IDENT
            self.auth_username = None
            #env['PATH_TRANSLATED'] = uqrest #self.translate_path(uqrest)
            #host = self.address_string()
            #if host != self.client_address[0]:
            #    env['REMOTE_HOST'] = host
            # env['SERVER_PROTOCOL'] = self.protocol_version
            RequestBase.__init__(self, properties)

        except error.FatalError, err:
            self.fail(err)

    def setup_args(self, form=None):
        self.env['REQUEST_METHOD'] = self.request_method

        # This is a ugly hack to get the query into the environment, due
        # to the wired way standalone form is created.
        self.env['QUERY_STRING'] = self.query_string.encode(config.charset)

        ct = self.headers.getheader('content-type')
        if ct:
            self.env['CONTENT_TYPE'] = ct
        cl = self.headers.getheader('content-length')
        if cl:
            self.env['CONTENT_LENGTH'] = cl
        
        #print "env = ", self.env
        #form = cgi.FieldStorage(self, headers=self.env, environ=self.env)
        if form is None:
            form = cgi.FieldStorage(self.rfile, environ=self.env)
        return self._setup_args_from_cgi_form(form)
        
    def read(self, n=None):
        """ Read from input stream.
        """
        if n is None:
            return self.rfile.read()
        else:
            return self.rfile.read(n)

    def write(self, *data):
        """ Write to output stream.
        """
        self.wfile.write(self.encode(data))

    def flush(self):
        self.wfile.flush()
        
    def finish(self):
        RequestBase.finish(self)
        self.wfile.flush()

    # Headers ----------------------------------------------------------

    def setHttpHeader(self, header):
        self.user_headers.append(header)

    def http_headers(self, more_headers=[]):
        if getattr(self, 'sent_headers', None):
            return
        self.sent_headers = 1

        # check for status header and send it
        our_status = 200
        for header in more_headers + self.user_headers:
            if header.lower().startswith("status:"):
                try:
                    our_status = int(header.split(':',1)[1].strip().split(" ", 1)[0]) 
                except:
                    pass
                # there should be only one!
                break
        # send response
        self.sareq.send_response(our_status)

        # send http headers
        have_ct = 0
        for header in more_headers + self.user_headers:
            if type(header) is unicode:
                header = header.encode('ascii')
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1

            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))


# mod_python/Apache ----------------------------------------------------

class RequestModPy(RequestBase):
    """ specialized on mod_python requests """

    def __init__(self, req):
        """ Saves mod_pythons request and sets basic variables using
            the req.subprocess_env, cause this provides a standard
            way to access the values we need here.

            @param req: the mod_python request instance
        """
        try:
            # flags if headers sent out contained content-type or status
            self._have_ct = 0
            self._have_status = 0

            req.add_common_vars()
            self.mpyreq = req
            # some mod_python 2.7.X has no get method for table objects,
            # so we make a real dict out of it first.
            if not hasattr(req.subprocess_env,'get'):
                env=dict(req.subprocess_env)
            else:
                env=req.subprocess_env
            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self)

        except error.FatalError, err:
            self.fail(err)
            
    def setup_args(self, form=None):
        """ Sets up args by using mod_python.util.FieldStorage, which
            is different to cgi.FieldStorage. So we need a separate
            method for this.
        """
        from mod_python import util
        if form is None:
            form = util.FieldStorage(self.mpyreq)

        args = {}
        for key in form.keys():
            values = form[key]
            if not isinstance(values, types.ListType):
                values = [values]
            fixedResult = []
            for i in values:
                ## if object has a filename attribute, remember it
                ## with a name hack
                if hasattr(i,'filename') and i.filename:
                    args[key+'__filename__']=i.filename
                    has_fn=1
                else:
                    has_fn=0
                ## mod_python 2.7 might return strings instead
                ## of Field objects
                if hasattr(i,'value'):
                    i = i.value
                ## decode if it is not a file
                if not has_fn:
                    i = wikiutil.decodeUserInput(i, self.decode_charsets)
                fixedResult.append(i)
            args[key] = fixedResult
        return args

    def run(self, req):
        """ mod_python calls this with its request object. We don't
            need it cause its already passed to __init__. So ignore
            it and just return RequestBase.run.

            @param req: the mod_python request instance
        """
        return RequestBase.run(self)

    def read(self, n=None):
        """ Read from input stream.
        """
        if n is None:
            return self.mpyreq.read()
        else:
            return self.mpyreq.read(n)

    def write(self, *data):
        """ Write to output stream.
        """
        self.mpyreq.write(self.encode(data))

    def flush(self):
        """ We can't flush it, so do nothing.
        """
        pass
        
    def finish(self):
        """ Just return apache.OK. Status is set in req.status.
        """
        RequestBase.finish(self)
        # is it possible that we need to return something else here?
        from mod_python import apache
        return apache.OK

    # Headers ----------------------------------------------------------

    def setHttpHeader(self, header):
        """ Filters out content-type and status to set them directly
            in the mod_python request. Rest is put into the headers_out
            member of the mod_python request.

            @param header: string, containing valid HTTP header.
        """
        if type(header) is unicode:
            header = header.encode('ascii')
        key, value = header.split(':',1)
        value = value.lstrip()
        if key.lower() == 'content-type':
            # save content-type for http_headers
            if not self._have_ct:
                # we only use the first content-type!
                self.mpyreq.content_type = value
                self._have_ct = 1
        elif key.lower() == 'status':
            # save status for finish
            try:
                self.mpyreq.status = int(value.split(' ',1)[0])
            except:
                pass
            else:
                self._have_status = 1
        else:
            # this is a header we sent out
            self.mpyreq.headers_out[key]=value

    def http_headers(self, more_headers=[]):
        """ Sends out headers and possibly sets default content-type
            and status.

            @keyword more_headers: list of strings, defaults to []
        """
        for header in more_headers:
            self.setHttpHeader(header)
        # if we don't had an content-type header, set text/html
        if self._have_ct == 0:
            self.mpyreq.content_type = "text/html;charset=%s" % config.charset
        # if we don't had a status header, set 200
        if self._have_status == 0:
            self.mpyreq.status = 200
        # this is for mod_python 2.7.X, for 3.X it's a NOP
        self.mpyreq.send_http_header()

# FastCGI -----------------------------------------------------------

class RequestFastCGI(RequestBase):
    """ specialized on FastCGI requests """

    def __init__(self, fcgRequest, env, form, properties={}):
        """ Initializes variables from FastCGI environment and saves
            FastCGI request and form for further use.

            @param fcgRequest: the FastCGI request instance.
            @param env: environment passed by FastCGI.
            @param form: FieldStorage passed by FastCGI.
        """
        try:
            self.fcgreq = fcgRequest
            self.fcgenv = env
            self.fcgform = form
            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, properties)

        except error.FatalError, err:
            self.fail(err)

    def setup_args(self, form=None):
        """ Use the FastCGI form to setup arguments. """
        if form is None:
            form = self.fcgform
        return self._setup_args_from_cgi_form(form)

    def read(self, n=None):
        """ Read from input stream.
        """
        if n is None:
            return self.fcgreq.stdin.read()
        else:
            return self.fcgreq.stdin.read(n)

    def write(self, *data):
        """ Write to output stream.
        """
        self.fcgreq.out.write(self.encode(data))

    def flush(self):
        """ Flush output stream.
        """
        self.fcgreq.flush_out()

    def finish(self):
        """ Call finish method of FastCGI request to finish handling
            of this request.
        """
        RequestBase.finish(self)
        self.fcgreq.finish()

    # Accessors --------------------------------------------------------

    def getPathinfo(self):
        """ Return the remaining part of the URL. """
        pathinfo = self.path_info

        # Fix for bug in IIS/4.0
        if os.name == 'nt':
            scriptname = self.getScriptname()
            if pathinfo.startswith(scriptname):
                pathinfo = pathinfo[len(scriptname):]

        return pathinfo

    # Headers ----------------------------------------------------------
    
    def setHttpHeader(self, header):
        """ Save header for later send. """
        self.user_headers.append(header)


    def http_headers(self, more_headers=[]):
        """ Send out HTTP headers. Possibly set a default content-type.
        """
        if getattr(self, 'sent_headers', None):
            return
        self.sent_headers = 1
        have_ct = 0

        # send http headers
        for header in more_headers + self.user_headers:
            if type(header) is unicode:
                header = header.encode('ascii')
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1
            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))


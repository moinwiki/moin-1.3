# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Multiple config handler
    and
    MoinMoin - Configuration defaults class

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, os, sys
from MoinMoin import error


_url_re = None
def url_re():
    """ Return url matching regular expression

    Using this regular expression, we find the config_module for each
    url.
    
    Import wikis from 'farmconfig' on the first time, compile and cache url_re
    regular expression, and return it.

    Note: You must restart a long running process when you edit
    farmconfig.py config file.

    @rtype: compiled re object
    @return: url to wiki config  matching re
    """
    global _url_re
    if not _url_re:
        try:
            farmconfig = __import__('farmconfig', globals(), {})
            pattern = '|'.join([r'(?P<%s>%s)' % (name, regex)
                                for name, regex in farmconfig.wikis])
            _url_re = re.compile(pattern)
        except (ImportError, AttributeError):
            # It is not there, so we maybe have only one config. Fall back to
            # old config file name and use it for all urls we get.
            # Or we have a farmconfig file, but it does not contain a wikis
            # attribute (because of typo or everything commented out as in
            # sample config).
            _url_re = re.compile(r'(?P<wikiconfig>.)')
    return _url_re


def getConfig(url):
    """ Make and return config object, or raise an error

    If the config file is not found or broken, either because of a typo
    in farmconfig or deleted file or some other error, we raise a
    ConfigurationError which is handled by our client.
    
    @param url: the url from request, possibly matching specific wiki
    @rtype: DefaultConfig subclass instance
    @return: config object for specific wiki
    """
    match = url_re().match(url)
    if match and match.groups():
        # Get config module name from match
        for name, value in match.groupdict().items():
            if value: break

        # FIXME: we should cache config objects by wiki url and return
        # here a ready to use config, instead of creating new instance
        # for each request.
        
        try:
            module =  __import__(name, globals(), {})
            Config = getattr(module, 'Config', None)
            if Config:
                # Config found, return config instance using name as
                # site identifier (name must be unique of our url_re).
                cfg = Config(name)
                return cfg
            else:
                # Broken config file, probably old config from 1.2
                msg = '''
Could not find required "Config" class in "%(name)s.py". This might
happen if you are trying to use a pre 1.3 configuration file, or made a
syntax or spelling error.

Please check your configuration file. As an example for correct syntax,
use the wikiconfig.py file from the distribution.
''' % {'name': name}

        # We don't handle fatal errors here
        except error.FatalError, err:
            raise err

        # These errors will not be big surprise:       
        except ImportError, err:
            msg = '''
Import of configuration file "%(name)s.py" failed because of
ImportError: %(err)s.

Check that the file is in the same directory as the server script. If
it is not, you must add the path of the directory where the file is located
to the python path in the server script. See the comments at the top of
the server script.

Check that the configuration file name is either "wikiconfig.py" or the
module name specified in the wikis list in farmconfig.py. Note that the module
name does not include the ".py" suffix.
''' % {'name': name, 'err': str(err)}

        except IndentationError, err:
            msg = '''
Import of configuration file "%(name)s.py" failed because of
IndentationError: %(err)s.

The configuration files are python modules. Therefore, whitespace is
important. Make sure that you use only spaces, no tabs are allowed here!
You have to use four spaces at the beginning of the line mostly.
''' % {'name': name, 'err': str(err)}

        # But people can have many other errors. We hope that the python
        # error message will help them.
        except:
            err = sys.exc_info()[1]
            msg = '''
Import of configuration file "%(name)s.py" failed because of %(class)s:
%(err)s.

We hope this error message make sense. If not, you are welcome to ask on
the page http://moinmoin.wikiwikiweb.de/MoinMoinQuestions/ConfigFiles
or the #moin channel on irc.freenode.net or on the mailing list.
''' % {'name': name, 'class': err.__class__.__name__, 'err': str(err)}

    else:
        # URL did not match anything, probably error in farmconfig.wikis 
        msg = '''
Could not find a match for url: "%(url)s".

Check your URL regular expressions in the "wikis" list in
"farmconfig.py". 
''' % {'url': url}

    raise error.ConfigurationError(msg)


# This is a way to mark some text for the gettext tools so that they don't
# get orphaned. See http://www.python.org/doc/current/lib/node278.html.
def _(text): return text


class DefaultConfig:
    """ default config values

    FIXME: update according to MoinMoin:UpdateConfiguration
    """    
    acl_enabled = 0
    # All acl_right lines must use unicode!
    acl_rights_default = u"Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write"
    acl_rights_before = u""
    acl_rights_after = u""
    acl_rights_valid = ['read', 'write', 'delete', 'revert', 'admin']
    
    allow_extended_names = 1
    allow_numeric_entities = 1
    allowed_actions = []
    allow_xslt = 0
    attachments = None # {'dir': path, 'url': url-prefix}
    auth_http_enabled = 0
    auth_http_insecure = 0
    bang_meta = 0
    backtick_meta = 1
    caching_formats = ['text_html']
    changed_time_fmt = '%H:%M'
    # chars_{upper,lower,digits,spaces} see MoinMoin/util/chartypes.py
    # if you have gdchart, add something like
    # chart_options = {'width = 720, 'height': 540}
    chart_options = None
    config_check_enabled = 0
    cookie_lifetime = 12 # 12 hours from now
    data_dir = './data/'
    data_underlay_dir = './underlay/'
    date_fmt = '%Y-%m-%d'
    datetime_fmt = '%Y-%m-%d %H:%M:%S'
    default_lang = 'en'
    default_markup = 'wiki'
    edit_locking = 'warn 10' # None, 'warn <timeout mins>', 'lock <timeout mins>'
    edit_rows = 30
    hosts_deny = []
    html_head = ''
    html_head_queries = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_posts   = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_index   = '''<meta name="robots" content="index,follow">\n'''
    html_head_normal  = '''<meta name="robots" content="index,nofollow">\n'''
    html_pagetitle = None

    mail_login = None # or "user pwd" if you need to use SMTP AUTH
    mail_smarthost = None
    mail_from = None
    navi_bar = [ u'%(page_front_page)s', u'RecentChanges', u'FindPage', u'HelpContents', ]
    nonexist_qm = 0

    page_credits = [
        '<a href="http://moinmoin.wikiwikiweb.de/">MoinMoin Powered</a>',
        '<a href="http://www.python.org/">Python Powered</a>',
        '<a href="http://validator.w3.org/check?uri=referer">Valid HTML 4.01</a>',
        ]
    page_footer1 = ''
    page_footer2 = ''

    page_header1 = ''
    page_header2 = ''
    
    page_front_page = u'FrontPage'
    page_local_spelling_words = u'LocalSpellingWords'
    page_category_regex = u'^Category[A-Z]'
    page_dict_regex = u'[a-z]Dict$'
    page_form_regex = u'[a-z]Form$'
    page_group_regex = u'[a-z]Group$'
    page_template_regex = u'[a-z]Template$'

    page_license_enabled = 0
    page_license_page = u'WikiLicense'

    # These icons will show in this order in the iconbar, unless they
    # are not relevant, e.g email icon when the wiki is not configured
    # for email.
    page_iconbar = ["up", "edit", "view", "diff", "info", "subscribe", "raw", "print",]

    # Standard buttons in the iconbar
    page_icons_table = {
        # key           last part of url, title, icon-key
        'help':        ("%(q_page_help_contents)s", "%(page_help_contents)s", "help"),
        'find':        ("%(q_page_find_page)s?value=%(q_page_name)s", "%(page_find_page)s", "find"),
        'diff':        ("%(q_page_name)s?action=diff", _("Diffs"), "diff"),
        'info':        ("%(q_page_name)s?action=info", _("Info"), "info"),
        'edit':        ("%(q_page_name)s?action=edit", _("Edit"), "edit"),
        'unsubscribe': ("%(q_page_name)s?action=subscribe", _("UnSubscribe"), "unsubscribe"),
        'subscribe':   ("%(q_page_name)s?action=subscribe", _("Subscribe"), "subscribe"),
        'raw':         ("%(q_page_name)s?action=raw", _("Raw"), "raw"),
        'xml':         ("%(q_page_name)s?action=format&amp;mimetype=text/xml", _("XML"), "xml"),
        'print':       ("%(q_page_name)s?action=print", _("Print"), "print"),
        'view':        ("%(q_page_name)s", _("View"), "view"),
        'up':          ("%(q_page_parent_page)s", _("Up"), "up"),
        }
    refresh = None # (minimum_delay, type), e.g.: (2, 'internal')
    shared_intermap = None # can be string or list of strings (filenames)
    show_hosts = 1
    show_section_numbers = 1
    show_timings = 0
    show_version = 0
    siteid = 'default'
    theme_default = 'modern'
    theme_force = False
    trail_size = 5
    tz_offset = 0.0 # default time zone offset in hours from UTC
    
    # a regex of HTTP_USER_AGENTS that should be excluded from logging
    # and receive a FORBIDDEN for anything except viewing a page
    ua_spiders = ('archiver|crawler|curl|google|holmes|htdig|httrack|httpunit|jeeves|larbin|leech|'
                  'linkbot|linkmap|linkwalk|mercator|mirror|nutbot|robot|scooter|'
                  'search|sherlock|sitecheck|spider|wget')

    # Wiki identity
    sitename = u'Untitled Wiki'
    url_prefix = '/wiki'
    logo_string = None
    interwikiname = None
    
    url_mappings = {}
    
    xmlrpc_putpage_enabled = 0 # if 0, putpage will write to a test page only
    xmlrpc_putpage_trusted_only = 1 # if 1, you will need to be http auth authenticated
    
    SecurityPolicy = None

    def __init__(self, siteid):
        """ Init Config instance """
        self.siteid = siteid
        if self.config_check_enabled:
            self._config_check()
            
        # Try to decode certain names which allow unicode
        self._decode()

        # Make sure directories are accessible
        self._check_directories()

        # Load plugin module
        self._loadPluginModule()
        
        # Normalize values
        self.default_lang = self.default_lang.lower()

        # Use site name as default name-logo
        if self.logo_string is None:
            self.logo_string = self.sitename

        # Check for needed modules

        # FIXME: maybe we should do this check later, just before a
        # chart is needed, maybe in the chart module, instead doing it
        # for each request. But this require a large refactoring of
        # current code.
        if self.chart_options:
            try:
                import gdchart
            except ImportError:
                self.chart_options = None
        
        # create excluded_actions with actions thats are not in
        # allowed_actions
        excluded_actions = ['DeletePage', 'AttachFile', 'RenamePage']
        self.excluded_actions = [action for action in excluded_actions
                                 if not action in self.allowed_actions]
        
        # define directories
        self.moinmoin_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.normpath(self.data_dir)
        self.data_dir = data_dir
        for dirname in ('user', 'cache', 'plugin'):
            name = dirname + '_dir'
            if not getattr(self, name, None):
                setattr(self, name, os.path.join(data_dir, dirname))
        
        # post process navibar
        # we replace any string placeholders with config values
        # e.g u'%(page_front_page)s' % self
        self.navi_bar = [elem % self for elem in self.navi_bar]

    def _config_check(self):
        """ Check namespace and warn about unknown names
        
        Warn about names which are not used by DefaultConfig, except
        modules, classes, _private or __magic__ names.

        This check is disabled by default, when enabled, it will show an
        error message with unknown names.
        """       
        unknown = ['"%s"' % name for name in dir(self)
                  if not name.startswith('_') and 
                  not DefaultConfig.__dict__.has_key(name) and
                  not isinstance(getattr(self, name), (type(sys), type(DefaultConfig)))]
        if unknown:
            msg = """
Unknown configuration options: %s.

For more information, visit HelpOnConfiguration. Please check your
configuration for typos before requesting support or reporting a bug.
""" % ', '.join(unknown)
            from MoinMoin import error
            raise error.ConfigurationError(msg)

    def _decode(self):
        """ Try to decode certain names, ignore unicode values
        
        Try to decode str using utf-8. If the decode fail, raise FatalError. 

        Certain config variables should contain unicode values, and
        should be defined with u'text' syntax. Python decode these if
        the file have a 'coding' line.
        
        This will allow utf-8 users to use simple strings using, without
        using u'string'. Other users will have to use u'string' for
        these names, because we don't know what is the charset of the
        config files.
        """
        charset = 'utf-8'

        # TODO: add to translation in 1.4?
        message = u'''
"%(name)s" configuration variable is a string, but should be
unicode. Use %(name)s = u"value" syntax for unicode variables.

Also check your "-*- coding -*-" line at the top of your configuration
file. It should match the actual charset of the configuration file.
'''
        
        decode_names = (
            'sitename', 'logo_string', 'navi_bar', 'page_front_page',
            'page_category_regex', 'page_dict_regex', 'page_form_regex',
            'page_group_regex', 'page_template_regex', 'page_license_page',
            'page_local_spelling_words', 'acl_rights_default',
            'acl_rights_before', 'acl_rights_after',
            )
        
        for name in decode_names:
            attr = getattr(self, name, None)
            if attr:
                # Try to decode strings
                if isinstance(attr, str):
                    try:
                        setattr(self, name, unicode(attr, charset)) 
                    except UnicodeError:
                        raise error.ConfigurationError(message %
                                                       {'name': name})
                # Look into lists and try to decode string inside them
                elif isinstance(attr, list):
                    for i in xrange(len(attr)):
                        item = attr[i]
                        if isinstance(item, str):
                            try:
                                attr[i] = unicode(item, charset)
                            except UnicodeError:
                                raise error.ConfigurationError(message %
                                                               {'name': name})

    def _check_directories(self):
        """ Make sure directories are accessible

        Both data and underlay should exists and allow read, write and
        execute.
        """
        mode = os.F_OK | os.R_OK | os.W_OK | os.X_OK
        for attr in ('data_dir', 'data_underlay_dir'):
            path = getattr(self, attr)
            
            # allow an empty underlay path or None
            if attr == 'data_underlay_dir' and not path:
                continue

            path_pages = os.path.join(path, "pages")
            if not (os.path.isdir(path_pages) and os.access(path_pages, mode)):
                msg = '''
"%(attr)s" does not exists at "%(path)s", or has incorrect ownership and
permissions.

Make sure the directory and the subdirectory pages are owned by the web server and are readable,
writable and executable by the web server user and group.

It is recommended to use absolute paths and not relative paths. Check
also the spelling of the directory name.
''' % {'attr': attr, 'path': path,}
                raise error.ConfigurationError(msg)

    def _loadPluginModule(self):
        """ import plugin module under configname.plugin

        To be able to import plugin from arbitrary path, we have to load
        the base package once using imp.load_module. Later, we can use
        standard __import__ call to load plugins in this package.

        Since each wiki has unique plugins, we load the plugin package
        under the wiki configuration module, named self.siteid.
        """
        import sys, imp

        name = self.siteid + '.plugin'
        
        # Get lock functions - require Python 2.3
        try:
            acquire_lock = imp.acquire_lock
            release_lock = imp.release_lock
        except AttributeError:
            def acquire_lock(): pass
            def release_lock(): pass

        try:
            # Lock other threads while we check and import
            acquire_lock()
            try:
                # If the module is not loaded, try to load it
                if not name in sys.modules:
                    # Find module on disk and try to load - slow!
                    fp, path, info = imp.find_module('plugin', [self.data_dir])
                    try:
                        # Load the module and set in sys.modules             
                        module = imp.load_module(name, fp, path, info)
                        sys.modules[self.siteid].plugin = module
                    finally:
                        # Make sure fp is closed properly
                        if fp:
                            fp.close()
            finally:
                release_lock()
        except ImportError, err:
            msg = '''
Could not import plugin package from "%(path)s" because of ImportError:
%(err)s.

Make sure your data directory path is correct, check permissions, and
that the data/plugin directory has an __init__.py file.
''' % {'path': self.data_dir, 'err': str(err)}
            raise error.ConfigurationError(msg)
            
    def __getitem__(self, item):
        """ Make it possible to access a config object like a dict """
        return getattr(self, item)
    
# remove the gettext pseudo function 
del _


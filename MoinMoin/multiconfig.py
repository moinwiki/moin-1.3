# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Multiple config handler
    and
    MoinMoin - Configuration defaults class

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, os, sys

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
    """ Make and return config object

    If the config file is not found or broken, either because of a typo
    in farmconfig or deleted file or some other error, we return a
    default config, and a warning.

    The default config works with a default installed wiki. If the wiki
    is installed using different url_prefix and other settings, it might
    not work, because other code does not do proper error checking.
    
    This is the behavior of moin up to version 1.2

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
                # Config found, return config instance
                cfg = Config()
                cfg.siteid = name
                return cfg
            else:
                # Broken config file, probably old config from 1.2
                err = 'could not find a "Config" class in "%s.py"; ' \
                      'default configuration used instead.' % (name)

        except ImportError, why:
            # Broken config file, probably indent problem
            err = 'import of config "%s" failed due to "%s"; ' \
                  'default configuration used instead.' % (name, why)
    else:
        # Missing config file, or error in farmconfig.py 
        err = 'could not find a config file for url: %s; ' \
              'default configuration used instead.' % (url)

    # Warn and return a default config
    import warnings
    warnings.warn(err)
    return DefaultConfig()


# This is a way to mark some text for the gettext tools so that they don't
# get orphaned. See http://www.python.org/doc/current/lib/node278.html.
def _(text): return text


class DefaultConfig:
    """ default config values

    FIXME: update according to MoinMoin:UpdateConfiguration
    """    
    acl_enabled = 0
    acl_rights_default = "Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write"
    acl_rights_before = ""
    acl_rights_after = ""
    acl_rights_valid = ['read', 'write', 'delete', 'revert', 'admin']
    allow_extended_names = 1
    allow_numeric_entities = 1
    allowed_actions = []
    allow_xslt = 0
    attachments = None # {'dir': path, 'url': url-prefix}
    auth_http_enabled = 0
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
    data_dir = './wiki/data/'
    data_underlay_dir = './wiki/underlay/'
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

    interwikiname = None
    mail_login = None # or "user pwd" if you need to use SMTP AUTH
    mail_smarthost = None
    mail_from = None
    navi_bar = [ u'%(page_front_page)s', u'RecentChanges', u'FindPage', u'HelpContents', ]
    nonexist_qm = 0

    page_credits = [
        '<a href="http://moinmoin.wikiwikiweb.de/">MoinMoin Powered</a>',
        '<a href="http://www.python.org/">Python Powered</a>',
        '''<a href="http://validator.w3.org/check?uri=referer"><img
  src="http://www.w3.org/Icons/valid-html401"
  alt="Valid HTML 4.01!" height="20" width="52"></a>''',
        ]
    page_footer1 = ''
    page_footer2 = ''

    page_header1 = ''
    page_header2 = ''
    
    page_front_page = 'FrontPage'
    page_local_spelling_words = 'LocalSpellingWords'
    page_category_regex = '^Category[A-Z]'
    page_dict_regex = '[a-z]Dict$'
    page_form_regex = '[a-z]Form$'
    page_group_regex = '[a-z]Group$'
    page_template_regex = '[a-z]Template$'

    page_license_enabled = 0
    page_license_page = 'WikiLicense'

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
    ua_spiders = ('archiver|crawler|curl|google|htdig|httrack|jeeves|larbin|leech|'
                  'linkbot|linkmap|linkwalk|mercator|mirror|nutbot|robot|scooter|'
                  'search|sitecheck|spider|wget')

    # Wiki identity
    sitename = 'Untitled Wiki'
    url_prefix = '/wiki'
    logo_string = None
    
    url_mappings = {}
    SecurityPolicy = None

    def __init__(self):
        """ Init Config instance """
        if self.config_check_enabled:
            self._config_check()

        # Decode certain names that allow unicode values
        # wikiconfig is utf-8, internal config are Unicode
        self._decode()

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
        """       
        unknown = ['"%s"' % name for name in dir(self)
                  if not name.startswith('_') and 
                  not DefaultConfig.__dict__.has_key(name) and
                  not isinstance(getattr(self, name), (type(sys), type(DefaultConfig)))]
        if unknown:
            msg = ("Warning: unknown config options: %s. Please check your "
                   "configuration for typos before requesting support or "
                   "reporting a bug.\n") % ', '.join(unknown)
            import warnings
            warnings.warn(msg)

    def _decode(self):
        """ Decode certain values from utf-8, preserve unicode values """
        decode_names = ('sitename', 'logo_string', 'page_category_regex',
                        'page_dict_regex', 'page_form_regex', 'page_group_regex',
                        'page_template_regex', 'navi_bar', 'page_front_page')
        for name in decode_names:
            attr = getattr(self, name, None)
            if attr:
                if isinstance(attr, str):
                    setattr(self, name, unicode(attr, 'utf-8'))
                elif isinstance(attr, list):
                    for i in xrange(len(attr)):
                        name = attr[i]
                        if isinstance(name, str):
                            attr[i] = unicode(name, 'utf-8')
                        
    def __getitem__(self, item):
        """ Make it possible to access a config object like a dict """
        return getattr(self, item)
    
# remove the gettext pseudo function 
del _


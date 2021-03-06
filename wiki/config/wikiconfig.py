# -*- coding: iso-8859-1 -*-
# IMPORTANT! This encoding (charset) setting MUST be correct! If you live in a
# western country and you don't know that you use utf-8, you probably want to
# use iso-8859-1 (or some other iso charset). If you use utf-8 (a Unicode
# encoding) you MUST use: coding: utf-8
# That setting must match the encoding your editor uses when you modify the
# settings below. If it does not, special non-ASCII chars will be wrong.

"""
    MoinMoin - Configuration for a single wiki

    If you run a single wiki only, you can omit the farmconfig.py config
    file and just use wikiconfig.py - it will be used for every request
    we get in that case.

    Note that there are more config options than you'll find in
    the version of this file that is installed by default; see
    the module MoinMoin.multiconfig for a full list of names and their
    default values.

    Also, the URL http://moinmoin.wikiwikiweb.de/HelpOnConfiguration has
    a list of config options.

    @copyright: 2000-2005 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.multiconfig import DefaultConfig


class Config(DefaultConfig):

    # Wiki identity ----------------------------------------------------

    # Site name, used by default for wiki name-logo [Unicode]
    sitename = u'Untitled Wiki'

    # Wiki logo. You can use an image, text or both. [Unicode]
    # Example: u'<img src="/wiki/mywiki.png" alt="My Wiki">My Wiki'
    # For no logo or text, use ''
    logo_string = sitename

    # The interwiki name used in interwiki links
    interwikiname = None


    # Critical setup  ---------------------------------------------------

    # Misconfiguration here will render your wiki unusable. Check that
    # all directories are accessible by the web server or moin server.

    # If you encounter problems, try to set data_dir and data_underlay_dir
    # to absolute paths.

    # Where your mutable wiki pages are. You want to make regular
    # backups of this directory.
    data_dir = './data/'

    # Where read-only system and help page are. You might want to share
    # this directory between several wikis. When you update MoinMoin,
    # you can safely replace the underlay directory with a new one. This
    # directory is part of MoinMoin distribution, you don't have to
    # backup it.
    data_underlay_dir = './underlay/'

    # This must be '/wiki' for twisted and standalone. For CGI, it should
    # match your Apache Alias setting.
    url_prefix = '/wiki'
    

    # Security ----------------------------------------------------------

    # Security critical actions (disabled by default)
    # Uncomment to enable options you like.
    #allowed_actions = ['DeletePage', 'AttachFile', 'RenamePage']
    
    # Enable acl (0 to disable)
    acl_enabled = 1    

    # IMPORTANT: grant yourself admin rights! replace YourName with
    # your user name. See HelpOnAccessControlLists for more help.
    # All acl_rights_xxx options must use unicode [Unicode]
    #acl_rights_before = u"YourName:read,write,delete,revert,admin"
    
    # Link spam protection for public wikis (Uncomment to enable)
    # Needs a reliable internet connection.
    #from MoinMoin.util.antispam import SecurityPolicy


    # Mail --------------------------------------------------------------
    
    # Configure to enable subscribing to pages (disabled by default)
    # or sending forgotten passwords.

    # SMTP server, e.g. "mail.provider.com" (empty or None to disable mail)
    mail_smarthost = ""

    # The return address, e.g "My Wiki <noreply@mywiki.org>"
    mail_from = ""

    # "user pwd" if you need to use SMTP AUTH
    mail_login = ""


    # User interface ----------------------------------------------------
    
    # Add your wikis important pages at the end. It is not recommended to
    # remove the default links.  Leave room for user links - don't use
    # more than 6 short items.
    # You MUST use Unicode strings here, but you need not use localized
    # page names for system and help pages, those will be used automatically
    # according to the user selected language. [Unicode]
    navi_bar = [
        # Will use page_front_page, (default FrontPage)
        u'%(page_front_page)s',
        u'RecentChanges',
        u'FindPage',
        u'HelpContents',
    ]

    # The default theme anonymous or new users get
    theme_default = 'modern'
    

    # Language options --------------------------------------------------

    # See http://moinmoin.wikiwikiweb.de/ConfigMarket for configuration in 
    # YOUR language that other people contributed.

    # The main wiki language, set the direction of the wiki pages
    default_lang = 'en'

    # You must use Unicode strings here [Unicode]
    page_category_regex = u'^Category[A-Z]'
    page_dict_regex = u'[a-z]Dict$'
    page_form_regex = u'[a-z]Form$'
    page_group_regex = u'[a-z]Group$'
    page_template_regex = u'[a-z]Template$'

    # Content options ---------------------------------------------------

    # Show users hostnames in RecentChanges
    show_hosts = 1                  

    # Enumerate headlines?
    show_section_numbers = 0

    # Charts size, require gdchart (Set to None to disable).
    chart_options = {'width': 600, 'height': 300}   



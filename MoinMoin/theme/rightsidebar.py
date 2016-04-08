# -*- coding: iso-8859-1 -*-
"""
    MoinMoin theme by and for crw.
"""

from MoinMoin import config, wikiutil
from MoinMoin.Page import Page
from MoinMoin.theme.classic import Theme as ThemeBase

class Theme(ThemeBase):
    """ here are the functions generating the html responsible for
        the look and feel of your wiki site
    """

    name = "rightsidebar"

    stylesheets_print = (
        # theme charset         media       basename
        (name,  'iso-8859-1',   'all',      'common'),
        (name,  'iso-8859-1',   'all',      'print'),
        )
    
    stylesheets_projection = (
        # theme charset         media       basename
        (name,  'iso-8859-1',   'all',      'common'),
        (name,  'iso-8859-1',   'all',      'projection'),
        )
    
    stylesheets = (
        # theme charset         media       basename
        (name,  'iso-8859-1',   'all',      'common'),
        (name,  'iso-8859-1',   'screen',   'screen'),
        (name,  'iso-8859-1',   'print',    'print'),
        (name,  'iso-8859-1',   'projection',    'projection'),
        )

    # Header stuff #######################################################

    def banner(self,d):
        """
        Assemble the banner

        @rtype: string
        @return: banner html
        """
        # 'banner_html': self.emit_custom_html('<div id="banner">\n<a id="bannertext" href="http://cwhipple.info">cwhipple.info</a>\n<p id="desctext">an evolving repository</p>\n</div>\n')
        html ='<div id="banner">\n<a id="bannertext" href="%(q_page_front_page)s">%(site_name)s</a>\n</div>\n' % d
        return html

    def title(self, d):
        """
        Assemble the title
        
        @param d: parameter dictionary
        @rtype: string
        @return: title html
        """
        _ = self.request.getText
        html = ['<div id="title">']
        if d['title_link']:
            html.append('<h1>&gt; <a title="%s" href="%s">%s</a></h1>' % (
                _('Click here to do a full-text search for this title'),
                d['title_link'],
                wikiutil.escape(d['title_text'])))
        else:
            html.append('<h1>%s</h1>' % wikiutil.escape(d['title_text']))
        html.append('</div>')
        return ''.join(html)

    def username(self, d):
        """
        Assemble the username / userprefs link
        
        @param d: parameter dictionary
        @rtype: string
        @return: username html
        """
        _ = self.request.getText
        html = ['<div class="sidetitle">%s</div>\n' % _("User")]
        if self.request.user.valid:
            html.append('<div class="user">') 
            html.append('%s' % wikiutil.link_tag(self.request, wikiutil.quoteWikiname(self.request.user.name), wikiutil.escape(self.request.user.name)))
            html.append('<br />')
            html.append('%s' % wikiutil.link_tag(self.request, wikiutil.quoteWikiname(d['page_user_prefs']), d['page_user_prefs']))
            html.append('<br /><br />')
            html.append('<form action="%s/%s" method="POST">' % (d['script_name'], d['q_page_user_prefs']))
            html.append('<input type="hidden" name="action" value="userform">')
            html.append('<input type="hidden" name="logout" value="Logout">')
            #html.append('<input type="image" name="Submit" value="Submit" src="http://cwhipple.info/crwiki/crw/img/logout.png" height="15" width="80" border="0">')
            html.append('<input type="image" name="Submit" value="Submit" src="%s" height="15" width="80" border="0">' % self.img_url('logout.png'))
            html.append('</form></div>')
        else:
            html.append('<div class="user">%s</div>' % wikiutil.link_tag(
                self.request, wikiutil.quoteWikiname(d['page_user_prefs']),
                wikiutil.escape(d['user_prefs'])))
        return ''.join(html)

    def navibar(self, d):
        """
        Assemble the navibar
        
        @param d: parameter dictionary
        @rtype: string
        @return: navibar html
        """
        _ = self.request.getText
        html = []
        html.append('<div class="sidetitle">%s</div>\n' % _("Site"))
        html.append('<ul id="navibar">\n')
        if d['navibar']:
            # Print site name in first field of navibar
            # html.append(('<li>%(site_name)s</li>\n') % d)
            for (link, navi_link) in d['navibar']:
                html.append((
                    '<li><a href="%(link)s">%(navi_link)s</a></li>\n') % {
                        'link': link,
                        'navi_link': navi_link,
                    })
        html.append('</ul>')
        return ''.join(html)


    def make_iconlink(self, which, d):
        """
        Make a link with an icon

        @param which: icon id (dictionary key)
        @param d: parameter dictionary
        @rtype: string
        @return: html link tag
        """
        page_params, title, icon = config.page_icons_table[which]
        d['title'] = title % d
        d['i18ntitle'] = self.request.getText(d['title'])
        img_src = self.make_icon(icon, d)
        return wikiutil.link_tag(self.request, page_params % d, d['i18ntitle'], attrs='title="%(title)s"' % d)


    def iconbar(self, d):
        """
        Assemble the iconbar
        
        @param d: parameter dictionary
        @rtype: string
        @return: iconbar html
        """
        _ = self.request.getText
        iconbar = []
        if config.page_iconbar and self.request.user.show_toolbar and d['page_name']:
            iconbar.append('<div class="sidetitle">%s</div>\n' % _("Page"))
            iconbar.append('<ul id="iconbar">\n')
            icons = config.page_iconbar[:]
            for icon in icons:
                if icon == "up":
                    if d['page_parent_page']:
                        iconbar.append('<li>%s</li>\n' % self.make_iconlink(icon, d))
                elif icon == "subscribe":
                    iconbar.append('<li>%s</li>\n' % self.make_iconlink(
                        ["subscribe", "unsubscribe"][self.request.user.isSubscribedTo([d['page_name']])], d))
                elif icon == "home":
                    if d['page_home_page']:
                        iconbar.append('<li>%s</li>\n' % self.make_iconlink(icon, d))
                else:
                    iconbar.append('<li>%s</li>\n' % self.make_iconlink(icon, d))
            iconbar.append('</ul>\n')
        return ''.join(iconbar)

    def trail(self, d):
        """
        Assemble page trail
        
        @param d: parameter dictionary
        @rtype: string
        @return: trail html
        """
        html = []
        if d['trail']:
            pagetrail = d['trail']
            html.append('<ul id="pagetrail">\n')
            for p in pagetrail[:-1]:
                html.append('<li><span>%s</span></li>\n' % (Page(p).link_to(self.request),))
            html.append('<li><span>%s</span></li>\n' % wikiutil.escape(pagetrail[-1]))
            html.append('</ul>\n')
        else:
            html.append('<!-- pagetrail would be here -->\n')
#           html.append('<hr id="pagetrail">\n')
        return ''.join(html)

    def html_head(self, d):
        """
        Assemble html head
        
        @param d: parameter dictionary
        @rtype: string
        @return: html head
        """
        dict = {
            'stylesheets_html': self.html_stylesheets(d),
        }
        dict.update(d)

        html = """
<title>%(sitename)s - %(title)s</title>
%(stylesheets_html)s
""" % dict

        return html

    def header(self, d):
        """
        Assemble page header
        
        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        dict = {
            'config_header1_html': self.emit_custom_html(config.page_header1),
            'config_header2_html': self.emit_custom_html(config.page_header2),
            # 'logo_html':  self.logo(d),
            'banner_html': self.banner(d),
            'title_html':  self.title(d),
    	    'username_html':  self.username(d),
            'navibar_html': self.navibar(d),
            'iconbar_html': self.iconbar(d),
            'msg_html': self.msg(d),
            'available_actions_html': self.availableactions(d),
            'search_form_html': self.searchform(d),
        }
        dict.update(d)

# %(logo_html)s ### from...
        html = """
%(config_header1_html)s
%(banner_html)s
%(title_html)s
%(config_header2_html)s
%(msg_html)s
<div id="sidebar">
%(username_html)s
%(navibar_html)s
%(iconbar_html)s
%(available_actions_html)s
%(search_form_html)s
</div>
""" % dict

        # Next parts will use config.default_lang direction, as set in the <body>
        return html

    # Footer stuff #######################################################
    
    def searchform(self, d):
        """
        assemble HTML code for the search forms
        
        @param d: parameter dictionary
        @rtype: string
        @return: search form html
        """
        _ = self.request.getText
        sitenav_pagename = wikiutil.getSysPage(self.request, 'SiteNavigation').page_name
        dict = {
            'search_title': _("Search"),
            'search_html': _("Title: %(titlesearch)s<br/>Text: %(textsearch)s") % d,
        }
        dict.update(d)
        
        html = """
<div class="sidetitle">%(search_title)s</div>
<div id="search">
<form method="POST" action="%(script_name)s/%(q_page_name)s">
<p>
<input type="hidden" name="action" value="inlinesearch">
<input type="hidden" name="context" value="40">
%(search_html)s
</p>
</form>
</div>
""" % dict

        return html

    def availableactions(self, d):    
        """
        assemble HTML code for the available actions
        
        @param d: parameter dictionary
        @rtype: string
        @return: available actions html
        """
        _ = self.request.getText
        html = []
        html.append('<div class="sidetitle">%s</div>\n' % _("Actions"))
        html.append('<ul id="actions">\n')
        for action in d['available_actions']:
            html.append("<li>%s</li>\n" % (
                wikiutil.link_tag(self.request, '%s?action=%s' % (d['q_page_name'], action), action)
            ))
        html.append('</ul>')
        return ''.join(html)

    def footer(self, d, **keywords):
        """
        Assemble page footer
        
        @param d: parameter dictionary
        @keyword ...:...
        @rtype: string
        @return: page footer html
        """
        dict = {
            'config_page_footer1_html': self.emit_custom_html(config.page_footer1),
            'config_page_footer2_html': self.emit_custom_html(config.page_footer2),
            'showtext_html': self.showtext_link(d, **keywords),
            'edittext_html': self.edittext_link(d, **keywords),
            'version_html': self.showversion(d, **keywords),
            'footer_fragments_html': self.footer_fragments(d, **keywords),
        }
        dict.update(d)
        
        html = """
<div id="footer">
%(config_page_footer1_html)s
%(showtext_html)s
%(footer_fragments_html)s
%(edittext_html)s
%(config_page_footer2_html)s
</div>
%(version_html)s
""" % dict

        return html

def execute(request):
    """
    Generate and return a theme object
        
    @param request: the request object
    @rtype: MoinTheme
    @return: Theme object
    """
    return Theme(request)


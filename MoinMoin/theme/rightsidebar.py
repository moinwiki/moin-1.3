# -*- coding: iso-8859-1 -*-
"""
    MoinMoin theme by and for crw.
"""

from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.theme import ThemeBase

class Theme(ThemeBase):
    """ here are the functions generating the html responsible for
        the look and feel of your wiki site
    """

    name = "rightsidebar"

    def wikipanel(self, d):
        """ Create wiki panel """
        _ = self.request.getText
        html = [
            u'<div class="sidepanel">',
            u'<h1>%s</h1>' % _("Wiki"),
            self.navibar(d),
            u'</div>',
            ]
        return u'\n'.join(html)
    
    def pagepanel(self, d):
        """ Create page panel """
        _ = self.request.getText
        if self.shouldShowEditbar(d['page']):
            html = [
                u'<div class="sidepanel">',
                u'<h1>%s</h1>' % _("Page"),
                self.editbar(d),
                u'</div>',
                ]
            return u'\n'.join(html)
        return ''   
        
    def userpanel(self, d):
        """ Create user panel """
        _ = self.request.getText

        trail = self.trail(d)
        if trail:
            trail = u'<h2>%s</h2>\n' % _("Trail") + trail

        html = [
            u'<div class="sidepanel">',
            u'<h1>%s</h1>' %  _("User"),
            self.username(d),
            trail,
            u'</div>'
            ]
        return u'\n'.join(html)

    def header(self, d):
        """
        Assemble page header
        
        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        _ = self.request.getText

        html = [
            # Custom html above header
            self.emit_custom_html(self.cfg.page_header1),

            # Hedar
            u'<div id="header">',
            self.searchform(d),
            self.logo(),
            u'</div>',
            
            # Custom html below header (not recomended!)
            self.emit_custom_html(self.cfg.page_header2),

            # Sidebar
            u'<div id="sidebar">',
            self.wikipanel(d),
            self.pagepanel(d),
            self.userpanel(d),
            self.credits(d),
            u'</div>',

            self.msg(d),
            
            # Page
            self.startPage(),
            self.title(d),
            ]
        return u'\n'.join(html)
    
    def footer(self, d, **keywords):
        """ Assemble page footer
        
        @param d: parameter dictionary
        @keyword ...:...
        @rtype: string
        @return: page footer html
        """
        page = d['page']
        html = [
            # Page end
            # Used to extend the page to the bottom of the sidebar
            u'<div id="pagebottom"></div>',
            self.pageinfo(page),
            self.endPage(),
            
            # Custom html above footer
            self.emit_custom_html(self.cfg.page_footer1),
            
            # And bellow
            self.emit_custom_html(self.cfg.page_footer2),
            ]
        return u'\n'.join(html)


def execute(request):
    """
    Generate and return a theme object
        
    @param request: the request object
    @rtype: MoinTheme
    @return: Theme object
    """
    return Theme(request)


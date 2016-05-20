# -*- coding: iso-8859-1 -*-
"""
    MoinMoin classic theme

    This class can also be used as base class for other themes -
    if you make an empty child class, you will get classic behaviour.

    If you want modified behaviour, just override the stuff you
    want to change in the child class.

    @copyright: 2003 by ThomasWaldmann (LinuxWiki:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import i18n, wikiutil, version
from MoinMoin.theme import ThemeBase
from MoinMoin.Page import Page


class Theme(ThemeBase):
    """ here are the functions generating the html responsible for
        the look and feel of your wiki site
    """
    
    name = "classic"

    def iconbar(self, d):
        """
        Assemble the iconbar
        
        @param d: parameter dictionary
        @rtype: string
        @return: iconbar html
        """
        iconbar = []
        if self.cfg.page_iconbar and self.request.user.show_toolbar and d['page_name']:
            iconbar.append('<ul id="iconbar">\n')
            icons = self.cfg.page_iconbar[:]
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
    
    def header(self, d):
        """
        Assemble page header
        
        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        dict = {
            'config_header1_html': self.emit_custom_html(self.cfg.page_header1),
            'config_header2_html': self.emit_custom_html(self.cfg.page_header2),
            'search_form_html': self.searchform(d),
            'logo_html':  self.logo(),
            'title_html':  self.title(d),
            'username_html':  self.username(d),
            'navibar_html': self.navibar(d),
            'iconbar_html': self.iconbar(d),
            'msg_html': self.msg(d),
            'trail_html': self.trail(d),
            'startpage_html': self.startPage(),
        }
        dict.update(d)

        html = """
%(config_header1_html)s

%(search_form_html)s
%(username_html)s
%(logo_html)s
%(title_html)s
%(trail_html)s
%(iconbar_html)s
%(navibar_html)s
%(msg_html)s

%(config_header2_html)s

%(startpage_html)s
""" % dict
        return html

    # Footer stuff #######################################################
    
    def edittext_link(self, d, **keywords):
        """
        Assemble EditText link (or indication that page cannot be edited)
        
        @param d: parameter dictionary
        @rtype: string
        @return: edittext link html
        """
        _ = self.request.getText
        page = d['page']
        if keywords.get('editable', 1):

            # Add edit link
            editable = (self.request.user.may.write(d['page_name']) and
                        page.isWritable())
            if editable:
                title = _('EditText', formatted=False)
                edit = wikiutil.link_tag(self.request, d['q_page_name'] +
                                         '?action=edit', title)
            else:
                edit = _('Immutable page')

            # Add last edit info
            info = page.lastEditInfo()
            if info:
                if info.get('editor'):
                    info = _("last edited %(time)s by %(editor)s") % info
                else:
                    info = _("last modified %(time)s") % info
                return '<p>%s (%s)</p>' % (edit, info)
        return ''

    def footer_fragments(self, d, **keywords):
        """
        assemble HTML code fragments added by the page formatters
        
        @param d: parameter dictionary
        @rtype: string
        @return: footer fragments html
        """
        html = ''
        if d['footer_fragments']:
            html = ''.join(d['footer_fragments'].values())
        return html

    def availableactions(self, d):    
        """
        assemble HTML code for the available actions
        
        @param d: parameter dictionary
        @rtype: string
        @return: available actions html
        """
        request = self.request
        _ = request.getText
        html = ''
        available = request.getAvailableActions(d['page'])
        if available:
            available = available.keys()
            available.sort()
            html = []
            for action in available:
                # Always add spaces: AttachFile -> Attach File 
                # XXX TODO do not make a page object just for split_title
                title = Page(request, action).split_title(request, force=1)
                # Use translated version if available
                title = _(title, formatted=False)
                params = '%s?action=%s' % (d['q_page_name'], action)
                link = wikiutil.link_tag(request, params, title)
                html.append(link)
                
            html = u'<p>%s %s</p>\n' % (_('Or try one of these actions:'),
                                       u', '.join(html))
        return html
    
    def footer(self, d, **keywords):
        """
        Assemble page footer
        
        @param d: parameter dictionary
        @keyword ...:...
        @rtype: string
        @return: page footer html
        """
        dict = {
            'config_page_footer1_html': self.emit_custom_html(self.cfg.page_footer1),
            'config_page_footer2_html': self.emit_custom_html(self.cfg.page_footer2),
            'edittext_html': self.edittext_link(d, **keywords),
            'available_actions_html': self.availableactions(d),
            'credits_html': self.credits(d, **keywords),
            'version_html': self.showversion(d, **keywords),
            'footer_fragments_html': self.footer_fragments(d, **keywords),
            'endpage_html': self.endPage(),
        }
        dict.update(d)
        
        html = """
%(endpage_html)s

%(config_page_footer1_html)s

<div id="footer">
%(footer_fragments_html)s
%(edittext_html)s
%(available_actions_html)s
</div>
%(credits_html)s
%(version_html)s

%(config_page_footer2_html)s
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


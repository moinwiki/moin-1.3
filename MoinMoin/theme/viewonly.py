# -*- coding: iso-8859-1 -*-
"""
    MoinMoin viewonly theme

    This is a theme intended for use on web sites that should not show wiki
    features to the public. So you can choose this as theme_default, while
    the site editors use another (normal) theme for updating the site via
    wiki functionality.

    This theme inherits most from classic theme, so if you change there,
    this theme will change, too.
    
    @copyright: 2004 by ThomasWaldmann (LinuxWiki:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""

import urllib
from MoinMoin import config, i18n, wikiutil, version
from MoinMoin.Page import Page
from classic import Theme as ThemeBase

class Theme(ThemeBase):

    name = "viewonly"
    icons_from = "classic"

    stylesheets = ThemeBase.stylesheets + (
        # theme charset         media       basename
        (name,  'iso-8859-1',   'screen',   'screen'),
    )

    def img_url(self, img):
        """
        generate an img url

        @param img: the image filename
        @rtype: string
        @return: the image url
        """
        return "%s/%s/img/%s" % (config.url_prefix, self.icons_from, img)

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
            'logo_html':  self.logo(d),
            'title_html':  self.title(d),
            'username_html': '',
            'navibar_html': self.navibar(d),
            'iconbar_html': '',
            'msg_html': self.msg(d),
            'trail_html': '<hr id="trail">'
        }
        dict.update(d)

        html = """
%(config_header1_html)s
%(logo_html)s
%(username_html)s
%(title_html)s
%(iconbar_html)s
%(trail_html)s
%(config_header2_html)s
%(msg_html)s
%(navibar_html)s
""" % dict

        # Next parts will use config.default_lang direction, as set in the <body>
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
        html = []
        html.append('<p>')
        if keywords.get('editable', 1):
            editable = self.request.user.may.edit(d['page_name']) and d['page'].isWritable()
            if editable:
                html.append("%s %s" % (
                    wikiutil.link_tag(self.request, d['q_page_name']+'?action=edit', _('EditText')),
                    _('of this page'),
                ))
            else:
                html.append("%s" % _('Immutable page'))
            html.append(' %(last_edit_info)s' % d)
            html.append('</p>')
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
            'showtext_html': '',
            'edittext_html': self.edittext_link(d, **keywords),
            'search_form_html': self.searchform(d),
            'available_actions_html': '',
            'credits_html': self.emit_custom_html(config.page_credits),
            'version_html': '',
            'footer_fragments_html': '',
        }
        dict.update(d)
        
        html = """
<div id="footer">
<div id="credits">
%(credits_html)s
</div>
%(config_page_footer1_html)s
%(showtext_html)s
%(footer_fragments_html)s
%(search_form_html)s
%(edittext_html)s
%(available_actions_html)s
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


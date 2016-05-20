# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create an action link

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ["language"]
from MoinMoin import wikiutil

def execute(self, args):
    # look for template pages
    templates = filter(lambda page, u = wikiutil: u.isTemplatePage(self.request, page),
        self.request.rootpage.getPageList())
    if templates:
        templates.sort()
                                                                                                                  
        # send list of template pages
        result = self.formatter.bullet_list(1)
        for page in templates:
            result = result +\
                     self.formatter.listitem(1) +\
                     wikiutil.link_tag(self.request, "%s?action=edit&amp;template=%s" % (
                        wikiutil.quoteWikinameURL(self.formatter.page.page_name),
                        wikiutil.quoteWikinameURL(page)), page
                     ) + \
                     self.formatter.listitem(0)

        result = result + self.formatter.bullet_list(0)
        return result
    else:
        return ''

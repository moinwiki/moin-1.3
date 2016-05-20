"""
newpage action

Create a new page with optional template. Can be used with NewPage.py macro.

@copyright: 2004 Vito Miliano (vito_moinnewpagewithtemplate@perilith.com)
@copyright: 2004 by Nir Soffer <nirs@freeshell.org>
@copyright: 2004 Alexander Schremmer <alex AT alexanderweb DOT de>
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import MoinMoinNoFooter
from MoinMoin.Page import Page

class NewPage:
    """ Open editor for a new page, using template """

    def __init__(self, request, referrer):
        self.request = request
        self.referrer = referrer # The page the user came from
        self.pagename = self.request.form.get('pagename', [None])[0]

    def checkArguments(self):
        """ Check arguments in form, return error msg

        @rtype: unicode
        @return: error message
        """
        _ = self.request.getText
        if not self.pagename:
            return _("Cannot create a new page without a page name."
                     "  Please specify a page name.")
        return ''
        
    def checkPermissions(self):
        """ Check write permission in form, return error msg

        @rtype: unicode
        @return: error message
        """
        _ = self.request.getText
        page = Page(self.request, self.pagename)
        if not page.isWritable() and self.request.user.may.read(self.pagename):
            # Same error as the edit page for localization reasons
            return _('You are not allowed to edit this page.')
        return ''

    def render(self):
        """ Redirect to the new page, using edit action and template """
        
        error = self.checkArguments() or self.checkPermissions()
        if error:
            # Send back to the page you came from, with an error msg
            page = Page(self.request, self.referrer)
            page.send_page(self.request, msg=error)
        else:
            # Redirect to new page using edit action. No error checking
            # is needed because it is done later in new request.
            pagename = self.pagename
            query = {'action': 'edit', 'backto': self.referrer}

            template = self.request.form.get('template', [''])[0]
            if template:
                from MoinMoin.wikiutil import quoteWikinameURL
                query['template'] = quoteWikinameURL(template)

            parent = self.request.form.get('parent', [''])[0]
            if parent:
                pagename = "%s/%s" % (parent, pagename)

            url = Page(self.request, pagename).url(self.request, query, 0)
            self.request.http_redirect(url)
            raise MoinMoinNoFooter

        return ''

def execute(pagename, request):
    """ Temporary glue code for current moin action system """
    return NewPage(request, pagename).render()


"""
    MoinMoin - DeletePage action

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action allows you to delete a page. Note that the standard
    config lists this action as excluded!

    $Id: DeletePage.py,v 1.15 2002/05/07 17:05:22 jhermann Exp $
"""

# Imports
import string
from MoinMoin import config, user, webapi, wikiutil
from MoinMoin.PageEditor import PageEditor
from MoinMoin.i18n import _


def execute(pagename, request):
    actname = string.split(__name__, '.')[-1]
    page = PageEditor(pagename)

    # be extra paranoid in dangerous actions
    if actname in config.excluded_actions \
            or not request.user.may.edit \
            or not request.user.may.delete:
        return page.send_page(request,
            msg='<strong>%s</strong>' %
                _('You are not allowed to delete pages in this wiki!'))


    # check whether page exists at all
    if not page.exists():
        return page.send_page(request,
            msg='<strong>%s</strong>' %
                _('This page is already deleted or was never created!'))

    # check whether the user clicked the delete button
    if request.form.has_key('button') and request.form.has_key('ticket'):
        # check whether this is a valid deletion request (make outside
        # attacks harder by requiring two full HTTP transactions)
        if not _checkTicket(request.form['ticket'].value):
            return page.send_page(request,
                msg='<strong>%s</strong>' %
                    _('Please use the interactive user interface to delete pages!'))

        # Delete the page
        page.deletePage(request, request.form.getvalue('comment'))

        # Redirect to RecentChanges
        return wikiutil.getSysPage('RecentChanges').send_page(request,
                msg='<strong>%s</strong>' %
                    (_('Page "%s" was sucessfully deleted!') % (pagename,)))

    # send deletion form
    wikiname = wikiutil.quoteWikiname(pagename)
    ticket = _createTicket()
    querytext = _('Really delete this page?')
    button = _(' Delete ')
    comment_label = _("Optional reason for the deletion")
    formhtml = """
<form method="GET" action="%(wikiname)s">
<strong>%(querytext)s</strong>
<input type="hidden" name="action" value="%(actname)s">
<input type="hidden" name="ticket" value="%(ticket)s">
<input type="submit" name="button" value="%(button)s">
<p>
%(comment_label)s<br>
<input type="text" name="comment" size="60" maxlength="60">
</form>""" % locals()

    return page.send_page(request, msg=formhtml)


def _createTicket(tm = None):
    """Create a ticket using a site-specific secret (the config)"""
    import sha, time, types
    ticket = (tm or "%010x" % time.time())
    digest = sha.new()
    digest.update(ticket)

    cfgvars = vars(config)
    for var in cfgvars.values():
        if type(var) is types.StringType:
            digest.update(repr(var))

    return ticket + '.' + digest.hexdigest()


def _checkTicket(ticket):
    """Check validity of a previously created ticket"""
    timestamp = string.split(ticket, '.')[0]
    ourticket = _createTicket(timestamp)
    return ticket == ourticket


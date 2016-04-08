"""
    MoinMoin - RenamePage action

    This action allows you to rename a page.

    Based on the DeletePage action by Jürgen Hermann <jh@web.de>

    @copyright: 2002-2004 Michael Reinsch <mr@uue.org>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
from MoinMoin import config, user, wikiutil
from MoinMoin.PageEditor import PageEditor

def execute(pagename, request):
    _ = request.getText
    actname = __name__.split('.')[-1]
    page = PageEditor(pagename, request)
    msg = ''

    # be extra paranoid in dangerous actions
    if actname in config.excluded_actions or \
        not request.user.may.edit(pagename) or not request.user.may.delete(pagename):
            msg = _('You are not allowed to rename pages in this wiki!')

    # check whether page exists at all
    elif not page.exists():
        msg = _('This page is already deleted or was never created!')

    # check whether the user clicked the delete button
    elif request.form.has_key('button') and \
        request.form.has_key('newpagename') and request.form.has_key('ticket'):
        # check whether this is a valid renaming request (make outside
        # attacks harder by requiring two full HTTP transactions)
        if not _checkTicket(request.form['ticket'][0]):
            msg = _('Please use the interactive user interface to rename pages!')
        else:
            comment = request.form.get('comment', [''])[0]
            newpagename = request.form.get('newpagename')[0]
            newpage = PageEditor(newpagename, request)

            # check whether a page with the new name already exists
            if newpage.exists():
                msg = _('A page with the name "%s" already exists!') % (newpagename,)
            else:
                # read content of old page and save in new page
                savetext = page.get_raw_body()
                datestamp = '0'
                savemsg = newpage.saveText(savetext, datestamp, stripspaces=0, notify=1, comment=comment)

                # Delete the old page
                page.deletePage(comment)

                msg = _('Page "%s" was successfully renamed to "%s"!') % (pagename,newpagename)

    else:
        # send renamepage form
        url = page.url(request)
        ticket = _createTicket()
        button = _('Rename')
        newname_label = _("New name")
        comment_label = _("Optional reason for the renaming")
        msg = """
<form method="GET" action="%(url)s">
<input type="hidden" name="action" value="%(actname)s">
<input type="hidden" name="ticket" value="%(ticket)s">
%(newname_label)s <input type="text" name="newpagename" size="20" value="%(pagename)s">
<input type="submit" name="button" value="%(button)s">
<p>
%(comment_label)s<br>
<input type="text" name="comment" size="60" maxlength="80">
</p>
</form>""" % locals()

    return page.send_page(request, msg)


def _createTicket(tm = None):
    """Create a ticket using a site-specific secret (the config)"""
    import sha, time, types
    ticket = tm or "%010x" % time.time()
    digest = sha.new()
    digest.update(ticket)

    cfgvars = vars(config)
    for var in cfgvars.values():
        if type(var) is types.StringType:
            digest.update(repr(var))

    return "%s.%s" % (ticket, digest.hexdigest())


def _checkTicket(ticket):
    """Check validity of a previously created ticket"""
    timestamp = ticket.split('.')[0]
    ourticket = _createTicket(timestamp)
    return ticket == ourticket


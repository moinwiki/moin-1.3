# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Security Interface

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This implements the basic interface for user permissions and
    system policy. If you want to define your own policy, inherit
    from the base class 'Permissions', so that when new permissions
    are defined, you get the defaults.

    Then assign your new class to "SecurityPolicy" in moin_config;
    and I mean the class, not an instance of it!

    $Id: security.py,v 1.14 2003/11/09 21:00:50 thomaswaldmann Exp $
"""

#############################################################################
### Basic Permissions Interface -- most features enabled by default
#############################################################################


class Permissions:
    """ Basic interface for user permissions and system policy.

        Note that you still need to allow some of the related actions, this
        just controls their behaviour, not their activation.
    """

    def __init__(self, user):
        """ Calculate the permissons `user` has.
        """
        # note that request object is in `self.user._request`
        self.user = user
        from MoinMoin.Page import Page
        self.Page = Page

    def read(self, pagename, **kw):
        """ Check whether user may read this page.

            `kw` allows passing more information without breaking user
            policies and is not used currently.
        """
        return self.getACL(pagename).may(self.user.name, "read")

    def edit(self, pagename, **kw):
        """ Check whether user may edit this page.

            `kw` allows passing more information without breaking user
            policies and is not used currently.
        """
        return self.getACL(pagename).may(self.user.name, "write")

    def save(self, editor, newtext, datestamp, **kw):
        """ Check whether user may save a page.

            `editor` is the PageEditor instance, the other arguments are
            those of the `PageEditor.saveText` method.

            The current msg presented to the user ("You are not allowed
            to edit any pages.") is a bit misleading, this will be fixed
            if we add policy-specific msgs.
        """
        return self.edit(editor.page_name)

    def delete(self, pagename, **kw):
        """ Check whether user may delete this page.

            `kw` allows passing more information without breaking user
            policies and is not used currently.
        """
        return self.getACL(pagename).may(self.user.name, "delete")

    def revert(self, pagename, **kw):
        """ Check whether user may revert this page.

            `kw` allows passing more information without breaking user
            policies and is not used currently.
        """
        return self.getACL(pagename).may(self.user.name, "revert")

    def getACL(self, pagename, **kw):
        return self.Page(pagename).getACL(self.user._request)

# make an alias for the default policy
Default = Permissions


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

    $Id: security.py,v 1.3 2002/02/13 21:13:52 jhermann Exp $
"""

#############################################################################
### Basic Permissions Interface -- all features enabled by default
#############################################################################

class Permissions:
    """ Basic interface for user permissions and system policy.
    """

    # allowed to edit pages?
    edit = 1

    # allowed to delete things? (note that you still need to allow the related
    # actions, this just controls their behaviour, not their activation)
    delete = 1

    def __init__(self, user):
        self.user = user

        # example for dynamic permissions: make pages editable only for
        # users that are logged in
        ###self.edit = self.edit and user.valid


# make an alias for the default policy
Default = Permissions


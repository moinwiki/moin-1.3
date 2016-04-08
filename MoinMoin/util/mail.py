# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Helper functions for email stuff

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: mail.py,v 1.7 2003/11/09 21:01:15 thomaswaldmann Exp $
"""

# Imports
import os

_transdict = {"AT": "@", "DOT": ".", "DASH": "-"}


#############################################################################
### Mail
#############################################################################

def sendmail(request, to, subject, text, **kw):
    """ Send a mail to the address(es) in 'to', with the given subject and
        mail body 'text'. Return a tuple of success or error indicator and
        message.

        Set a different "From" address with "mail_from=<email>".
    """
    import smtplib, socket
    from MoinMoin import config

    _ = request.getText

    mail_from = kw.get('mail_from', config.mail_from) or config.mail_from

    try:
        server = smtplib.SMTP(config.mail_smarthost)
        try:
            #server.set_debuglevel(1)
            if config.mail_login:
                user, pwd = config.mail_login.split()
                server.login(user, pwd)
            header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" %(
                mail_from, ', '.join(to), subject)
            server.sendmail(mail_from, to, header + text)
        finally:
            try:
                server.quit()
            except AttributeError:
                # in case the connection failed, SMTP has no "sock" attribute
                pass
    except smtplib.SMTPException, e:
        return (0, str(e))
    except (os.error, socket.error), e:
        return (0, _("Connection to mailserver '%(server)s' failed: %(reason)s") % {
            'server': config.mail_smarthost, 
            'reason': str(e)
        })

    return (1, _("Mail sent OK"))


# code originally by Thomas Waldmann
def decodeSpamSafeEmail(address):
    """ Decode a spam-safe email address in `address` by applying the
        following rules.
    
        Known all-uppercase words and their translation:
            "DOT"   -> "."
            "AT"    -> "@"
            "DASH"  -> "-"

        Any unknown all-uppercase words simply get stripped.
        Use that to make it even harder for spam bots!

        Blanks (spaces) simply get stripped.
    """
    email = []

    # words are separated by blanks
    for word in address.split():
        # is it all-uppercase?
        if word.isalpha() and word == word.upper():
            # strip unknown CAPS words
            word = _transdict.get(word, '')
        email.append(word)

    # return concatenated parts
    return ''.join(email)


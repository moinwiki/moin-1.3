# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Helper functions for email stuff

    @copyright: 2003 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import os

_transdict = {"AT": "@", "DOT": ".", "DASH": "-"}


#############################################################################
### Mail
#############################################################################

def sendmail(request, to, subject, text, **kw):
    """
    Send a mail to the address(es) in 'to', with the given subject and
    mail body 'text'.
    
    Return a tuple of success or error indicator and message.

    Set a different "From" address with "mail_from=<email>".
    @param request: the request object
    @param to: target email address
    @param subject: subject of email
    @param text: email body text
    @rtype: tuple
    @return: (is_ok, msg)
    """
    import smtplib, socket
    from email.MIMEText import MIMEText
    from email.Header import Header
    from email.Utils import formatdate
    from MoinMoin import config

    _ = request.getText
    # should not happen, but who knows ...
    if not config.mail_smarthost:
        return (0, _('''This wiki is not enabled for mail processing. '''
                '''Contact the owner of the wiki, who can either enable email, or remove the "Subscribe" icon.'''))
    mail_from = kw.get('mail_from', config.mail_from) or config.mail_from

    # Create a text/plain message
    msg = MIMEText(text, 'plain', config.charset)
    msg['From'] = mail_from
    msg['To'] = ', '.join(to)
    msg['Subject'] = Header(subject, config.charset)
    msg['Date'] = formatdate()
    
    try:
        server = smtplib.SMTP(config.mail_smarthost)
        try:
            #server.set_debuglevel(1)
            if config.mail_login:
                user, pwd = config.mail_login.split()
                server.login(user, pwd)
            server.sendmail(mail_from, to, msg.as_string())
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


def decodeSpamSafeEmail(address):
    """
    Decode a spam-safe email address in `address` by applying the following rules.
    
    Known all-uppercase words and their translation:
        "DOT"   -> "."
        "AT"    -> "@"
        "DASH"  -> "-"

    Any unknown all-uppercase words simply get stripped.
    Use that to make it even harder for spam bots!

    Blanks (spaces) simply get stripped.
    
    @param address: obfuscated email address string
    @rtype: string
    @return: decoded email address
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


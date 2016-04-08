"""
    MoinMoin - Utility Functions

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: util.py,v 1.20 2001/07/16 21:21:48 jhermann Exp $
"""

# Imports
import os, re, sys


#############################################################################
### XML helper functions
#############################################################################

g_xmlIllegalCharPattern = re.compile('[\x01-\x08\x0B-\x0D\x0E-\x1F\x80-\xFF]')
g_undoUtf8Pattern       = re.compile('\xC2([^\xC2])')
g_cdataCharPattern      = re.compile('[&<\'\"]')
g_textCharPattern       = re.compile('[&<]')
g_charToEntity = {
    '&': '&amp;',
    '<': '&lt;',
    "'": '&apos;',
    '"': '&quot;'
}

def TranslateCDATA(text):
    """
        Convert a string to a CDATA-encoded one
        Copyright (c) 1999-2000 FourThought, http://4suite.com/4DOM
    """
    new_string, num_subst = re.subn(g_undoUtf8Pattern, lambda m: m.group(1), text)
    new_string, num_subst = re.subn(g_cdataCharPattern, lambda m, d=g_charToEntity: d[m.group()], new_string)
    new_string, num_subst = re.subn(g_xmlIllegalCharPattern, lambda m: '&#x%02X;'%ord(m.group()), new_string)
    return new_string

def TranslateText(text):
    """
        Convert a string to a PCDATA-encoded one (do minimal encoding)
        Copyright (c) 1999-2000 FourThought, http://4suite.com/4DOM
    """
    new_string, num_subst = re.subn(g_undoUtf8Pattern, lambda m: m.group(1), text)
    new_string, num_subst = re.subn(g_textCharPattern, lambda m, d=g_charToEntity: d[m.group()], new_string)
    new_string, num_subst = re.subn(g_xmlIllegalCharPattern, lambda m: '&#x%02X;'%ord(m.group()), new_string)
    return new_string


#############################################################################
### Mail
#############################################################################

def sendmail(to, subject, text):
    """ Send a mail to the address(es) in 'to', with the given subject and
        mail body 'text'. Return a success or error message.
    """
    import smtplib
    from MoinMoin import config

    try:
        server = smtplib.SMTP(config.mail_smarthost)
        #server.set_debuglevel(1)
        header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" %(
            config.mail_from, ', '.join(to), subject)
        server.sendmail(config.mail_from, to, header + text)
        server.quit()
    except SMTPException, e:
        return str(e)

    return "Mail sent OK"


#############################################################################
### Misc
#############################################################################

# popen (use win32 version if available)
popen = os.popen
if os.name == "nt":
    try:
        import win32pipe
        popen = win32pipe.popen
    except ImportError:
        pass


def getPackageModules(packagefile):
    pyre = re.compile(r"^([^_].*)\.py$")
    pyfiles = filter(None, map(pyre.match, os.listdir(os.path.dirname(packagefile))))
    modules = map(lambda x: x.group(1), pyfiles)
    modules.sort()
    return modules


def importName(modulename, name):
    """ Import a named object from a module in the context of this function,
        which means you should use fully qualified module paths.

        Return None on failure.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None

    return vars(module)[name]


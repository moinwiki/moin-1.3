"""
    MoinMoin - Utility Functions

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    General helper functions that are not directly wiki related.

    $Id: __init__.py,v 1.1 2002/05/09 18:17:48 jhermann Exp $
"""

# Imports
import os, re, string, time
from MoinMoin.i18n import _


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

def sendmail(to, subject, text, **kw):
    """ Send a mail to the address(es) in 'to', with the given subject and
        mail body 'text'. Return a success or error message.

        Set a different "From" address with "mail_from=<email>".
    """
    import smtplib, socket
    from MoinMoin import config

    try:
        server = smtplib.SMTP(config.mail_smarthost)
        try:
            #server.set_debuglevel(1)
            header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" %(
                config.mail_from, string.join(to, ', '), subject)
            server.sendmail(
                kw.get('mail_from', config.mail_from) or config.mail_from,
                to, header + text)
        finally: 
            server.quit()
    except smtplib.SMTPException, e:
        return str(e)
    except (os.error, socket.error), e:
        return _("Connection to mailserver '%(server)s' failed: %(reason)s") % {
            'server': config.mail_smarthost, 
            'reason': str(e)
        }

    return _("Mail sent OK")


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


def rangelist(numbers):
    """ Convert a list of integers to a range string in the form
        '1,2-5,7'.
    """
    numbers = numbers[:]
    numbers.sort()
    numbers.append(999999)
    pattern = ','
    for i in range(len(numbers)-1):
        if pattern[-1] == ',':
            pattern = pattern + str(numbers[i])
            if numbers[i]+1 == numbers[i+1]:
                pattern = pattern + '-'
            else:
                pattern = pattern + ','
        elif numbers[i]+1 != numbers[i+1]:
            pattern = pattern + str(numbers[i]) + ','

    if pattern[-1] in ',-':
        return pattern[1:-1]
    return pattern[1:]


def W3CDate(tm=None):
    """ Return time string according to http://www.w3.org/TR/NOTE-datetime
    """
    if not tm: tm = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", tm) + "%s%02d:%02d" % (
        "+-"[time.timezone < 0],
        abs(time.timezone) / 3600,
        abs(time.timezone) / 60 % 60
    )


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

    return vars(module).get(name, None)


def importPlugin(path, package, modulename, name):
    """ Import a named object from a module in the context of this function,
        located in the given path.

        Return None on failure.
    """
    import imp
    try:
        file = None
        try:
            file, filename, description = imp.find_module(modulename, [path])
            assert file is not None
            module = imp.load_module(package + "." + modulename,
                file, filename, description)
        finally:
            if file: file.close()
    except ImportError:
        return None

    return vars(module).get(name, None)


def isImportable(module):
    """ Check whether a certain module is available.
    """
    try:
        __import__(module)
        return 1
    except ImportError:
        return 0


def dumpFormData(form):
    """ Dump the form data for debugging purposes
    """
    import cgi

    result = '<dt><b>Form entries</b></dt>'
    for k in form.keys():
        v = form.getvalue(k, "<empty>")
        if type(v) is type([]):
            # Multiple username fields specified
            v = string.join(v, "|")
        result = result + '<dd><em>%s</em>=%s</dd>' % (k, cgi.escape(v))

    return result


def parseQueryString(qstr):
    """ Parse a querystring "key=value&..." into a dict.
    """
    import urllib

    values = {}
    pairs = string.split(qstr, '&')
    for pair in pairs:
        key, val = string.split(pair, '=')
        values[urllib.unquote(key)] = urllib.unquote(val)

    return values


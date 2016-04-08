"""
    MoinMoin - Utility Functions

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: util.py,v 1.7 2000/12/06 10:48:50 jhermann Exp $
"""

# Imports
import os, re, time, string, sys

# Globals
sent_headers = 0
user_headers = []


#############################################################################
### CGI stuff
#############################################################################

def getScriptname():
    return os.environ.get('SCRIPT_NAME', '')


def getPathinfo():
    pathinfo = os.environ.get('PATH_INFO', '')
    scriptname = getScriptname()

    # Fix for bug in IIS/4.0
    if string.find(pathinfo, scriptname) == 0:
        pathinfo = pathinfo[len(scriptname):]                
    
    return pathinfo


def setHttpHeader(header):
    global user_headers
    user_headers.append(header)


def http_headers(more_headers=[]):
    global sent_headers
    if sent_headers:
        #print "Headers already sent!!!\n"
        return
    sent_headers = 1
    have_ct = 0

    # send http headers
    for header in more_headers:
        if string.lower(header)[:13] is "content-type:": have_ct = 1
        print header

    global user_headers
    for header in user_headers:
        if string.lower(header)[:13] is "content-type:": have_ct = 1
        print header

    if not have_ct:
        print "Content-type: text/html"

    #print "Pragma: no-cache"
    #print "Cache-control: no-cache"
    #!!! Better set expiry to some 10 mins or so for normal pages?
    print

    #from pprint import pformat
    #sys.stderr.write(pformat(more_headers))
    #sys.stderr.write(pformat(user_headers))



def http_redirect(url):
    """ Redirect to a fully qualified, or server-rooted URL """
    if string.count(url, "://") == 0:
        url = "http://%s:%s%s" % (
            os.environ.get('SERVER_NAME'),
            os.environ.get('SERVER_PORT'),
            url)

    http_headers(["Location: " + url])


#############################################################################
### Timing
#############################################################################

class Clock:
    def __init__(self):
        self.timings = {'total': time.clock()}

    def start(self, timer):
        self.timings[timer] = time.clock()
    
    def stop(self, timer):
        self.timings[timer] = time.clock() - self.timings[timer]

    def value(self, timer):
        return "%.3f" % (self.timings[timer],)

    def dump(self, file):
        for timing in self.timings.items():
            file.write("%s = %.3f\n" % timing)


#############################################################################
### Misc
#############################################################################

# popen (use win32 version if available)
popen = os.popen
if os.name == "nt":
    try:
        import win32pipe
        popen = win32pipe.popen
    except:
        pass


def getPackageModules(packagefile):
    pyre = re.compile(r"^([^_].*)\.py$")
    pyfiles = filter(None, map(pyre.match, os.listdir(os.path.dirname(packagefile))))
    return map(lambda x: x.group(1), pyfiles)


def importName(modulename, name):
    """ Import a named object from a module in the context of this function,
        i.e. use fully qualified module paths.

        Return None on failure.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
        
    return vars(module)[name]


# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Stand-alone HTTP Server

    This is a simple, fast and very easy to install server. Its
    recommended for personal wikis or public wikis with little load.

    It is not well tested in public wikis with heavy load. In these case
    you might want to use twisted, fast cgi or mod python, or if you
    can't use those, cgi.
        
    Minimal usage:

        from MoinMoin.server.standalone import StandaloneConfig, run
        
        class Config(StandaloneConfig):
            docs = '/usr/share/moin/wiki/htdocs'
            user = 'www-data'
            group = 'www-data'
            
        run(Config)
        
    See more options in StandaloneConfig class.

    For security, the server will not run as root. If you try to run it
    as root, it will run as the user and group in the config. If you run
    it as a normal user, it will run with your regular user and group.
    
    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.

    Significant contributions to this module by R. Church <rc@ghostbitch.org>
"""

# Imports
import os, signal, sys, time, urllib, socket, errno
import BaseHTTPServer, SimpleHTTPServer, SocketServer
from email.Utils import formatdate

# MoinMoin imports
from MoinMoin import version
from MoinMoin.server import Config, switchUID
from MoinMoin.request import RequestStandAlone

# Set threads flag, so other code can use proper locking
from MoinMoin import config
config.use_threads = True
del config

# Server globals
httpd = None
config = None
moin_requests_done = 0


class MoinServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    
    def __init__(self, server_address, htdocs):
        BaseHTTPServer.HTTPServer.__init__(self, server_address,
                                           MoinRequestHandler)
        self.htdocs = htdocs
        self._abort = 0

    def serve_forever(self):
        """Handle one request at a time until we die."""
        # Startup message
        sys.stderr.write("Serving on %s:%d, documents in '%s'\n" % (
            self.server_address + (self.htdocs,)))

        # Server loop
        while not self._abort:
            self.handle_request()

    def die(self):
        """Abort this server instance's serving loop."""
        # Close hotshot profiler
        if config.hotshotProfile:
            config.hotshotProfile.close()

        # Set abort flag, then make request to wake the server
        self._abort = 1
        try:
            import httplib
            req = httplib.HTTP('%s:%d' % self.server_address)
            req.connect()
            req.putrequest('DIE', '/')
            req.endheaders()
            del req
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EADDRNOTAVAIL,]:
                raise


class MoinRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    server_version = "MoinMoin/" + version.revision
    
    def __init__(self, request, client_address, server):
        self.expires = 0
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, 
            client_address, server)

    # do_METHOD dispatchers  --------------------------------------------

    # These are called by the base class for each request
    
    def do_DIE(self):
        if self.server._abort:
            self.log_error("Shutting down")

    def do_POST(self):
        self.serveMoin()

    def do_GET(self):
        """ Handle GET requests

        Separate between wiki pages and css and image url by similar
        system as cgi and twisted, the '/wiki/' url prefix.

        TODO: should use request.cfg.url_prefix - and not a constant but
        request is not available at this time.  Should be fixed by
        loading config earlier.
        """
        if self.path.startswith('/wiki/'):
            self.path = self.path[5:]
            self.serveStaticFile()
        elif self.path in ['/favicon.ico', '/robots.txt']:
            self.serveStaticFile()
        else:
            self.serveMoin()

    # Serve methods  -----------------------------------------------------
    
    def serveStaticFile(self):
        """ Serve files from the htdocs directory """
        # 1 week expiry for static files
        self.expires = 7*24*3600
        try: 
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EPIPE, errno.ECONNABORTED]:
                raise
    
    def serveMoin(self):
        """ Serve a request using moin """
        global moin_requests_done

        # don't make an Expires header for wiki pages
        # TODO: does this work with cookies? they define expires header.
        self.expires = 0
        
        # Run request, use optional profiling
        if config.memoryProfile:
            config.memoryProfile.addRequest()
        try:
            if config.hotshotProfile and moin_requests_done > 0:
                # Don't profile the first request, its not interesting
                # for long running process, and its very expensive.
                runcall = config.hotshotProfile.runcall
                req = runcall(RequestStandAlone, self)
                runcall(req.run)
            else:
                req = RequestStandAlone(self)
                req.run()
        except socket.error, err:
            # Ignore certain errors
            if err.args[0] not in [errno.EPIPE, errno.ECONNABORTED]:
                raise
        # Count moin requests
        moin_requests_done += 1
        
    def translate_path(self, uri):
        """ Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.
        """
        file = urllib.unquote(uri)
        file.replace('\\', '/')
        words = file.split('/')
        words = filter(None, words)

        path = self.server.htdocs
        bad_uri = 0
        for word in words:
            drive, word = os.path.splitdrive(word)
            if drive:
                bad_uri = 1
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                bad_uri = 1
                continue
            path = os.path.join(path, word)

        if bad_uri:
            self.log_error("Detected bad request URI '%s', translated to '%s'" %
                           (uri, path,))    
        return path

    def end_headers(self):
        """overload the default end_headers, inserting expires header"""
        if self.expires:
            now = time.time()
            expires = now + self.expires
            self.send_header('Expires', formatdate(expires))
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)
        

def quit(signo, stackframe):
    """Signal handler for aborting signals."""
    global httpd
    print "Interrupted!"
    if httpd:
        httpd.die()

class StandaloneConfig(Config):
    """ Standalone server default config """

    docs = '/usr/share/moin/htdocs'
    user = 'www-data'
    group = 'www-data'
    port = 8000
    interface = 'localhost'
    logPath = None
    memoryProfile = None
    hotshotProfile = None


def run(configClass):
    """ Create and run a moin server
    
    See StandaloneConfig for available options
    
    @param configClass: config class
    """    
    # set globals (only on first import, save from reloads!)
    global httpd
    global config

    # Create config instance (raise RuntimeError if config invalid)   
    config = configClass()
    
    # register signal handler
    signal.signal(signal.SIGABRT, quit)
    signal.signal(signal.SIGINT,  quit)
    signal.signal(signal.SIGTERM, quit)

    # Create error log
    if config.logPath:
        sys.stderr = file(config.logPath, 'at')

    # Start profiler
    if config.memoryProfile:
        config.memoryProfile.sample()

    # create web server 
    httpd = MoinServer((config.interface, config.port), config.docs)
        
    # start server

    # drop root
    if os.name == 'posix' and os.getuid() == 0:
        switchUID(config.uid, config.gid)        

    httpd.serve_forever()


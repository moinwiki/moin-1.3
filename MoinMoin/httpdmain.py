"""
    MoinMoin - Stand-alone HTTP Server

    Copyright (c) 2001 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Significant contributions to this module by R. Church <rc@ghostbitch.org>

    $Id: httpdmain.py,v 1.8 2001/07/11 20:23:00 jhermann Exp $
"""
__version__ = "$Revision: 1.8 $"[11:-2]

# Imports
import os, signal, sys, time, thread, urllib, string
import BaseHTTPServer
import SimpleHTTPServer
from MoinMoin import config

allowed_extensions = ['.gif', '.jpg', '.png', '.css', '.js']

# Classes
class MoinServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, htdocs):
        BaseHTTPServer.HTTPServer.__init__(self, server_address, MoinRequestHandler)

        self.htdocs = htdocs
        self._abort = 0

    def serve_in_thread(self):
        """Start the main serving loop in its own thread."""
        thread.start_new_thread(self.serve_forever, ())

    def serve_forever(self):
        """Handle one request at a time until we die."""
        sys.stderr.write("Serving on %s:%d, documents in '%s'\n" % (self.server_address + (self.htdocs,)))
        while not self._abort:
            self.handle_request()

    def die(self):
        """Abort this server instance's serving loop."""
        self._abort = 1

        # make request to self so server wakes up
        import httplib
        req = httplib.HTTP('%s:%d' % self.server_address)
        req.connect()
        req.putrequest('DIE', '/')
        req.endheaders()
        del req


class MoinRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    server_version = "MoinMoin/" + __version__

    def __init__(self, request, client_address, server):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_DIE(self):
        if self.server._abort:
            self.log_error("Shutting down")

    def do_POST(self):
        self.doRequest()

    def do_GET(self):
        dummy, extension = os.path.splitext(self.path)
        if extension.lower() in allowed_extensions:
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.doRequest()

    def translate_path(self, uri):
        """ Translate a /-separated PATH to the local filename syntax.

            Components that mean special things to the local file system
            (e.g. drive or directory names) are ignored.

        """
        import urllib

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
            self.log_error("Detected bad request URI '%s', translated to '%s'" % (uri, path,))
            
        return path

    def doRequest(self):
        """Serve a request."""
        rest = self.path
        i = string.rfind(rest, '?')
        if i >= 0:
            rest, query = rest[:i], rest[i+1:]
        else:
            query = ''

        env = {}
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.unquote(rest)
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = uqrest #self.translate_path(uqrest)
        env['SCRIPT_NAME'] = '' #scriptname
        env['QUERY_STRING'] = query or ''
        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]
        # XXX AUTH_TYPE
        # XXX REMOTE_USER
        # XXX REMOTE_IDENT
        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader
        length = self.headers.getheader('content-length')
        env['CONTENT_LENGTH'] = length or ''
        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in string.whitespace:
                accept.append(string.strip(line))
            else:
                accept = accept + string.split(line[7:], ',')
        env['HTTP_ACCEPT'] = string.joinfields(accept, ',')
        ua = self.headers.getheader('user-agent')
        env['HTTP_USER_AGENT'] = ua or ''
        co = filter(None, self.headers.getheaders('cookie'))
        env['HTTP_COOKIE'] = string.join(co, ', ') or ''

        save_env = os.environ
        save_stdin = sys.stdin
        save_stdout = sys.stdout
        save_stderr = sys.stderr

        from MoinMoin import cgimain

        try:
            try:
                os.environ.update(env)
                sys.stdout = self.wfile
                sys.stdin = self.rfile
                self.send_response(200)

                cgimain.run()

                sys.stdout.flush()
            finally:
                os.environ = save_env
                sys.stdin = save_stdin
                sys.stdout = save_stdout
                sys.stderr = save_stderr
        except SystemExit, sts:
            self.log_error("CGI script exit status %s", str(sts))
        else:
            #cgimain.request.clock.stop('total')
            self.log_error("CGI script exited OK, taking %s secs" %
                cgimain.request.clock.value('total'))

        sys.stdout.flush()
        sys.stderr.flush()


# Functions
def quit(signo, stackframe):
    """Signal handler for aborting signals."""
    print "Interrupted!"
    if httpd: httpd.die()
    #sys.exit(0)

def run():
    # set globals (only on first import, save from reloads!)
    global httpd
    httpd = None

    # register signal handler
    signal.signal(signal.SIGABRT, quit)
    signal.signal(signal.SIGINT,  quit)
    signal.signal(signal.SIGTERM, quit)

    # create web server
    filepath = os.path.normpath(os.path.abspath(config.httpd_docs))
    httpd = MoinServer((config.httpd_host, config.httpd_port), filepath)

    # start it
    if sys.platform == 'win32':
        # run threaded server
        httpd.serve_in_thread()

        # main thread accepts signal
        i = 0
        while not httpd._abort:
            i += 1
            print "\|/-"[i%4], "\r",
            time.sleep(1)
    else:
        # if run as root, change to configured user
        if os.getuid() == 0:
            if not config.httpd_user:
                print "Won't run as root, set the http_user config variable!"
                sys.exit(1)
            
            import pwd
            try:
                pwentry = pwd.getpwnam(config.httpd_user)
            except KeyError:
                print "Can't find http_user '%s'!" % (config.httpd_user,)
                sys.exit(1)

            uid = pwentry[2]
            os.setreuid(uid, uid)

        httpd.serve_forever()

if __name__ == "__main__":
    run()


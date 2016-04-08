"""
    MoinMoin - Stand-alone HTTP Server

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: httpdmain.py,v 1.1 2001/02/02 00:10:52 jhermann Exp $
"""
__version__ = "$Revision: 1.1 $"[11:-2]

# Imports
import os, signal, sys, thread, urllib, string
import BaseHTTPServer
import SimpleHTTPServer

# Classes
class MoinServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address):
        BaseHTTPServer.HTTPServer.__init__(self, server_address, MoinRequestHandler)
    
        self._abort = 0

    def serve_in_thread(self):
        """Start the main serving loop in its own thread."""
        thread.start_new_thread(self.serve_forever, ())

    def serve_forever(self):
        """Handle one request at a time until we die."""
        while not self._abort:
            self.handle_request()

    def die(self):
        """Abort this server instance's serving loop."""
        self._abort = 1


class MoinRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    server_version = "MoinMoin/" + __version__

    def do_GET(self):
        """Serve a GET request."""
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

        try:
            try:
                os.environ.update(env)
                sys.stdout = self.wfile
                sys.stdin = self.rfile
                self.send_response(200)
                #self.send_header("Content-type", "text/html")
                #self.end_headers()

                import util
                util.clock = util.Clock()

                import cgimain
                cgimain.run()
            finally:
                os.environ = save_env
                sys.stdin = save_stdin
                sys.stdout = save_stdout
                sys.stderr = save_stderr
        except SystemExit, sts:
            self.log_error("CGI script exit status %s", str(sts))
        else:
            self.log_error("CGI script exited OK")


# Functions
def quit(signo, stackframe):
    """Signal handler for aborting signals."""
    print "Interrupted!"
    if httpd: httpd.die()
    sys.exit(0)

def run():
    # set globals (only on first import, save from reloads!)
    global httpd
    httpd = None

    # register signal handler
    signal.signal(signal.SIGABRT, quit)
    signal.signal(signal.SIGINT,  quit)
    signal.signal(signal.SIGTERM, quit)

    # start web server
    server_address = ('', 8080)
    httpd = MoinServer(server_address)
    httpd.serve_forever()

if __name__ == "__main__":
    run()

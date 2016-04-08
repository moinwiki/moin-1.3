"""
    twisted.web based wiki server
    
    @copyright: 2004 Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""
# adapt this to fit your needs --------------------------------------
httpd_docs = '/org/de.wikiwikiweb.moinmoin/htdocs'
httpd_user = 'wikiwikiweb_de'
httpd_group = 'wikiwikiweb_de'
httpd_host = '80.190.101.154'
httpd_port = 80

import sys
sys.path.append('/org/de.wikiwikiweb.moinmoin/bin')
sys.path.append('/org/wiki')
sys.path.append('/home/twaldmann/moincvs/moin--main')

# -------------------------------------------------------------------

from twisted.web import script, static, server, vhost, resource, util
from twisted.internet import app, threads, reactor
import pwd, grp
import random

from MoinMoin.request import RequestTwisted

from twisted.python import threadable
threadable.init(1)

class WikiResource(resource.Resource):
    isLeaf = 1
    def render(self, request):
        return server.NOT_DONE_YET

class WikiRoot(resource.Resource):
    def getChild(self, name, request):
        if request.prepath == [] and name == 'wiki':
            return resource.Resource.getChild(self, name, request)
        else:
            req = RequestTwisted(request, name, reactor)
            threads.deferToThread(req.run)
            return WikiResource()

#
# custom MoinRequest and MoinSite to enable passing of file-upload filenames
#
# Copyright (c) 2004 by Oliver Graf <ograf@bitart.de>
#
import cgi, types

class MoinRequest(server.Request):

    def requestReceived(self, command, path, version):
        """Called by channel when all data has been received.
           Creates an extra member extended_args which also has
           filenames of file uploads ( FIELDNAME__filename__ ).

        This method is not intended for users.
        """
        self.content.seek(0,0)
        self.args = {}
        self.extended_args = {}
        self.stack = []

        self.method, self.uri = command, path
        self.clientproto = version
        x = self.uri.split('?')

        argstring = ""
        if len(x) == 1:
            self.path = self.uri
        else:
            if len(x) != 2:
                log.msg("May ignore parts of this invalid URI: %s"
                        % repr(self.uri))
            self.path, argstring = x[0], x[1]

        # cache the client and server information, we'll need this later to be
        # serialized and sent with the request so CGIs will work remotely
        self.client = self.channel.transport.getPeer()
        self.host = self.channel.transport.getHost()

        # create dummy env for cgi.FieldStorage
        env = {
            'REQUEST_METHOD': self.method,
            'QUERY_STRING': argstring,
            }
        if self.method in ('GET', 'HEAD') \
           and not self.received_headers.has_key('content-type'):
            self.received_headers['content-type']='application/x-www-form-urlencoded'

        form = cgi.FieldStorage(fp=self.content,
                                environ=env,
                                headers=self.received_headers)

        # Argument processing

        args = self.args
        try:
            keys = form.keys()
        except TypeError:
            pass
        else:
            for key in keys:
                values = form[key]
                if not isinstance(values, types.ListType):
                    values = [values]
                fixedResult = []
                for i in values:
                    if isinstance(i, cgi.MiniFieldStorage):
                        fixedResult.append(i.value)
                    elif isinstance(i, cgi.FieldStorage):
                        fixedResult.append(i.value)
                        # multiple uploads to same form field are stupid!
                        if i.filename:
                            args[key + '__filename__'] = i.filename
                args[key] = fixedResult

        self.process()

class MoinSite(server.Site):
    requestFactory = MoinRequest

# The root of the HTTP hierarchy
default = WikiRoot()

# here is where img and css come from
default.putChild('wiki', static.File(httpd_docs))

# set logfile name.
# This is the *Apache compatible* log file, not the twisted-style logfile.
# Leaving this as None will have no Apache compatible log file. Apache
# compatible logfiles are useful because there are quite a few programs
# which analyse them and display statistics. 
logPath = None

# Allow the requestor to tell us which host we are
# default.putChild('vhost', vhost.VHostMonsterResource())

# Make sure it is easy to add new virtual hosts:
root = vhost.NameVirtualHost()
root.default = default

# To add virtual hosts
# exampleRoot = static.File('/var/vhosts/example')
# root.addHost('localhost', default)

# Generate the Site factory. You will not normally
# want to modify this line.
site = MoinSite(root, logPath=logPath)

# Set user/group to run under
# Usually, it runs under the www-data user and group.
#uid = pwd.getpwnam('www-data')[2]
#gid = grp.getgrnam('www-data')[2]
uid = pwd.getpwnam(httpd_user)[2]
gid = grp.getgrnam(httpd_group)[2]

# Generate the Application. You will not normally
# want to modify this line.
application = app.Application("web", uid=uid, gid=gid)
application.listenTCP(httpd_port, site, interface=httpd_host)


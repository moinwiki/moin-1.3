# -*- coding: iso-8859-1 -*-
"""
    MoinMoin.server.twistedmoin

    Create standalone twisted based server.

    Minimal usage:

        from MoinMoin.server.twistedmoin import TwistedConfig, makeApp
        
        class Config(TwistedConfig):
            docs = '/usr/share/moin/wiki/htdocs'
            user = 'www-data'
            group = 'www-data'
            
        application = makeApp(Config)

    Then run this code with twistd -y yourcode.py. See moin_twisted script.

    @copyright: 2004 by Thomas Waldmann, Oliver Graf, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import cgi
import os

# Twisted imports
from twisted.application import internet, service
from twisted.web import script, static, server, vhost, resource, util
from twisted.internet import threads, reactor

# Enable threads
from twisted.python import threadable
threadable.init(1)

# MoinMoin imports
from MoinMoin.request import RequestTwisted
from MoinMoin.server import Config

config = None

    
class WikiResource(resource.Resource):
    """ Wiki resource """
    isLeaf = 1
    
    def render(self, request):
        return server.NOT_DONE_YET


class WikiRoot(resource.Resource):
    """ Wiki root resource """
    
    def getChild(self, name, request):
        # Serve images and css from '/wiki'
        if request.prepath == [] and name == 'wiki':
            return resource.Resource.getChild(self, name, request)

        # Serve special 'root' files from '/wiki'
        elif name in ['favicon.ico', 'robots.txt'] and request.postpath == []:
            return self.children['wiki'].getChild(name, request)

        # All other through moin
        else:
            if config.memoryProfile:
                config.memoryProfile.addRequest()
            req = RequestTwisted(request, name, reactor)
            if config.hotshotProfile:
                threads.deferToThread(config.hotshotProfile.runcall, req.run)
            else:
                threads.deferToThread(req.run)
            return WikiResource()


class MoinRequest(server.Request):
    """ MoinMoin request

    Enable passing of file-upload filenames
    """

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
                if not isinstance(values, list):
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
    """ Moin site """
    requestFactory = MoinRequest

    def startFactory(self):
        """ Setup before starting """
        # Memory profile
        if config.memoryProfile:
            config.memoryProfile.sample()

        # hotshot profile
        if config.hotshotProfile:
            import hotshot
            config.hotshotProfile = hotshot.Profile(config.hotshotProfile)
        server.Site.startFactory(self)

    def stopFactory(self):
        """ Cleaup before stoping """
        server.Site.stopFactory(self)
        if config.hotshotProfile:
            config.hotshotProfile.close()        


class TwistedConfig(Config):
    """ Twisted server default config """

    docs = '/usr/share/moin/htdocs'
    user = 'www-data'
    group = 'www-data'
    port = 8080
    interfaces = ['']
    threads = 10
    logPath = None
    virtualHosts = None
    memoryProfile = None
    hotshotProfile = None

    def __init__(self):
        Config.__init__(self)

        # Check for '' in interfaces, then ignore other
        if '' in self.interfaces:
            self.interfaces = ['']


def makeApp(ConfigClass):
    """ Generate and return an application

    See MoinMoin.server.Config for config options

    @param ConfigClass: config class
    @rtype: application object
    @return twisted application, needed by twistd
    """
    # Create config instance (raise RuntimeError if config invalid)
    global config
    config = ConfigClass()
        
    # Set number of threads
    reactor.suggestThreadPoolSize(config.threads)
    
    # The root of the HTTP hierarchy
    default = WikiRoot()

    # Here is where img and css and some special files come from
    default.putChild('wiki', static.File(config.docs))

    # Generate the Site factory
    # TODO: Maybe we can use WikiRoot instead of this
    # ----------------------------------------------
    root = vhost.NameVirtualHost()
    root.default = default
    # ----------------------------------------------
    site = MoinSite(root, logPath=config.logPath)

    # Make application
    application = service.Application("web", uid=config.uid, gid=config.gid)
    sc = service.IServiceCollection(application)

    # Listen to all interfaces in config.interfaces
    for interface in config.interfaces:
        # Add a TCPServer for each interface. Default [''] uses only one.
        s = internet.TCPServer(config.port, site, interface=interface)
        s.setServiceParent(sc)

    return application


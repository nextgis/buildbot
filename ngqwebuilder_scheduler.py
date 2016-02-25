from twisted.web import server, resource
from twisted.internet import reactor

from buildbot.schedulers import base
from buildbot.process.properties import Properties
from buildbot.util import json

"""
from ngqwebuilder_scheduler import NGQWebBuilderForceScheduler
c['schedulers'].append(
    NGQWebBuilderForceScheduler(
        "sched",
        8011,
        ["mytest"]
    )
)
"""

class NGQWebBuilderForceScheduler(resource.Resource, base.BaseScheduler):  
    isLeaf = True

    def __init__(self, name, listeningPort, builderNames, **kwargs):
        resource.Resource.__init__(self)
        base.BaseScheduler.__init__(self, name, builderNames, {}, **kwargs)
        
        self.site = server.Site(self)
        self.listeningPort = listeningPort

    def startService(self):
        self.port = reactor.listenTCP(self.listeningPort, self.site)

    def stopService(self):
        self.port.stopListening()

    def _delayedRender(self, res, request):
        request.responseHeaders.addRawHeader(b"content-type", b"application/json")
        request.write(json.dumps({'bsid': res[0]}))
        request.finish()

    def render_POST(self, request):
        newdata = request.content.getvalue()
        propertiesAsDict = json.loads(newdata)
        properties = Properties.fromDict(propertiesAsDict)
        d = self.startBuild(properties)
        
        d.addCallback(self._delayedRender, request)
        return server.NOT_DONE_YET

    def startBuild(self, properties):
        return self.addBuildsetForLatest(
            reason="NGQWebBuilderForceScheduler ask", 
            properties=properties
        )

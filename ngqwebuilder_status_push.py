from buildbot.status.status_push import *
from buildbot.status import base
from buildbot.util import json


"""
from ngqwebuilder_status_push import NGQWebBuilderNotifier
c['status'].append(NGQWebBuilderNotifier("http://0.0.0.0:8080", ["mytest"]))
"""


class NGQWebBuilderNotifier(StatusPush):
    def __init__(self, serverUrl, targetBuilders=[]):
        base.StatusReceiverMultiService.__init__(self)

        self.serverUrl = serverUrl
        self.targetBuilders = targetBuilders
        # self.lastPushWasSuccessful = True
        path = ('events_' +
                    urlparse.urlparse(self.serverUrl)[1].split(':')[0])
        queue = PersistentQueue(
            primaryQueue=MemoryQueue(),
            secondaryQueue=DiskQueue(path)
        )

        StatusPush.__init__(
            self,
            serverPushCb=NGQWebBuilderNotifier.pushStatus,
            queue=queue,
            path=path,
            bufferDelay=5,
            blackList=[
                'start',
                'shutdown',
                'requestSubmitted',
                'requestCancelled',
                # 'buildsetSubmitted',
                'builderAdded',
                'builderChangedState',
                # 'buildStarted',
                'buildETAUpdate',
                'stepStarted',
                'stepTextChanged',
                'stepText2Changed',
                'stepETAUpdate',
                'logStarted',
                'logFinished',
                'stepFinished',
                # 'buildFinished',
                'buildedRemoved',
                'changeAdded',
                'slaveConnected',
                'slaveDisconnected',
                'slavePaused',
                'slaveUnpaused',
            ]
        )

    def pushStatus(self):
        items = self.queue.popChunk()

        newitems = []
        for item in items:
            log.msg("?????? item: {}".format(item))

            if item.get('event') in ['buildStarted','buildFinished']:
                if item.get('payload', {}).get('build', {}).get('builderName') not in self.targetBuilders:
                    continue

            newitems.append(item)

        if len(newitems) > 0:
            # packets = json.dumps(newitems, separators=(',', ':'))
            # params = {'packets': packets}
            data = json.dumps(newitems)

            self.pushHTTP(data, newitems)
        else:
            return self.queueNextServerPush()

    # def wasLastPushSuccessful(self):
    #     return self.lastPushWasSuccessful

    def pushHTTP(self, data, items):
        def Success(result):
            log.msg('Sent %d events to %s' % (len(items), self.serverUrl))
            # self.lastPushWasSuccessful = True

        def Failure(result):
            log.msg('Failed to push %d events to %s: %s' %
                    (len(items), self.serverUrl, str(result)))
            self.queue.insertBackChunk(items)
            if self.stopped:
                self.queue.save()
            # self.lastPushWasSuccessful = False

        headers = {'Content-Type': 'application/json'}
        connection = client.getPage(self.serverUrl,
                                    method='POST',
                                    postdata=data,
                                    headers=headers,
                                    agent='buildbot')
        connection.addCallbacks(Success, Failure)
        return connection

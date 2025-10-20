import fnmatch
import os
import sys

from buildbot_worker.bot import Worker
from twisted.application import service
from twisted.python.log import FileLogObserver, ILogObserver

basedir = os.path.abspath(os.path.dirname(__file__))
application = service.Application("buildbot-worker")

application.setComponent(ILogObserver, FileLogObserver(sys.stdout).emit)

buildmaster_host = os.environ.get("BUILDMASTER", "localhost")
port = int(os.environ.get("BUILDMASTER_PORT", 9989))
connection_string = None

workername = os.environ.get("WORKERNAME", "docker")
passwd = os.environ.get("WORKERPASS")

# delete the password from the environ so that it is not leaked in the log
blacklist = os.environ.get("WORKER_ENVIRONMENT_BLACKLIST", "WORKERPASS").split()
for name in list(os.environ.keys()):
    for toremove in blacklist:
        if fnmatch.fnmatch(name, toremove):
            del os.environ[name]

keepalive = 600
umask = None
maxdelay = 300
numcpus = None
allow_shutdown = None
maxretries = 10
use_tls = 0
delete_leftover_dirs = 0
proxy_connection_string = None
protocol = "pb"

service = Worker(
    buildmaster_host,
    port,
    workername,
    passwd,
    basedir,
    keepalive,
    umask=umask,
    maxdelay=maxdelay,
    numcpus=numcpus,
    allow_shutdown=allow_shutdown,
    maxRetries=maxretries,
    protocol=protocol,
    useTls=use_tls,
    delete_leftover_dirs=delete_leftover_dirs,
    connection_string=connection_string,
    proxy_connection_string=proxy_connection_string,
)
service.setServiceParent(application)

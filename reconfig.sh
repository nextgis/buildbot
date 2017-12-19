t#!/bin/sh

# Master monitoring is enough as everything rewrite on git pull
inotifywait -q -m -e modify -e attrib /opt/buildbot/master/master.cfg | while read events; do
    sleep 15
    /opt/buildbot/sandbox/bin/buildbot stop /opt/buildbot/master
    sleep 10
    /opt/buildbot/sandbox/bin/buildbot start /opt/buildbot/master
done &

#inotifywait -q -m -e attrib /opt/buildbot/master/*.py | while read events; do 
#    sleep 30
#    /opt/buildbot/sandbox/bin/buildbot restart master
#done &

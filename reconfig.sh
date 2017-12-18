#!/bin/sh

inotifywait -q -m -e attrib /opt/buildbot/master/master.cfg | while read events; do
    sleep 30
    /opt/buildbot/sandbox/bin/buildbot restart master
done &

inotifywait -q -m -e attrib /opt/buildbot/master/*.py | while read events; do 
    sleep 30
    /opt/buildbot/sandbox/bin/buildbot restart master
done &

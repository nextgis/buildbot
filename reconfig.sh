#!/bin/sh

while inotifywait -q -e modify /opt/buildbot/master/master.cfg; do
    sleep 30
    /opt/buildbot/sandbox/bin/buildbot restart master
done &

while inotifywait -q -e modify /opt/buildbot/master/*.py; do 
    sleep 30
    /opt/buildbot/sandbox/bin/buildbot restart master
done &

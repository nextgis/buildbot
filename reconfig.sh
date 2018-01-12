#!/bin/sh

# This script restart build bot on master.cfg changes after push to the buildbot
# repo. Master monitoring is enough as everything rewrite on git pull

inotifywait -e close_write,moved_to,create -m /opt/buildbot/master |
while read -r directory events filename; do
  if [ "$filename" = "master.cfg" ]; then
    sleep 10
    /opt/buildbot/sandbox/bin/buildbot stop /opt/buildbot/master
    sleep 10
    /opt/buildbot/sandbox/bin/buildbot start /opt/buildbot/master
  fi
done

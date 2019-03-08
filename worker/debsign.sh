#!/bin/sh
debsign -k0000AAAA -p"gpg --passphrase-file /home/ngw_admin/slave/lp_passphrase --batch --no-use-agent" --re-sign /home/ngw_admin/slave/$1/build/*changes

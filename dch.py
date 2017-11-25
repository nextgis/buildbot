# -*- coding: utf-8 -*-
################################################################################
# Project:  ppa buildbot utility
# Purpose:  prepare changelog by input values
# Author:   Dmitry Barishnikov, dmitry.baryshnikov@nextgis.ru
################################################################################
# Copyright (C) 2016-2017, NextGIS <info@nextgis.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

# help message
# python dch.py -h

# add commit messages to changelog and save it to path_to_src_dir/debian/changelog
# python dch.py -n 2.2.0 -o path_to_source_changelog -d path_to_src_dir -p fill

# rewrite original changelog by changed one
# python dch.py -o path_to_source_changelog -d path_to_src_dir -p store

import sys
import os
import argparse
import ConfigParser
import subprocess
from shutil import copy
from datetime import datetime

format_simple = '--pretty=format:%h - %an : %s'
fromat_debian = '--pretty=format:  * %h - %an : %s'
config_name = 'dch.cfg'

def writeChangeLog(app, version, counter, distro, last_commit, current_commit, folder, infile, outfile):
    ver_str = str(version)
    count_str = str(int(counter) + 1)
    full_message = app + ' (' + ver_str + '+' + count_str + '-0' + distro + '1) ' + distro + '; urgency=medium\n\n'
    if last_commit == '':
        # get last 20 messages
        log_messages = subprocess.check_output(['git', 'log', fromat_debian, '-20', '--no-merges'], cwd=folder)
    else:
        log_messages = subprocess.check_output(['git', 'log', fromat_debian, last_commit+'..'+current_commit, '--no-merges'], cwd=folder)

    full_message += log_messages
    full_message += '\n\n -- '
    full_message += os.environ.get('DEBFULLNAME')
    full_message += ' <'+os.environ.get('DEBEMAIL')+'>  '
    dt = datetime.utcnow()
    full_message += dt.strftime("%a, %d %b %Y %H:%M:%S +0000\n\n")
    try:
        with open(infile, 'r') as f:
            full_message += f.read()
        f.closed
    except:
        print 'no changelog, will be created'

    cf = open(outfile, 'w')
    cf.write(full_message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare debian changelog.')
    parser.add_argument('-n', '--number', help='package number')
    parser.add_argument('-o', '--origin', help='inited changelog file or file to save changes')
    parser.add_argument('-f', '--folder', help='destination git folder')
    parser.add_argument('-d', '--distro', help='ubuntu distribution', choices=['precise', 'trusty', 'wily', 'xenial', 'yakkety', 'zesty', 'artful'])
    parser.add_argument('-p', '--process', help='operation fill or store', choices=['fill', 'store', 'simple', 'tar'], required=True)
    parser.add_argument('-a', '--app', help='application name')

    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(config_name)
    try:
        counter = config.get('main', 'counter', 0)
    except:
        counter = 0

    try:
        version = config.get('main', 'version')
    except:
        version = args.number

    if version != args.number:
        counter = 0
        version = args.number

    if args.process == 'tar':
        ver_str = str(version)
        count_str = str(int(counter) + 1)
        subprocess.call(["tar", '-caf', args.app + '_' + ver_str + '+' + count_str + '.orig.tar.gz', args.folder, '--exclude-vcs'])
        sys.exit(0)

    try:
        last_commit = config.get('main', 'commit')
    except:
        last_commit = ''

    current_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.folder).strip()

    if last_commit == current_commit:
        print 'No changes to log'
        sys.exit(1)

    if args.process == 'store':
        if args.origin is not None:
            writeChangeLog(args.app, version, counter, 'unstable', last_commit, current_commit, args.folder, 'changelog', 'changelog')
        config_stor = ConfigParser.RawConfigParser()
        config_stor.add_section('main')
        config_stor.set('main', 'counter', int(counter) + 1)
        config_stor.set('main', 'version', version)
        config_stor.set('main', 'commit', current_commit)
        with open(config_name, 'wb') as configfile:
            config_stor.write(configfile)
    elif args.process == 'fill':
        writeChangeLog(args.app, version, counter, args.distro, last_commit, current_commit, args.folder, 'changelog', args.folder + '/debian/changelog')
    elif args.process == 'simple':
        if last_commit == '':
            # get last 5 messages
            log_messages = subprocess.check_output(['git', 'log', format_simple, '-5', '--no-merges'], cwd=args.folder)
        else:
            log_messages = subprocess.check_output(['git', 'log', format_simple, last_commit+'..'+current_commit, '--no-merges'], cwd=args.folder)
        f = open(args.origin, 'w')
        f.write(args.app + ' ' + args.number + '\n' + log_messages)
    else:
        print 'Unexpected operation'
        sys.exit(1)

    sys.exit(0)

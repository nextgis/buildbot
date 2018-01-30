#!/usr/bin/python

# Script to upload pack to ftp

import os
import subprocess
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NextGIS buildbot tools. Utility to upload pack to ftp')
    parser.add_argument('-v', '--version', action='version', version='NextGIS buildbot version 1.0')
    parser.add_argument('--ftp_user', dest='ftp_user', help='ftp login:password')
    parser.add_argument('--ftp', dest='ftp', help='ftp url')
    parser.add_argument('--build_path', dest='build', help='release file to upload')

    args = parser.parse_args()

    user = args.ftp_user
    ftp_url = args.ftp

    version_file = os.path.join(build_path, 'version.str')
    with open(version_file) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]

    release_file = os.path.join(build_path, content[2]) + '.zip'

    args = ['curl', '-u', user, '-T', '{' + release_file + ',' + version_file + '}', '--ftp-create-dirs', ftp_url]
    subprocess.check_output(args)

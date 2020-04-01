#!/usr/bin/python

# Script to upload pack to ftp

# python install_from_ftp.py --ftp_user 'user:password' --ftp 'ftp://192.168.2.1:21' --build_path '/Volumes/Data/tmp/test/ftp' --platform 'mac' --packages lib_freetype lib_gif lib_jpeg lib_png lib_sqlite lib_tiff lib_z py_sip lib_qt4

import os
import subprocess
import sys
import argparse
import shutil
import site
import json

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen


repka_endpoint = 'https://rm.nextgis.com'
repo_id = 2

compilers = {
    'mac' : 'Clang-9.0',
    'win32' : 'MSVC-19.12',
    'win64' : 'MSVC-19.12-64bit',
}

def get_packet_id(repo_id, packet_name):
    url =  repka_endpoint + '/api/packet?repository={}&filter={}'.format(repo_id, packet_name)
    color_print('Check packet url: ' + url, False, 'OKGRAY')
    response = urlopen(url)
    packets = json.loads(response.read())
    for packet in packets:
        if packet['name'] == packet_name: 
            return packet['id']
    return -1

def get_release(packet_id, tag):
    url =  repka_endpoint + '/api/release?packet={}'.format(packet_id)
    color_print('Check release url: ' + url, False, 'OKGRAY')
    response = urlopen(url)
    releases = json.loads(response.read())
    if releases is None:
        color_print('Release ID not found', False, 'LCYAN')
        return None

    for release in releases:
        if tag in release['tags']: 
            color_print('Release ID {} found'.format(release['id']), False, 'LCYAN')
            return release

    color_print('Release ID not found', False, 'LCYAN')
    return None

def get_file_id(release, platform):
    for file in release['files']:
        if file['name'].endswith('{}.zip'.format(compilers[platform])):
            return file['id']
    return -1

def run(args):
    subprocess.check_call(args)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKGRAY = '\033[0;37m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DGRAY='\033[1;30m'
    LRED='\033[1;31m'
    LGREEN='\033[1;32m'
    LYELLOW='\033[1;33m'
    LBLUE='\033[1;34m'
    LMAGENTA='\033[1;35m'
    LCYAN='\033[1;36m'
    WHITE='\033[1;37m'

def color_print(text, bold, color):
    if sys.platform == 'win32':
        print(text)
    else:
        out_text = ''
        if bold:
            out_text += bcolors.BOLD
        if color == 'GREEN':
            out_text += bcolors.OKGREEN
        elif color == 'LGREEN':
            out_text += bcolors.LGREEN
        elif color == 'LYELLOW':
            out_text += bcolors.LYELLOW
        elif color == 'LMAGENTA':
            out_text += bcolors.LMAGENTA
        elif color == 'LCYAN':
            out_text += bcolors.LCYAN
        elif color == 'LRED':
            out_text += bcolors.LRED
        elif color == 'LBLUE':
            out_text += bcolors.LBLUE
        elif color == 'DGRAY':
            out_text += bcolors.DGRAY
        elif color == 'OKGRAY':
            out_text += bcolors.OKGRAY
        else:
            out_text += bcolors.OKGRAY
        out_text += text + bcolors.ENDC
        print(out_text)

base_ftp_path = 'software/installer/src'
package_path_suffix = '/package.zip'

# lib_freetype_mac
# lib_gif_mac
# lib_jpeg_mac
# lib_png_mac
# lib_qt4_mac
# lib_sqlite_mac
# lib_tiff_mac
# lib_z_mac
# py_sip_mac

def delete_path(path_to_delete):
    color_print('Delete existing build dir ...', True, 'LRED')
    shutil.rmtree(path_to_delete, ignore_errors=True)

def copytree(src, dst, symlinks=False):
    color_print('Copy tree from {} to {}'.format(src, dst), True, 'LYELLOW')
    if not os.path.exists(dst):
        os.makedirs(dst)
        shutil.copystat(src, dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if symlinks and os.path.islink(s):
            if os.path.lexists(d):
                os.remove(d)
            os.symlink(os.readlink(s), d)
            try:
                st = os.lstat(s)
                mode = stat.S_IMODE(st.st_mode)
                os.lchmod(d, mode)
            except:
                pass # lchmod not available
        elif os.path.isdir(s):
            copytree(s, d, symlinks)
        else:
            shutil.copy2(s, d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NextGIS buildbot tools. Utility to download packages from ftp')
    parser.add_argument('-v', '--version', action='version', version='NextGIS buildbot version 1.0')
    parser.add_argument('--build_path', dest='build', required=True, help='Path to extract packages')
    parser.add_argument('--platform', dest='platform', choices=['mac','win32','win64'], required=True, help='package platform')
    parser.add_argument('--packages', dest='packages', nargs='+', required=True, help='download packages list without platform prefix')
    # parser.add_argument('--repo_id', dest='repo_id', required=True, help='{} repository identifier'.format(repka_endpoint))
    parser.add_argument('--create_pth', action='store_true')

    args = parser.parse_args()

    build_path = args.build
    if(not os.path.isabs(build_path)):
        build_path = os.path.abspath(build_path)

    tmp_path = os.path.join(build_path, 'tmp')
    if(os.path.exists(tmp_path) == False):
        os.makedirs(tmp_path)

    os.chdir( tmp_path )

    for package in args.packages:
        packet_id = get_packet_id(repo_id, package)
        if packet_id == -1:
            continue
        release = get_release(packet_id, 'latest')
        if release is None:
            continue
        file_id = get_file_id(release, args.platform)
        if file_id == -1:
            continue

        path = repka_endpoint + '/api/asset/{}/download'.format(file_id)
        out_zip = os.path.join(tmp_path, 'package.zip')
        color_print('Download ' + path, True, 'LGREEN')
        run(('curl', path, '-o', out_zip, '-s'))

        color_print('Extract ' + out_zip, False, 'LGREEN')
        run(('cmake', '-E', 'tar', 'xzf', out_zip))

        # Get first directory
        for x in os.listdir(tmp_path):
            full_x = os.path.join(tmp_path, x)
            if(os.path.isdir(full_x)):
                for y in os.listdir(full_x):
                    full_y = os.path.join(full_x, y)
                    if(os.path.isdir(full_y)):
                        if(package == 'lib_qt4'):
                            if(y == 'lib'):
                                copytree(full_y, os.path.join(build_path, 'Library', 'Frameworks'), True)
                        else:
                            copytree(full_y, os.path.join(build_path, y), True)
                        # shutil.move(full_y, build_path)
                        # shutil.copytree(full_y, os.path.join(build_path, y), symlinks=True)
                shutil.rmtree(full_x)

    # Create pth
    if args.create_pth:
        site_path = site.getusersitepackages()
        color_print('Create pth file at ' + site_path, False, 'LCYAN')
        with open(site_path + '/ng.pth', 'w') as f:
            f.write(build_path + '/Library/Python/2.7/site-packages\n')

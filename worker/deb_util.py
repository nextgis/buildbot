# -*- coding: utf-8 -*-
################################################################################
# Project:  ppa deb buildbot utility
# Purpose:  prepare debian changelog and package
# Author:   Dmitry Baryshnikov, dmitry.baryshnikov@nextgis.ru
################################################################################
# Copyright (C) 2016-2020, NextGIS <info@nextgis.com>
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

import argparse
import base64
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from urllib.request import HTTPError, Request, urlopen

format_simple = "--pretty=format:%h - %an : %s"
format_debian = "--pretty=format:  * %h - %an : %s"
repka_site = "rm.nextgis.com"
repka_endpoint = "https://{}".format(repka_site)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    OKGRAY = "\033[0;37m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DGRAY = "\033[1;30m"
    LRED = "\033[1;31m"
    LGREEN = "\033[1;32m"
    LYELLOW = "\033[1;33m"
    LBLUE = "\033[1;34m"
    LMAGENTA = "\033[1;35m"
    LCYAN = "\033[1;36m"
    WHITE = "\033[1;37m"


def color_print(text, bold, color):
    if sys.platform == "win32":
        print(text)
    else:
        out_text = ""
        if bold:
            out_text += bcolors.BOLD
        if color == "GREEN":
            out_text += bcolors.OKGREEN
        elif color == "LGREEN":
            out_text += bcolors.LGREEN
        elif color == "LYELLOW":
            out_text += bcolors.LYELLOW
        elif color == "LMAGENTA":
            out_text += bcolors.LMAGENTA
        elif color == "LCYAN":
            out_text += bcolors.LCYAN
        elif color == "LRED":
            out_text += bcolors.LRED
        elif color == "LBLUE":
            out_text += bcolors.LBLUE
        elif color == "DGRAY":
            out_text += bcolors.DGRAY
        elif color == "OKGRAY":
            out_text += bcolors.OKGRAY
        else:
            out_text += bcolors.OKGRAY
        out_text += text + bcolors.ENDC
        print(out_text)


def upload_file(file_path, username, password):
    post_url = repka_endpoint + "/api/upload"
    args = []
    if username is not None and password is not None:
        args = [
            "curl",
            "-u",
            username + ":" + password,
            "-F",
            "file=@" + file_path,
            post_url,
        ]
    else:
        args = ["curl", "-F", "file=@" + file_path, post_url]
    load_response = subprocess.check_output(args)
    response = json.loads(load_response.decode())

    file_uid = response["file"]
    file_name = response["name"]
    color_print("Uploaded: {} / {}".format(file_uid, file_name), True, "LGREEN")

    return file_uid, file_name


def add_auth(request, login, password):
    if login is not None and password is not None:
        base64string = base64.b64encode("{}:{}".format(login, password).encode())
        request.add_header("Authorization", "Basic {}".format(base64string.decode()))
    return request


def get_packet_id(repo_id, packet_name, username, password):
    url = repka_endpoint + "/api/packet?repository={}&filter={}".format(
        repo_id, packet_name
    )
    color_print("Check packet url: " + url, False, "OKGRAY")
    request = Request(url)
    request = add_auth(request, username, password)

    response = urlopen(request)
    packets = json.loads(response.read().decode("utf-8"))
    for packet in packets:
        if packet["name"] == packet_name:
            return packet["id"]
    return -1


def get_release_counter(packet_id, tag, distro_codename, username, password):
    url = repka_endpoint + "/api/release?packet={}".format(packet_id)
    color_print("Check release url: " + url, False, "OKGRAY")
    request = Request(url)
    request = add_auth(request, username, password)
    response = urlopen(request)
    releases = json.loads(response.read().decode("utf-8"))
    counter = 0
    if releases is None:
        color_print("Release ID not found", False, "LCYAN")
        return counter

    for release in releases:
        for tag_item in release["tags"]:
            if tag_item.startswith(tag):
                for option_item in release["options"]:
                    if option_item["value"] == distro_codename:
                        tag_parts = tag_item.split("+")
                        if len(tag_parts) > 1:
                            current_counter = int(tag_parts[1])
                            if current_counter >= counter:
                                counter = current_counter + 1

    color_print("Release counter not found. Set to 0", False, "LCYAN")
    return counter


def create_release(
    packet_id,
    name,
    description,
    tag,
    distrib,
    distrib_version,
    component,
    files,
    username,
    password,
):
    url = repka_endpoint + "/api/release"

    data = json.dumps(
        {
            "name": name,
            "description": description,
            "tags": [
                tag,
            ],
            "packet": packet_id,
            "files": files,
            "options": [
                {"key": "distribution", "value": distrib},
                {"key": "component", "value": component},
                {"key": "version", "value": distrib_version},
            ],
        }
    )

    request = Request(
        url, data=data.encode(), headers={"Content-Type": "application/json"}
    )  # , 'Content-Length': len(data)
    request = add_auth(request, username, password)

    try:
        response = urlopen(request)
    except HTTPError as e:
        print(e.read())
        exit(1)
    release = json.loads(response.read().decode("utf-8"))

    color_print("Release with ID {} created".format(release["id"]), False, "LCYAN")

    return release["id"]


def write_changelog(
    package, version, counter, distribution, repo_path, urgency="medium"
):
    full_message = "{} ({}+{}) {}; urgency={}\n\n".format(
        package, version, counter, distribution, urgency
    )
    log_messages = subprocess.check_output(
        ["git", "log", format_debian, "-3", "--no-merges"], cwd=repo_path
    )
    full_message += log_messages.decode(sys.stdout.encoding)
    full_message += "\n\n -- "
    full_message += os.environ.get("DEBFULLNAME", "NextGIS")
    full_message += " <" + os.environ.get("DEBEMAIL", "info@nextgis.com") + ">  "
    dt = datetime.utcnow()
    full_message += dt.strftime("%a, %d %b %Y %H:%M:%S +0000\n\n")
    changelog_path = os.path.join(repo_path, "debian", "changelog")
    with open(changelog_path, "w") as cl:
        cl.write(full_message)


def get_distro():
    import configparser
    import itertools

    config = configparser.ConfigParser()
    distro_version = ""
    distro_codename = ""
    with open("/etc/os-release") as fp:
        config.read_file(itertools.chain(["[global]"], fp))
        distro_version = config.get("global", "VERSION_ID").replace('"', "")
        distro_codename = config.get("global", "VERSION_CODENAME")
    return distro_version, distro_codename


def get_package_version(file):
    version = ""
    with open(args.version_file) as f:
        version = f.readline().rstrip()

    if version is None or version == "":
        sys.exit("Cannot find version")
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare debian package")
    parser.add_argument("-vf", "--version_file", help="version.str path")
    parser.add_argument(
        "-op",
        "--operation",
        help="operation to process",
        choices=[
            "info",
            "changelog",
            "tar",
            "make_release",
            "create_debian",
            "add_repka_repo",
            "add_deb_repo",
        ],
        required=True,
    )
    parser.add_argument("-rp", "--repo_path", help="repository path")
    parser.add_argument("-dp", "--deb_files_path", help="deb files path")
    parser.add_argument("-pn", "--package_name", help="package name")
    parser.add_argument(
        "--repo_id",
        dest="repo_id",
        help="{} repository identifier".format(repka_endpoint),
    )
    parser.add_argument(
        "--repo_component",
        dest="repo_component",
        default="main",
        help="Repository component. Usually main, contfib and non-free",
    )
    parser.add_argument("--deb", dest="deb", help="deb line to add to sources.list")
    parser.add_argument(
        "--deb_key", dest="deb_key", help="deb key to check packages sign"
    )
    parser.add_argument(
        "--deb_keyserver", dest="deb_keyserver", help="deb keyserver to verify sign"
    )
    parser.add_argument(
        "--login", dest="login", help="login for {}".format(repka_endpoint)
    )
    parser.add_argument(
        "--password", dest="password", help="password for {}".format(repka_endpoint)
    )
    args = parser.parse_args()

    if args.operation == "info":
        distro_version, distro_codename = get_distro()
        version = get_package_version(args.version_file)
        print(
            "Package: {}\nVersion: {}\nDistribution:\n  * version - {}\n  * codename - {}\n".format(
                args.package_name, version, distro_version, distro_codename
            )
        )

    elif args.operation == "changelog":
        distro_version, distro_codename = get_distro()
        version = get_package_version(args.version_file)
        packet_id = get_packet_id(
            args.repo_id, args.package_name, args.login, args.password
        )
        counter = get_release_counter(
            packet_id, version, distro_codename, args.login, args.password
        )
        write_changelog(args.package_name, version, counter, "unstable", args.repo_path)

    elif args.operation == "tar":
        distro_version, distro_codename = get_distro()
        version = get_package_version(args.version_file)
        packet_id = get_packet_id(
            args.repo_id, args.package_name, args.login, args.password
        )
        counter = get_release_counter(
            packet_id, version, distro_codename, args.login, args.password
        )
        subprocess.call(
            [
                "tar",
                "-caf",
                "{}_{}+{}.orig.tar.gz".format(args.package, version, counter),
                args.repo_path,
                "--exclude-vcs",
            ]
        )

    elif args.operation == "make_release":
        packet_id = get_packet_id(
            args.repo_id, args.package_name, args.login, args.password
        )
        if packet_id == -1:
            color_print(
                "Packet {} not found in repository".format(args.package_name),
                True,
                "LRED",
            )
            exit(1)

        deb_files = glob.glob(os.path.join(args.deb_files_path, "*.deb"))
        uploaded_files = []
        for deb_file in deb_files:
            file_uid, file_name = upload_file(deb_file, args.login, args.password)
            uploaded_files.append({"upload_name": file_uid, "name": file_name})

        version = get_package_version(args.version_file)
        distro_version, distro_codename = get_distro()
        counter = get_release_counter(
            packet_id, version, distro_codename, args.login, args.password
        )
        tag_name = "{}+{}".format(version, counter)
        create_release(
            packet_id,
            "v{} [{}]".format(tag_name, distro_codename),
            "Version " + tag_name + " on " + distro_codename,
            tag_name,
            distro_codename,
            distro_version,
            args.repo_component,
            uploaded_files,
            args.login,
            args.password,
        )

    elif args.operation == "create_debian":
        # 1 clone ppa
        if os.path.exists("ppa") == False:
            subprocess.call(
                ["git", "clone", "--depth", "1", "https://github.com/nextgis/ppa.git"]
            )
        # 2 copy debian into repo
        ppa_path = os.path.join("ppa", args.package_name)
        if os.path.exists(ppa_path) == False:
            sys.exit("No debian directory in path {}".format(args.operation))

        distro_version, distro_codename = get_distro()
        ppa_dist_path = os.path.join(ppa_path, distro_codename)
        out_path = os.path.join(args.repo_path, "debian")
        shutil.rmtree(out_path, True)
        if os.path.exists(ppa_dist_path) == False:
            ppa_dist_path = os.path.join(ppa_path, "debian")
        shutil.copytree(ppa_dist_path, out_path)

    elif args.operation == "add_repka_repo":
        distro_version, distro_codename = get_distro()
        # https://rm.nextgis.com/api/repo/11/deb stretch Release
        url = repka_endpoint + "/api/repo/{}/deb/dists/{}/Release".format(
            args.repo_id, distro_codename
        )
        print("Check {}".format(url))
        try:
            # 1. Check exists
            request = Request(url)
            request = add_auth(request, args.login, args.password)
            response = urlopen(request)
            # 2. Add repo
            curl_user_key = ""
            if args.login is not None and args.password is not None:
                curl_user_key = '--user "{}:{}" '.format(args.login, args.password)
                with open("/etc/apt/auth.conf.d/rm.conf", "w") as repka_file:
                    repka_file.write(
                        """machine {}
  login {}
  password {}""".format(repka_site, args.login, args.password)
                    )
            subprocess.call(
                [
                    "/bin/sh",
                    "-c",
                    "echo deb {}/api/repo/{}/deb {} {} | tee -a /etc/apt/sources.list".format(
                        repka_endpoint,
                        args.repo_id,
                        distro_codename,
                        args.repo_component,
                    ),
                ]
            )
            subprocess.call(
                [
                    "/bin/sh",
                    "-c",
                    "curl {}-s -L {}/api/repo/{}/deb/key.gpg | apt-key add -".format(
                        curl_user_key, repka_endpoint, args.repo_id
                    ),
                ]
            )
            try:
                with open("/etc/apt/preferences.d/nextgis", "w") as apt_preferences:
                    apt_preferences.write("""Package: libgdal-dev libgdal36 libgdal31 gdal-bin gdal-data python3-gdal\nPin: origin rm.nextgis.com\nPin-Priority: 1001\n""")
            except Exception as e:
                print(f"Failed to write APT preferences: {e}")
        except:
            print(
                "Skip add repo: {}/api/repo/{}/deb {} {}".format(
                    repka_endpoint, args.repo_id, distro_codename, args.repo_component
                )
            )
            pass
        subprocess.call(["apt", "update"])
    elif args.operation == "add_deb_repo":
        subprocess.call(
            ["/bin/sh", "-c", "echo {} | tee -a /etc/apt/sources.list".format(args.deb)]
        )
        subprocess.call(
            [
                "/bin/sh",
                "-c",
                "apt-key adv --keyserver {} --recv-keys {}".format(
                    args.deb_keyserver, args.deb_key
                ),
            ]
        )
        subprocess.call(["apt", "update"])
    else:
        sys.exit("Unsupported operation {}".format(args.operation))

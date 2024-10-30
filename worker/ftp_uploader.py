#!/usr/bin/python3

# Script to upload pack to ftp

import argparse
import os
import subprocess
import sys


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NextGIS buildbot tools. Utility to upload pack to ftp"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="NextGIS buildbot version 1.0"
    )
    parser.add_argument(
        "--ftp_user", dest="ftp_user", required=True, help="ftp login:password"
    )
    parser.add_argument("--ftp", dest="ftp", required=True, help="ftp url")
    parser.add_argument(
        "--build_path", dest="build", required=True, help="release file to upload"
    )

    args = parser.parse_args()

    user = args.ftp_user
    ftp_url = args.ftp
    build_path = args.build

    if ftp_url[-1:] != "/":
        ftp_url += "/"

    version_file = os.path.join(build_path, "version.str")
    with open(version_file) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]

    release_file = os.path.join(build_path, content[2]) + ".zip"
    package_file = os.path.join(build_path, "package.zip")
    os.rename(release_file, package_file)

    color_print(
        "Upload files {} and {} to ftp".format(package_file, version_file),
        True,
        "LGREEN",
    )
    args = [
        "curl",
        "-u",
        user,
        "-T",
        "{package.zip,version.str}",
        "--ftp-create-dirs",
        ftp_url,
    ]
    subprocess.check_output(args, cwd=build_path)

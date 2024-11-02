# -*- python -*-
# ex: set syntax=python:

import os
from typing import List

from buildbot.plugins import schedulers, steps, util

from .util import MACOS_REPO, WIN64_REPO

# Common

PROJECT_NAME = "inst_framework"
DESCRIPTION = "Build and publish tools for Qt and installer framework"

QT_PACKAGE_NAME = "inst_framework_qt"
INSTALLER_PACKAGE_NAME = "inst_framework"

LOGNAME = "stdio"
WORK_DIR = "build"
BUILD_SUBDIR_NAME = "build"

# Build constants

VM_CPU_COUNT = 6

MAC_OS_MIN_VERSION = "10.14"
MAC_OS_SDKS_PATH = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"

REPKA_SCRIPT_NAME = "repka_release.py"

QT_GIT_URL = "https://github.com/nextgis-borsch/lib_qt5.git"
INSTALLER_GIT_URL = "https://github.com/nextgis/nextgis_installer.git"

USERNAME = "buildbot"
userkey = os.environ.get("BUILDBOT_PASSWORD")

# Helpers


def cmake_qt_configure_definition(configure_args: List[str]) -> str:
    return "-DQT_CONFIGURE_ARGS=" + ";".join(
        map(lambda arg: arg.replace(" ", ";"), configure_args)
    )


# Build params


QT_CONFIGURE_COMMON_ARGS = [
    "-accessibility",
    "-no-icu",
    "-no-sql-sqlite",
    "-no-qml-debug",
    "-no-feature-ftp",
    "-no-feature-socks5",
    "-skip qtactiveqt",
    "-skip qtandroidextras",
    "-skip qtcharts",
    "-skip qtconnectivity",
    "-skip qtdatavis3d",
    "-skip qtdoc",
    "-skip qtgamepad",
    "-skip qtgraphicaleffects",
    "-skip qtlocation",
    "-skip qtmultimedia",
    "-skip qtpurchasing",
    "-skip qtquickcontrols",
    "-skip qtquickcontrols2",
    "-skip qtremoteobjects",
    "-skip qtscript",
    "-skip qtscxml",
    "-skip qtsensors",
    "-skip qtserialbus",
    "-skip qtserialport",
    "-skip qtspeech",
    "-skip qtvirtualkeyboard",
    "-skip qtwayland",
    "-skip qtwebchannel",
    "-skip qtwebengine",
    "-skip qtwebglplugin",
    "-skip qtwebsockets",
    "-skip qtwebview",
    "-skip qt3d",
    "-skip qtxmlpatterns",
    "-nomake examples",
    "-nomake tests",
    # Old options
    # "-skip qtlottie",
    # "-skip qtenginio",
    # "-skip qtquick1",
    # "-skip qtwebkit",
]

QT_CONFIGURE_WIN_ARGS = [
    *QT_CONFIGURE_COMMON_ARGS,
    "-no-opengl",
]

QT_CONFIGURE_MAC_ARGS = [
    *QT_CONFIGURE_COMMON_ARGS,
    "-qt-zlib",
    "-qt-libpng",
    "-qt-libjpeg",
    "-no-cups",
]

CMAKE_QT_COMMON_DEFS = [
    "-DBUILD_STATIC_LIBS=TRUE",
    "-DWITH_OpenSSL_EXTERNAL=ON",
    "-DSUPPRESS_VERBOSE_OUTPUT=ON",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DSKIP_DEFAULTS=ON",
    "-DWITH_ZLIB=OFF",
    "-DWITH_Freetype=OFF",
    "-DWITH_JPEG=OFF",
    "-DWITH_PNG=OFF",
    "-DWITH_TIFF=OFF",
    "-DWITH_SQLite3=OFF",
    "-DWITH_PostgreSQL=OFF",
    "-DWITH_WEBPDEMUX=OFF",
    "-DWITH_WEBPMUX=OFF",
    "-DWITH_WEBP=OFF",
    "-DWITH_HarfBuzz=OFF",
    "-DCREATE_CPACK_LIGHT=ON",
]

CMAKE_QT_WIN_DEFS = [
    *CMAKE_QT_COMMON_DEFS,
    cmake_qt_configure_definition(QT_CONFIGURE_WIN_ARGS),
]

CMAKE_QT_MAC_DEFS = [
    *CMAKE_QT_COMMON_DEFS,
    cmake_qt_configure_definition(QT_CONFIGURE_MAC_ARGS),
]

CMAKE_CONFIGURE_QT_WIN_ARGS = [
    *CMAKE_QT_WIN_DEFS,
    "-G",
    "Visual Studio 16 2019",
    "-A",
    "x64",
]

CMAKE_CONFIGURE_QT_MAC_ARGS = [
    *CMAKE_QT_MAC_DEFS,
    "-DCMAKE_OSX_SYSROOT=" + MAC_OS_SDKS_PATH + "/MacOSX.sdk",
    "-DCMAKE_OSX_DEPLOYMENT_TARGET=" + MAC_OS_MIN_VERSION,
]

# qt_without_openssl = False
# if qt_without_openssl:
#     qt_args = [
#         "-DBUILD_STATIC_LIBS=TRUE",
#         "-DWITH_OpenSSL=OFF",
#         "-DSUPPRESS_VERBOSE_OUTPUT=ON",
#         "-DCMAKE_BUILD_TYPE=Release",
#         "-DSKIP_DEFAULTS=ON",
#         "-DQT_CONFIGURE_ARGS=-accessibility;-no-ssl;-no-opengl;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtlocation;-skip;qtmultimedia;-skip;qtserialport;-skip;qtsensors;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qt3d;-skip;qtconnectivity;-skip;qtandroidextras;-skip;qtcanvas3d;-skip;qtcharts;-skip;qtdatavis3d;-skip;qtgamepad;-skip;qtpurchasing;-skip;qtserialbus;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebsockets;-skip;qtxmlpatterns;-skip;qtwebview;-no-feature-ftp;-no-feature-socks5",
#         "-DWITH_ZLIB=OFF",
#         "-DWITH_Freetype=OFF",
#         "-DWITH_JPEG=OFF",
#         "-DWITH_PNG=OFF",
#         "-DWITH_SQLite3=OFF",
#         "-DWITH_PostgreSQL=OFF",
#         "-DCREATE_CPACK_LIGHT=ON",
#     ]

CMAKE_CONFIGURE_QT_WIN_COMMAND = ["cmake", *CMAKE_CONFIGURE_QT_WIN_ARGS, ".."]
CMAKE_CONFIGURE_QT_MAC_COMMAND = ["cmake", *CMAKE_CONFIGURE_QT_MAC_ARGS, ".."]

CMAKE_BUILD_COMMAND = ["cmake", "--build", ".", "--config", "release"]
CMAKE_BUILD_QT_WIN_COMMAND = [*CMAKE_BUILD_COMMAND, "--", "/m:" + str(VM_CPU_COUNT)]
CMAKE_BUILD_QT_MAC_COMMAND = [*CMAKE_BUILD_COMMAND, "--", "-j" + str(VM_CPU_COUNT)]


# Build config


PLATFORMS = [
    {
        "name": "win",
        "os": "win64",
        "worker": "build-win-py3",
        "repo_id": WIN64_REPO,
        "env": {},
        "cmake_configure_qt_command": CMAKE_CONFIGURE_QT_WIN_COMMAND,
        "cmake_build_qt_command": CMAKE_BUILD_QT_WIN_COMMAND,
    },
    {
        "name": "mac",
        "os": "mac",
        "worker": "build-mac-py3",
        "repo_id": MACOS_REPO,
        "env": {
            "PATH": ["/usr/local/bin", "${PATH}"],
            "MACOSX_DEPLOYMENT_TARGET": MAC_OS_MIN_VERSION,
        },
        "cmake_configure_qt_command": CMAKE_CONFIGURE_QT_MAC_COMMAND,
        "cmake_build_qt_command": CMAKE_BUILD_QT_MAC_COMMAND,
    },
]

c = {}
c["change_source"] = []
c["schedulers"] = []
c["builders"] = []

force_scheduler = schedulers.ForceScheduler(
    name=PROJECT_NAME + "_force",
    label="Make installer framework",
    buttonName="Make installer framework",
    builderNames=list(
        map(lambda platform: f"{PROJECT_NAME}_{platform["name"]}", PLATFORMS)
    ),
)
c["schedulers"].append(force_scheduler)

for platform in PLATFORMS:
    qt_code_dir = os.path.join(WORK_DIR, "qt_code")
    qt_build_dir = os.path.join(qt_code_dir, BUILD_SUBDIR_NAME)

    build_factory = util.BuildFactory()

    # Clone qt repository
    build_factory.addStep(
        steps.Git(
            name="Clone Qt repository",
            repourl=QT_GIT_URL,
            mode="full",
            method="clobber",
            submodules=False,
            shallow=True,
            alwaysUseLatest=True,
            workdir=qt_code_dir,
        )
    )

    # Make build dir
    build_factory.addStep(
        steps.MakeDirectory(
            name="Make Qt build directory",
            dir=qt_build_dir,
        )
    )

    # Configure qt via cmake
    build_factory.addStep(
        steps.ShellCommand(
            command=platform["cmake_configure_qt_command"],
            name="Configure Qt build",
            haltOnFailure=True,
            timeout=125 * 60,
            workdir=qt_build_dir,
            env=platform["env"],
        )
    )

    # Build qt
    build_factory.addStep(
        steps.ShellCommand(
            name="Build Qt",
            command=platform["cmake_build_qt_command"],
            haltOnFailure=True,
            workdir=qt_build_dir,
            env=platform["env"],
        )
    )

    # Get uploader
    build_factory.addStep(
        steps.FileDownload(
            name="Download Repka script for Qt",
            mastersrc=os.path.join("worker", REPKA_SCRIPT_NAME),
            workerdest=os.path.join(qt_code_dir, REPKA_SCRIPT_NAME),
            haltOnFailure=True,
        )
    )

    # Send package to rm.nextgis
    build_factory.addStep(
        steps.ShellCommand(
            name=f"Publish {QT_PACKAGE_NAME} to Repka",
            command=[
                "python3",
                REPKA_SCRIPT_NAME,
                "--repo_id",
                platform["repo_id"],
                "--asset_build_path",
                BUILD_SUBDIR_NAME,
                "--packet_name",
                QT_PACKAGE_NAME,
                "--login",
                USERNAME,
                "--password",
                userkey,
            ],
            haltOnFailure=True,
            workdir=qt_code_dir,
            env=platform["env"],
        )
    )

    # 2. Build installer framework
    installer_code_dir = os.path.join(WORK_DIR, "installer_code")
    installer_build_dir = os.path.join(installer_code_dir, BUILD_SUBDIR_NAME)

    # Clone NextGIS installer repository
    build_factory.addStep(
        steps.Git(
            name="Clone installer repository",
            repourl=INSTALLER_GIT_URL,
            mode="full",
            method="clobber",
            submodules=False,
            shallow=True,
            alwaysUseLatest=True,
            workdir=installer_code_dir,
        )
    )

    # Create build directory
    build_factory.addStep(
        steps.MakeDirectory(
            name="Make installer build directory",
            dir=installer_build_dir,
        )
    )

    build_installer_cmd = [
        "python",
        "build_installer_bb.py",
        "--qtdir",
        qt_build_dir,
        "--make",
    ]
    separator = "/"
    if platform["name"] == "win":
        separator = "\\"
        build_installer_cmd.append("nmake")
    elif platform["name"] == "mac":
        build_installer_cmd.append("make")

    build_factory.addStep(
        steps.ShellCommand(
            command=build_installer_cmd,
            name="build_installer_bb.py",
            haltOnFailure=True,
            workdir=os.path.join(installer_code_dir, "qtifw", "tools"),
            env=platform["env"],
        )
    )

    create_archive = [
        "cmake",
        "-E",
        "tar",
        "cfv",
        "archive.zip",
        "--format=zip",
        "qtifw_build" + separator + "bin",
    ]
    build_factory.addStep(
        steps.ShellCommand(
            command=create_archive,
            name="archive installer binaries",
            haltOnFailure=True,
            workdir=installer_code_dir,
            env=platform["env"],
        )
    )

    build_factory.addStep(
        steps.StringDownload(
            "0.0.0\nnow\narchive", workerdest="version.str", workdir=installer_code_dir
        )
    )

    # 3. Upload installer framework to rm.nextgis
    build_factory.addStep(
        steps.FileDownload(
            name="Download Repka script for installer",
            mastersrc=os.path.join("worker", REPKA_SCRIPT_NAME),
            workerdest=os.path.join(installer_code_dir, REPKA_SCRIPT_NAME),
            haltOnFailure=True,
        )
    )

    # Send inst_framework to rm.nextgis
    build_factory.addStep(
        steps.ShellCommand(
            name=f"Publish {INSTALLER_PACKAGE_NAME} to Repka",
            command=[
                "python3",
                REPKA_SCRIPT_NAME,
                "--repo_id",
                platform["repo_id"],
                "--asset_build_path",
                ".",
                "--packet_name",
                INSTALLER_PACKAGE_NAME,
                "--login",
                USERNAME,
                "--password",
                userkey,
            ],
            haltOnFailure=True,
            workdir=installer_code_dir,
            env=platform["env"],
        )
    )

    builder = util.BuilderConfig(
        name=PROJECT_NAME + "_" + platform["name"],
        workernames=[platform["worker"]],
        factory=build_factory,
        description=f"{DESCRIPTION} [" + platform["name"] + "]",
        tags=[platform["os"]],
    )

    c["builders"].append(builder)

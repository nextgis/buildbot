# -*- python -*-
# ex: set syntax=python:

import os

from buildbot.plugins import schedulers, steps, util

c = {}

vm_cpu_count = 6

mac_os_min_version = "10.14"
mac_os_sdks_path = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"

repka_script_src = (
    "https://raw.githubusercontent.com/nextgis/buildbot/master/worker/repka_release.py"
)
repka_script_name = "repka_release.py"
ci_project_name = "create_installer"

username = "buildbot"
userkey = os.environ.get("BUILDBOT_PASSWORD")

c["change_source"] = []
c["schedulers"] = []
c["builders"] = []

project_name = "inst_framework"
forceScheduler = schedulers.ForceScheduler(
    name=project_name + "_force",
    label="Make installer framework",
    buttonName="Make installer framework",
    builderNames=[
        project_name + "_win",
        project_name + "_mac",
    ],
)

c["schedulers"].append(forceScheduler)

qt_git = "https://github.com/nextgis-borsch/lib_qt5.git"

qt_base_args = "-DQT_CONFIGURE_ARGS=-accessibility;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtandroidextras;-skip;qtcharts;-skip;qtconnectivity;-skip;qtdatavis3d;-skip;qtdoc;-skip;qtgamepad;-skip;qtgraphicaleffects;-skip;qtlocation;-skip;qtmultimedia;-skip;qtpurchasing;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qtremoteobjects;-skip;qtscript;-skip;qtscxml;-skip;qtsensors;-skip;qtserialbus;-skip;qtserialport;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebglplugin;-skip;qtwebsockets;-skip;qtwebview;-skip;qt3d;-skip;qtxmlpatterns;-no-feature-ftp;-no-feature-socks5;-nomake;examples;-nomake;tests"

# old options -skip;qtlottie;-skip;qtenginio;-skip;qtquick1;;-skip;qtwebkit

qt_args = [
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

# qt_without_openssl = False
# if qt_without_openssl:
#     qt_args = [ '-DBUILD_STATIC_LIBS=TRUE', '-DWITH_OpenSSL=OFF',
#                 '-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release',
#                 '-DSKIP_DEFAULTS=ON',  '-DQT_CONFIGURE_ARGS=-accessibility;-no-ssl;-no-opengl;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtlocation;-skip;qtmultimedia;-skip;qtserialport;-skip;qtsensors;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qt3d;-skip;qtconnectivity;-skip;qtandroidextras;-skip;qtcanvas3d;-skip;qtcharts;-skip;qtdatavis3d;-skip;qtgamepad;-skip;qtpurchasing;-skip;qtserialbus;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebsockets;-skip;qtxmlpatterns;-skip;qtwebview;-no-feature-ftp;-no-feature-socks5',
#                 '-DWITH_ZLIB=OFF', '-DWITH_Freetype=OFF', '-DWITH_JPEG=OFF',
#                 '-DWITH_PNG=OFF', '-DWITH_SQLite3=OFF', '-DWITH_PostgreSQL=OFF',
#                 '-DCREATE_CPACK_LIGHT=ON',
#               ]

cmake_build = ["cmake", "--build", ".", "--config", "release"]

installer_git = "https://github.com/nextgis/nextgis_installer.git"

logname = "stdio"

platforms = [
    {"name": "win", "worker": "build-win-py3", "repo_id": 5},
    {"name": "mac", "worker": "build-mac-py3", "repo_id": 6},
]

for platform in platforms:
    code_dir_last = "{}_code".format("qt")
    code_dir = os.path.join("build", code_dir_last)
    build_subdir = "build"
    build_dir = os.path.join(code_dir, build_subdir)

    qt_args_set = list(qt_args)

    if platform["name"] == "win":
        qt_args_set.append(qt_base_args + ";-no-opengl")
    elif platform["name"] == "mac":
        qt_args_set.append(qt_base_args + ";-qt-zlib;-qt-libpng;-qt-libjpeg;-no-cups")

    run_args_ext = qt_args_set
    cmake_build_ext = list(cmake_build)
    env = {}
    worker_name = ""
    if platform["name"] == "win":
        run_args_ext.extend(["-G", "Visual Studio 16 2019", "-A", "x64"])
        cmake_build_ext.append("--")
        cmake_build_ext.append("/m:" + str(vm_cpu_count))
    elif platform["name"] == "mac":
        run_args_ext.extend(
            [
                "-DCMAKE_OSX_SYSROOT=" + mac_os_sdks_path + "/MacOSX.sdk",
                "-DCMAKE_OSX_DEPLOYMENT_TARGET=" + mac_os_min_version,
            ]
        )
        cmake_build_ext.append("--")
        cmake_build_ext.append("-j" + str(vm_cpu_count))
        env = {
            "PATH": ["/usr/local/bin", "${PATH}"],
            "MACOSX_DEPLOYMENT_TARGET": mac_os_min_version,
        }

    factory = util.BuildFactory()

    # Get qt repository
    factory.addStep(
        steps.Git(
            repourl=qt_git,
            mode="full",
            method="clobber",
            submodules=False,
            shallow=True,
            alwaysUseLatest=True,
            workdir=code_dir,
        )
    )
    # Make build dir
    factory.addStep(steps.MakeDirectory(dir=build_dir, name="Make build directory"))

    # Configure qt via cmake
    factory.addStep(
        steps.ShellCommand(
            command=["cmake", run_args_ext, ".."],
            name="configure",
            haltOnFailure=True,
            timeout=125 * 60,
            workdir=build_dir,
            env=env,
        )
    )

    # Make qt
    factory.addStep(
        steps.ShellCommand(
            command=cmake_build_ext,
            name="make",
            haltOnFailure=True,
            workdir=build_dir,
            env=env,
        )
    )

    qt_build_dir = build_dir

    # Get uploader
    factory.addStep(
        steps.ShellSequence(
            commands=[
                util.ShellArg(
                    command=["curl", repka_script_src, "-o", repka_script_name, "-s"],
                    logname=logname,
                ),
            ],
            name="Download repka script",
            haltOnFailure=True,
            workdir=code_dir,
            env=env,
        )
    )

    # Send package to rm.nextgis
    factory.addStep(
        steps.ShellCommand(
            command=[
                "python3",
                repka_script_name,
                "--repo_id",
                platform["repo_id"],
                "--asset_build_path",
                build_subdir,
                "--packet_name",
                "inst_framework_qt",
                "--login",
                username,
                "--password",
                userkey,
            ],
            name="Send inst_framework_qt to repka",
            haltOnFailure=True,
            workdir=code_dir,
            env=env,
        )
    )

    # 2. Build installer framework
    code_dir_last = "{}_code".format("installer")
    code_dir = os.path.join("build", code_dir_last)
    build_dir = os.path.join(code_dir, build_subdir)

    # Clone NextGIS installer repository
    factory.addStep(
        steps.Git(
            repourl=installer_git,
            mode="full",
            method="clobber",
            submodules=False,
            shallow=True,
            alwaysUseLatest=True,
            workdir=code_dir,
        )
    )

    # Create build directory
    factory.addStep(
        steps.MakeDirectory(dir=build_dir, name="make directory for installer build")
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

    factory.addStep(
        steps.ShellCommand(
            command=build_installer_cmd,
            name="build_installer_bb.py",
            haltOnFailure=True,
            workdir=os.path.join(code_dir, "qtifw", "tools"),
            env=env,
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
    factory.addStep(
        steps.ShellCommand(
            command=create_archive,
            name="archive installer binaries",
            haltOnFailure=True,
            workdir=code_dir,
            env=env,
        )
    )

    factory.addStep(
        steps.StringDownload(
            "0.0.0\nnow\narchive", workerdest="version.str", workdir=code_dir
        )
    )

    # 3. Upload installer framework to rm.nextgis
    factory.addStep(
        steps.ShellSequence(
            commands=[
                util.ShellArg(
                    command=["curl", repka_script_src, "-o", repka_script_name, "-s"],
                    logname=logname,
                ),
            ],
            name="Download repka script",
            haltOnFailure=True,
            workdir=code_dir,
            env=env,
        )
    )

    # Send inst_framework to rm.nextgis
    factory.addStep(
        steps.ShellCommand(
            command=[
                "python3",
                repka_script_name,
                "--repo_id",
                platform["repo_id"],
                "--asset_build_path",
                ".",
                "--packet_name",
                "inst_framework",
                "--login",
                username,
                "--password",
                userkey,
            ],
            name="Send inst_framework to repka",
            haltOnFailure=True,
            workdir=code_dir,
            env=env,
        )
    )

    builder = util.BuilderConfig(
        name=project_name + "_" + platform["name"],
        workernames=[platform["worker"]],
        factory=factory,
        description="Create installer framework [" + platform["name"] + "]",
    )

    c["builders"].append(builder)

# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import multiprocessing
import bbconf

c = {}

vm_cpu_count = 8

mac_os_min_version = '10.10'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

ngftp = 'ftp://192.168.255.51/software/installer/src/'
ngftp_user = bbconf.ftp_mynextgis_user
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/ftp_uploader.py'
upload_script_name = 'ftp_upload.py'
ci_project_name = 'create_installer'

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

project_name = 'inst_framework'
forceScheduler = schedulers.ForceScheduler(
                            name=project_name + "_force",
                            label="Make installer framework",
                            buttonName="Make installer framework",
                            builderNames=[
                                            project_name + "_win",
                                            project_name + "_mac",
                                        ])
c['schedulers'].append(forceScheduler)

qt_git = 'git://github.com/nextgis-borsch/lib_qt5.git'

qt_without_openssl = True

qt_args = [ '-DBUILD_STATIC_LIBS=TRUE', '-DWITH_OpenSSL_EXTERNAL=ON',
            '-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release',
            '-DSKIP_DEFAULTS=ON',  '-DQT_CONFIGURE_ARGS=-accessibility;-no-opengl;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtlocation;-skip;qtmultimedia;-skip;qtserialport;-skip;qtsensors;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qt3d;-skip;qtconnectivity;-skip;qtandroidextras;-skip;qtcanvas3d;-skip;qtcharts;-skip;qtdatavis3d;-skip;qtgamepad;-skip;qtpurchasing;-skip;qtserialbus;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebsockets;-skip;qtxmlpatterns;-skip;qtwebview;-no-feature-ftp;-no-feature-socks5',
            '-DWITH_ZLIB=OFF', '-DWITH_Freetype=OFF', '-DWITH_JPEG=OFF',
            '-DWITH_PNG=OFF', '-DWITH_SQLite3=OFF', '-DWITH_PostgreSQL=OFF',
            '-DCREATE_CPACK_LIGHT=ON',
          ]
# For qt 5.10 -skip;qtwebglplugin;

if qt_without_openssl:
    qt_args = [ '-DBUILD_STATIC_LIBS=TRUE', '-DWITH_OpenSSL=OFF',
                '-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release',
                '-DSKIP_DEFAULTS=ON',  '-DQT_CONFIGURE_ARGS=-accessibility;-no-ssl;-no-opengl;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtlocation;-skip;qtmultimedia;-skip;qtserialport;-skip;qtsensors;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qt3d;-skip;qtconnectivity;-skip;qtandroidextras;-skip;qtcanvas3d;-skip;qtcharts;-skip;qtdatavis3d;-skip;qtgamepad;-skip;qtpurchasing;-skip;qtserialbus;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebsockets;-skip;qtxmlpatterns;-skip;qtwebview;-no-feature-ftp;-no-feature-socks5',
                '-DWITH_ZLIB=OFF', '-DWITH_Freetype=OFF', '-DWITH_JPEG=OFF',
                '-DWITH_PNG=OFF', '-DWITH_SQLite3=OFF', '-DWITH_PostgreSQL=OFF',
                '-DCREATE_CPACK_LIGHT=ON',
              ]

cmake_build = ['cmake', '--build', '.', '--config', 'release']

installer_git = 'git://github.com/nextgis/nextgis_installer.git'

os_types = ['win', 'mac']
for os_type in os_types:

    code_dir_last = '{}_code'.format('qt')
    code_dir = os.path.join('build', code_dir_last)
    build_subdir = 'build'
    build_dir = os.path.join(code_dir, build_subdir)

    run_args_ext = list(qt_args)
    cmake_build_ext = list(cmake_build)
    env = {}
    worker_name = ''
    if os_type == 'win':
        run_args_ext.extend(['-G', 'Visual Studio 15 2017'])
        cmake_build_ext.append('--')
        cmake_build_ext.append('/m:' + str(vm_cpu_count))
    elif os_type == 'mac':
        run_args_ext.extend(['-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + mac_os_min_version])
        cmake_build_ext.append('--')
        cmake_build_ext.append('-j' + str(vm_cpu_count))
        env = {
            'PATH': [
                        "/usr/local/bin",
                        "${PATH}"
                    ],
            'MACOSX_DEPLOYMENT_TARGET': mac_os_min_version,
        }

    factory = util.BuildFactory()

    # Get qt repository
    factory.addStep(steps.Git(repourl=qt_git, mode='full', method='clobber',
                            submodules=False, shallow=True, alwaysUseLatest=True,
                            workdir=code_dir))
    # Make build dir
    factory.addStep(steps.MakeDirectory(dir=build_dir, name="Make build directory"))

    # Configure qt via cmake
    factory.addStep(steps.ShellCommand(command=["cmake", run_args_ext, '..'],
                                       name="configure",
                                       haltOnFailure=True,
                                       timeout = 60 * 40,
                                       workdir=build_dir,
                                       env=env))

    # Make qt
    factory.addStep(steps.ShellCommand(command=cmake_build_ext,
                                       name="make",
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))


    qt_build_dir = build_dir

    # Get uploader
    factory.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                        name="download upload script",
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    # Send package to ftp
    factory.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_' + os_type + '/qt',
                                                '--build_path', build_subdir],
                                        name="send package to ftp",
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    # 2. Build installer framework
    code_dir_last = '{}_code'.format('installer')
    code_dir = os.path.join('build', code_dir_last)
    build_dir = os.path.join(code_dir, build_subdir)

    # Clone NextGIS installer repository
    factory.addStep(steps.Git(repourl=installer_git, mode='full', method='clobber',
                                submodules=False, shallow = True,
                                alwaysUseLatest=True, workdir=code_dir))

    # Create build directory
    factory.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="make directory for installer build"))

    build_installer_cmd = ['python', 'build_installer_bb.py', '--qtdir',
                            qt_build_dir, '--make']
    separator = '/'
    if os_type == 'win':
        separator = '\\'
        build_installer_cmd.append('nmake')
    elif os_type == 'mac':
        build_installer_cmd.append('make')


    factory.addStep(steps.ShellCommand(command=build_installer_cmd,
                                        name="build_installer_bb.py",
                                        haltOnFailure=True,
                                        workdir=os.path.join(code_dir, 'qtifw', 'tools'),
                                        env=env))

    create_archive = ['cmake', '-E', 'tar', 'cfv', 'archive.zip', '--format=zip', 'qtifw_build' + separator + 'bin']
    factory.addStep(steps.ShellCommand(command=create_archive,
                                        name="archive installer binaries",
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    factory.addStep(steps.StringDownload("0.0.0\nnow\narchive",
                                        workerdest="version.str",
                                        workdir=code_dir))

    # 3. Upload installer framework to ftp
    factory.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                        name="download upload script",
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    factory.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_' + os_type,
                                                '--build_path', '.'],
                                           name="send package to ftp",
                                           haltOnFailure=True,
                                           workdir=code_dir,
                                           env=env))

    builder = util.BuilderConfig(name = project_name + '_' + os_type,
                                workernames = ['build-' + os_type],
                                factory = factory,
                                description="Create installer framework [" + os_type + "]")

    c['builders'].append(builder)

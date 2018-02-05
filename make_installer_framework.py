# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import multiprocessing
import bbconf

c = {}

vm_cpu_count = 8

max_os_min_version = '10.11'
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
                            builderNames=[
                                            project_name + "_win",
                                            project_name + "_mac",
                                        ])
c['schedulers'].append(forceScheduler)

# 1. Build qt static
# 2. Build installer
# 3. Upload to ftp

#==============================================================================#
code_dir_last = '{}_code'.format('qt')
code_dir = os.path.join('build', code_dir_last)
build_subdir = 'build'
build_dir = os.path.join(code_dir, build_subdir)

qt_git = 'git://github.com/nextgis-borsch/lib_qt5.git'

qt_args = [ '-DBUILD_STATIC_LIBS=TRUE', '-DWITH_OpenSSL_EXTERNAL=ON',
            '-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release',
            '-DSKIP_DEFAULTS=ON',  '-DQT_CONFIGURE_ARGS=-accessibility;-no-opengl;-no-icu;-no-sql-sqlite;-no-qml-debug;-skip;qtactiveqt;-skip;qtlocation;-skip;qtmultimedia;-skip;qtserialport;-skip;qtsensors;-skip;qtxmlpatterns;-skip;qtquickcontrols;-skip;qtquickcontrols2;-skip;qt3d;-skip;qtconnectivity;-skip;qtandroidextras;-skip;qtcanvas3d;-skip;qtcharts;-skip;qtdatavis3d;-skip;qtgamepad;-skip;qtpurchasing;-skip;qtquickcontrols2;-skip;qtserialbus;-skip;qtspeech;-skip;qtvirtualkeyboard;-skip;qtwayland;-skip;qtwebchannel;-skip;qtwebengine;-skip;qtwebglplugin;-skip;qtwebsockets;-skip;qtwebview;-no-feature-ftp;-no-feature-socks5',
            '-DWITH_ZLIB=OFF', '-DWITH_Freetype=OFF', '-DWITH_JPEG=OFF',
            '-DWITH_PNG=OFF', '-DWITH_SQLite3=OFF', '-DWITH_PostgreSQL=OFF',
            '-DCREATE_CPACK=ON',
          ]
cmake_build = ['cmake', '--build', '.', '--config', 'release', '--']

installer_git = 'git://github.com/nextgis/nextgis_installer.git'

# Windows ##################################################################
win_run_args = list(qt_args)
win_cmake_build = list(cmake_build)
win_cmake_build.append('/m:' + str(vm_cpu_count))

mac_run_args = list(qt_args)
mac_cmake_build = list(cmake_build)
mac_run_args.extend(['-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + max_os_min_version])
mac_cmake_build.append('-j' + str(vm_cpu_count))

factory_win = util.BuildFactory()
factory_mac = util.BuildFactory()
# Install common dependencies

factory_win.addStep(steps.Git(repourl=qt_git,
                            mode='full',
                            method='clobber',
                            submodules=False,
                            shallow=True,
                            workdir=code_dir))
factory_mac.addStep(steps.Git(repourl=qt_git,
                            mode='full',
                            method='clobber',
                            submodules=False,
                            shallow = True,
                            workdir=code_dir))

# make build dir
factory_win.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory 32 bit"))
factory_mac.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory"))

# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", win_run_args, '-G', 'Visual Studio 15 2017', '../'],
                                       name="configure 32 bit",
                                       description=["cmake", "configure for win32"],
                                       descriptionDone=["cmake", "configured for win32"],
                                       haltOnFailure=True,
                                       workdir=build_dir))
env = {
    'PATH': [
                "/usr/local/bin",
                "${PATH}"
            ],
}
factory_mac.addStep(steps.ShellCommand(command=["cmake", mac_run_args, '..'],
                                       name="configure",
                                       description=["cmake", "configure"],
                                       descriptionDone=["cmake", "configured"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

# make
factory_win.addStep(steps.ShellCommand(command=win_cmake_build,
                                       name="make 32 bit",
                                       description=["cmake", "make for win32"],
                                       descriptionDone=["cmake", "made for win32"],
                                       haltOnFailure=True,
                                       workdir=build_dir))
factory_mac.addStep(steps.ShellCommand(command=mac_cmake_build,
                                       name="make",
                                       description=["cmake", "make"],
                                       descriptionDone=["cmake", "made"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

qt_build_dir = build_dir

factory_win.addStep(steps.ShellCommand(command=['cpack', '.'],
                                       name="pack qt",
                                       description=["pack", "for win32"],
                                       descriptionDone=["packed", "for win32"],
                                       haltOnFailure=True,
                                       workdir=build_dir))
factory_mac.addStep(steps.ShellCommand(command=['cpack', '.'],
                                       name="pack qt",
                                       description=["pack", "for MacOS X"],
                                       descriptionDone=["packed", "for MacOS X"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

factory_win.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                       name="download upload script",
                                       description=["curl", "download upload script"],
                                       descriptionDone=["curl", "downloaded upload script"],
                                       haltOnFailure=True,
                                       workdir=code_dir))
factory_mac.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                       name="download upload script",
                                       description=["curl", "download upload script"],
                                       descriptionDone=["curl", "downloaded upload script"],
                                       haltOnFailure=True,
                                       workdir=code_dir))

factory_win.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_win' + '/qt',
                                                '--build_path', build_subdir],
                                       name="send 32 bit package to ftp",
                                       description=["send", "32 bit package to ftp"],
                                       descriptionDone=["sent", "32 bit package to ftp"],
                                       haltOnFailure=True,
                                       workdir=code_dir))
factory_mac.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_macos' + '/qt',
                                                '--build_path', build_subdir],
                                       name="send package to ftp",
                                       description=["send", "package to ftp"],
                                       descriptionDone=["sent", "package to ftp"],
                                       haltOnFailure=True,
                                       workdir=code_dir))

# 2. Build installer framework
code_dir_last = '{}_code'.format('installer')
code_dir = os.path.join('build', code_dir_last)
build_dir = os.path.join(code_dir, build_subdir)

factory_win.addStep(steps.Git(repourl=installer_git,
                                mode='full',
                                method='clobber',
                                submodules=False,
                                shallow = True,
                                workdir=code_dir))
factory_mac.addStep(steps.Git(repourl=installer_git,
                                mode='full',
                                method='clobber',
                                submodules=False,
                                shallow = True,
                                workdir=code_dir))

factory_win.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory for installer build"))
factory_mac.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory for installer build"))

factory_win.addStep(steps.ShellCommand(command=['python', 'build_installer_bb.py',
                                                '--qtdir', qt_build_dir,
                                                '--make', 'nmake'],
                                        name="build_installer.py",
                                        description=["build_installer.py", "make"],
                                        descriptionDone=["build_installer.py", "made"],
                                        haltOnFailure=True,
                                        workdir=os.path.join(code_dir, 'qtifw', 'tools')))
factory_mac.addStep(steps.ShellCommand(command=['python', 'build_installer_bb.py',
                                                '--qtdir', qt_build_dir,
                                                '--make', 'make'],
                                        name="build_installer.py",
                                        description=["build_installer.py", "make"],
                                        descriptionDone=["build_installer.py", "made"],
                                        haltOnFailure=True,
                                        workdir=os.path.join(code_dir, 'qtifw', 'tools'),
                                        env=env))

create_archive = ['cmake', '-E', 'tar', 'cfv', 'archive.zip', '--format=zip', os.path.join(build_dir, 'qtifw_pkg')]
factory_win.addStep(steps.ShellCommand(command=create_archive,
                                       name="archive",
                                       description=["cmake", "make archive"],
                                       descriptionDone=["cmake", "made archive"],
                                       haltOnFailure=True,
                                       workdir=build_dir))
factory_mac.addStep(steps.ShellCommand(command=create_archive,
                                       name="archive",
                                       description=["cmake", "make archive"],
                                       descriptionDone=["cmake", "made archive"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

factory_win.addStep(steps.StringDownload("0.0.0\nnow\narchive",
                                        workerdest="version.str",
                                        workdir=build_dir))
factory_mac.addStep(steps.StringDownload("0.0.0\nnow\narchive",
                                        workerdest="version.str",
                                        workdir=build_dir))

# 3. Upload installer framework to ftp
factory_win.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                       name="download upload script",
                                       haltOnFailure=True,
                                       workdir=code_dir))
factory_mac.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                       name="download upload script",
                                       haltOnFailure=True,
                                       workdir=code_dir))

factory_win.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_win',
                                                '--build_path', build_subdir],
                                       name="send 32 bit package to ftp",
                                       haltOnFailure=True,
                                       workdir=code_dir))
factory_mac.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                '--ftp_user', ngftp_user, '--ftp',
                                                ngftp + project_name + '_macos',
                                                '--build_path', build_subdir],
                                       name="send package to ftp",
                                       haltOnFailure=True,
                                       workdir=code_dir))

builder_win = util.BuilderConfig(name = project_name + '_win', workernames = ['build-win'], factory = factory_win)
builder_mac = util.BuilderConfig(name = project_name + '_mac', workernames = ['build-mac'], factory = factory_mac)

c['builders'].append(builder_win)
c['builders'].append(builder_mac)

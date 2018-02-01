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

qt_ver_major = 5
qt_ver_minor = 10
qt_ver_patch = 0

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

# 1. Build openssl static
openssl_args = ['-DOPENSSL_NO_DYNAMIC_ENGINE=ON', '-DBUILD_STATIC_LIBS=TRUE',
                '-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release',
                '-DSKIP_DEFAULTS=ON']
openssl_git = 'git://github.com/nextgis-borsch/lib_openssl.git'
cmake_build = ['cmake', '--build', '.', '--config', 'release', '--']

# Windows specific
win_run_args = list(openssl_args)
win_cmake_build = list(cmake_build)
win_cmake_build.append('/m:' + str(vm_cpu_count))

# Mac OS X specific
mac_run_args = list(openssl_args)
mac_cmake_build = list(cmake_build)
mac_run_args.extend(['-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + max_os_min_version])
mac_cmake_build.append('-j' + str(vm_cpu_count))

code_dir_last = '{}_code'.format('openssl')
code_dir = os.path.join('build', code_dir_last)
build_dir = os.path.join(code_dir, 'build')
open_ssl_include1 = os.path.join(code_dir, 'include')
open_ssl_include2 = os.path.join(build_dir, 'include')
open_ssl_lib = os.path.join(build_dir, 'release')

# Windows ##################################################################

factory_win = util.BuildFactory()
# Install common dependencies
install_dependencies(factory_win, repository['requirements'], 'win')

factory_win.addStep(steps.Git(repourl=openssl_git,
                                mode='full',
                                submodules=False,
                                workdir=code_dir))

# make build dir
factory_win.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory 32 bit"))

# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", win_run_args, '-G', 'Visual Studio 15 2017', '../'],
                                       name="configure 32 bit",
                                       description=["cmake", "configure for win32"],
                                       descriptionDone=["cmake", "configured for win32"],
                                       haltOnFailure=True,
                                       workdir=build_dir))

# make
factory_win.addStep(steps.ShellCommand(command=win_cmake_build,
                                       name="make 32 bit",
                                       description=["cmake", "make for win32"],
                                       descriptionDone=["cmake", "made for win32"],
                                       haltOnFailure=True,
                                       workdir=build_dir))

# 2. Build qt5 static minimal

code_dir_last = '{}_code'.format('qt')
code_dir = os.path.join('build', code_dir_last)
build_dir = os.path.join(code_dir, 'build')

# make build dir
factory_win.addStep(steps.MakeDirectory(dir=code_dir,
                                        name="Make qt directory"))

qt_version = '{}.{}.{}'.format(qt_ver_major, qt_ver_minor, qt_ver_patch)
qt_subfolder = 'single/'
qt_input_name = 'qt-everywhere-src-{}'.format(qt_version)
qt_url = 'http://download.qt.io/official_releases/qt/{}.{}/{}/{}{}.tar.xz'.format(qt_ver_major, qt_ver_minor, qt_version, qt_subfolder, qt_input_name)

qt_args = [ '-release', '-static', '-opensource', '-confirm-license',
            '-accessibility', '-no-opengl', '-no-icu', '-no-sql-sqlite',
            '-no-qml-debug', '-nomake', 'examples', '-nomake', 'tests', '-skip',
            'qtactiveqt', '-skip', 'qtlocation', '-skip', 'qtmultimedia', '-skip',
            'qtserialport', '-skip', 'qtsensors', '-skip', 'qtxmlpatterns',
            '-skip', 'qtquickcontrols', '-skip', 'qtquickcontrols2', '-skip',
            'qt3d', '-openssl-linked']

factory_win.addStep(steps.ShellCommand(command=["curl", qt_url, '-o', 'qt.tar.xz', '-s'],
                                       name="download qt",
                                       description=["curl", "download qt"],
                                       descriptionDone=["curl", "downloaded qt"],
                                       haltOnFailure=True,
                                       workdir=code_dir))

factory_win.addStep(steps.ShellCommand(command=["cmake", '-E', 'tar', 'xzf', 'qt.tar.xz'],
                                       name="extract qt",
                                       description=["cmake", "extract qt"],
                                       descriptionDone=["cmake", "extracted qt"],
                                       haltOnFailure=True,
                                       workdir=code_dir))

factory_win.addStep(steps.ShellCommand(command=["configure", '-prefix', '%CD%\\qtbase',
                                                '-platform', 'win32-msvc2017', qt_args,
                                                '-I', open_ssl_include1, '-I', open_ssl_include2,
                                                '-L', open_ssl_lib, '-l', 'Gdi32', '-l', 'User32'],
                                       name="configure qt",
                                       description=["configure", "qt"],
                                       descriptionDone=["configure", "qt"],
                                       haltOnFailure=True,
                                       workdir=os.path.join(code_dir, 'qt_input_name')))

# 3. Build installer framework
# 4. Upload installer framework to ftp

builder_win = util.BuilderConfig(name = project_name + '_win', workernames = ['build-win'], factory = factory_win)

c['builders'].append(builder_win)

# MacOS X ##################################################################
code_dir_last = '{}_code'.format('openssl')
code_dir = os.path.join('build', code_dir_last)
build_dir = os.path.join(code_dir, 'build')

factory_mac = util.BuildFactory()

factory_mac.addStep(steps.Git(repourl=openssl_git,
                                mode='full',
                                submodules=False,
                                workdir=code_dir))

env = {
    'PATH': [
                "/usr/local/bin",
                "${PATH}"
            ],
}

# make build dir
factory_mac.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make directory"))

# configure view cmake
factory_mac.addStep(steps.ShellCommand(command=["cmake", mac_run_args, '..'],
                                       name="configure",
                                       description=["cmake", "configure"],
                                       descriptionDone=["cmake", "configured"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

# make
factory_mac.addStep(steps.ShellCommand(command=mac_cmake_build,
                                       name="make",
                                       description=["cmake", "make"],
                                       descriptionDone=["cmake", "made"],
                                       haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

builder_mac = util.BuilderConfig(name = project_name + '_mac', workernames = ['build-mac'], factory = factory_mac)

c['builders'].append(builder_mac)

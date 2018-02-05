# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import multiprocessing
import bbconf

c = {}

repositories = [
    {'repo':'lib_z', 'args':[], 'requirements':[]},
    {'repo':'lib_openssl', 'args':['-DOPENSSL_NO_DYNAMIC_ENGINE=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON'], 'requirements':[]},
    {'curl', 'repo':'lib_curl', 'args':['-DENABLE_INET_PTON=OFF', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DHTTP_ONLY=ON', '-DCMAKE_USE_OPENSSL=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DBUILD_TESTING=ON'], 'requirements':[]},
    # {'repo':'lib_qt5', 'args':['-DCREATE_CPACK=ON','-DQT_CONFIGURE_ARGS=-accessibility;...'], 'requirements':[]},
]

vm_cpu_count = 8

max_os_min_version = '10.11'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

release_script_src = 'https://raw.githubusercontent.com/nextgis-borsch/borsch/master/opt/github_release.py'
script_name = 'github_release.py'
username = 'bishopgis'
userkey = bbconf.githubAPIToken
ngftp = 'ftp://192.168.255.51/software/installer/src/'
ngftp_user = bbconf.ftp_mynextgis_user
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/ftp_uploader.py'
upload_script_name = 'ftp_upload.py'
ci_project_name = 'create_installer'

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

def install_dependencies(factory, requirements, os):
    for requirement in requirements:
        if requirement == 'perl' and os == 'win': # This is example. Perl already installed in VM.
            # Upload distro to worker
            factory.addStep(steps.FileDownload(
                            mastersrc="/opt/buildbot/distrib/perl.msi",
                            workerdest="perl.msi"))
            # Execute install
            factory.addStep(steps.ShellCommand(command=['msiexec', '/package', 'perl.msi', '/quiet', '/norestart'],
                                                name="install " + requirement,
                                                description=[requirement, "install"],
                                                descriptionDone=[requirement, "installed"],
                                                haltOnFailure=True))


for repository in repositories:
    project_name = repository['repo']
    repourl = 'git://github.com/nextgis-borsch/{}.git'.format(project_name)
    git_project_name = 'nextgis-borsch/{}'.format(project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-workdir',
                           branches = ['master'],
                           pollinterval = 600,) # TODO: change 10min to 2 hours (7200)
    c['change_source'].append(git_poller)

    scheduler1 = schedulers.SingleBranchScheduler(
                                name=project_name,
                                change_filter=util.ChangeFilter(project = git_project_name, branch="master"),
                                treeStableTimer=1*60,
                                builderNames=[
                                                project_name + "_win",
                                                project_name + "_mac",
                                            ])
    c['schedulers'].append(scheduler1)
    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                builderNames=[
                                                project_name + "_win",
                                                project_name + "_mac",
                                            ])
    c['schedulers'].append(forceScheduler)

    code_dir_last = '{}_code'.format(project_name)
    code_dir = os.path.join('build', code_dir_last)

    run_args = repository['args']
    run_args.extend(['-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release', '-DSKIP_DEFAULTS=ON'])
    cmake_build = ['cmake', '--build', '.', '--config', 'release', '--']

    # Windows specific
    win_run_args = list(run_args)
    win_cmake_build = list(cmake_build)
    win_run_args.append('-DBUILD_SHARED_LIBS=TRUE')
    win_cmake_build.append('/m:' + str(vm_cpu_count))

    # Mac OS X specific
    mac_run_args = list(run_args)
    mac_cmake_build = list(cmake_build)
    mac_run_args.extend(['-DOSX_FRAMEWORK=ON', '-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + max_os_min_version])
    mac_cmake_build.append('-j' + str(vm_cpu_count))

    # Windows ##################################################################

    factory_win = util.BuildFactory()
    # Install common dependencies
    install_dependencies(factory_win, repository['requirements'], 'win')

    factory_win.addStep(steps.Git(repourl=repourl, mode='full', shallow=True, method='clobber', submodules=False, workdir=code_dir))
    factory_win.addStep(steps.ShellCommand(command=["curl", release_script_src, '-o', script_name, '-s', '-L'],
                                           name="download script",
                                           description=["curl", "download script"],
                                           descriptionDone=["curl", "downloaded script"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    factory_win.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                           name="download upload script",
                                           description=["curl", "download upload script"],
                                           descriptionDone=["curl", "downloaded upload script"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    # Build 32bit ##############################################################
    build_subdir = 'build32'
    build_dir = os.path.join(code_dir, build_subdir)
    env = {
        'PYTHONPATH': 'C:\\Python27_32',
        'LANG': 'en_US',
        'PATH': [
                    "C:\\buildbot\worker\\" + project_name + "_win\\build\\" + code_dir_last + "\\" + build_subdir + "\\release",
                    "${PATH}"
                ],
    }
    # make build dir
    factory_win.addStep(steps.MakeDirectory(dir=build_dir,
                                            name="Make directory 32 bit"))

    # configure view cmake
    factory_win.addStep(steps.ShellCommand(command=["cmake", win_run_args, '-G', 'Visual Studio 15 2017', '../'],
                                           name="configure 32 bit",
                                           description=["cmake", "configure for win32"],
                                           descriptionDone=["cmake", "configured for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make
    factory_win.addStep(steps.ShellCommand(command=win_cmake_build,
                                           name="make 32 bit",
                                           description=["cmake", "make for win32"],
                                           descriptionDone=["cmake", "made for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make tests
    factory_win.addStep(steps.ShellCommand(command=['ctest', '-C', 'release'],
                                           name="test 32 bit",
                                           description=["test", "for win32"],
                                           descriptionDone=["tested", "for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make package
    factory_win.addStep(steps.ShellCommand(command=['cpack', '.'],
                                           name="pack 32 bit",
                                           description=["pack", "for win32"],
                                           descriptionDone=["packed", "for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))
    # send package to github
    factory_win.addStep(steps.ShellCommand(command=['python', script_name, '--login', username, '--key', userkey, '--build_path', build_subdir],
                                           name="send 32 bit package to github",
                                           description=["send", "32 bit package to github"],
                                           descriptionDone=["sent", "32 bit package to github"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    # upload to ftp
    factory_win.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                    '--ftp_user', ngftp_user, '--ftp',
                                                    ngftp + project_name + '_win32',
                                                    '--build_path', build_subdir],
                                           name="send 32 bit package to ftp",
                                           description=["send", "32 bit package to ftp"],
                                           descriptionDone=["sent", "32 bit package to ftp"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    factory_win.addStep(steps.Trigger(schedulerNames=[ci_project_name + '_win32'],
                                      waitForFinish=True))

    # Build 64bit ##############################################################
    build_subdir = 'build64'
    build_dir = os.path.join(code_dir, build_subdir)
    env = env = {
        'PYTHONPATH': 'C:\\Python27',
        'LANG': 'en_US',
        'PATH': [
                    "C:\\buildbot\worker\\" + project_name + "_win\\build\\" + code_dir_last + "\\" + build_subdir + "\\release",
                    "${PATH}"
                ],
    }
    # make build dir
    factory_win.addStep(steps.MakeDirectory(dir=build_dir,
                                            name="Make directory 64 bit"))

    # configure view cmake
    factory_win.addStep(steps.ShellCommand(command=["cmake", win_run_args, '-G', 'Visual Studio 15 2017 Win64', '../'],
                                           name="configure 64 bit",
                                           description=["cmake", "configure for win64"],
                                           descriptionDone=["cmake", "configured for win64"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make
    factory_win.addStep(steps.ShellCommand(command=win_cmake_build,
                                       name="make 64 bit",
                                       description=["cmake", "make for win64"],
                                       descriptionDone=["cmake", "made for win64"], haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

    # make tests
    factory_win.addStep(steps.ShellCommand(command=['ctest', '-C', 'release'],
                                           name="test 64 bit",
                                           description=["test", "for win64"],
                                           descriptionDone=["tested", "for win64"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))


    # make package
    factory_win.addStep(steps.ShellCommand(command=['cpack', '.'],
                                           name="pack 64 bit",
                                           description=["pack", "for win64"],
                                           descriptionDone=["packed", "for win64"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))
    # send package to github
    factory_win.addStep(steps.ShellCommand(command=['python', script_name, '--login', username, '--key', userkey, '--build_path', build_subdir],
                                           name="send 64 bit package to github",
                                           description=["send", "64 bit package to github"],
                                           descriptionDone=["sent", "64 bit package to github"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    # upload to ftp
    factory_win.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                    '--ftp_user', ngftp_user, '--ftp',
                                                    ngftp + project_name + '_win64',
                                                    '--build_path', build_subdir],
                                           name="send 64 bit package to ftp",
                                           description=["send", "64 bit package to ftp"],
                                           descriptionDone=["sent", "64 bit package to ftp"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    factory_win.addStep(steps.Trigger(schedulerNames=[ci_project_name + '_win64'],
                                      waitForFinish=True))

    builder_win = util.BuilderConfig(name = project_name + '_win', workernames = ['build-win'], factory = factory_win)

    c['builders'].append(builder_win)


    # MacOS X ##################################################################

    factory_mac = util.BuildFactory()
    # Install common dependencies
    install_dependencies(factory_mac, repository['requirements'], 'mac')

    factory_mac.addStep(steps.Git(repourl=repourl, mode='full', shallow=True, method='clobber', submodules=False, workdir=code_dir))
    factory_mac.addStep(steps.ShellCommand(command=["curl", release_script_src, '-o', script_name, '-s', '-L'],
                                           name="download script",
                                           description=["curl", "download script"],
                                           descriptionDone=["curl", "downloaded script"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    factory_mac.addStep(steps.ShellCommand(command=["curl", upload_script_src, '-o', upload_script_name, '-s'],
                                           name="download upload script",
                                           description=["curl", "download upload script"],
                                           descriptionDone=["curl", "downloaded upload script"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    # Build 32bit ##############################################################
    build_subdir = 'build'
    build_dir = os.path.join(code_dir, build_subdir)
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

    # make tests
    factory_mac.addStep(steps.ShellCommand(command=['ctest', '-C', 'release'],
                                           name="test",
                                           description=["test", "for MacOS X"],
                                           descriptionDone=["tested", "for MacOS X"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make package
    factory_mac.addStep(steps.ShellCommand(command=['cpack', '.'],
                                           name="pack 32 bit",
                                           description=["pack", "for MacOS X"],
                                           descriptionDone=["packed", "for MacOS X"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))
    # send package to github
    factory_mac.addStep(steps.ShellCommand(command=['python', script_name, '--login', username, '--key', userkey, '--build_path', build_subdir],
                                           name="send MacOS X package to github",
                                           description=["send", "MacOS X package to github"],
                                           descriptionDone=["sent", "MacOS X package to github"],
                                           haltOnFailure=True,
                                           workdir=code_dir,
                                           env=env))

    factory_mac.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                    '--ftp_user', ngftp_user, '--ftp',
                                                    ngftp + project_name + '_macos',
                                                    '--build_path', build_subdir],
                                           name="send package to ftp",
                                           description=["send", "package to ftp"],
                                           descriptionDone=["sent", "package to ftp"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    factory_mac.addStep(steps.Trigger(schedulerNames=[ci_project_name + '_mac'],
                                      waitForFinish=True))

    builder_mac = util.BuilderConfig(name = project_name + '_mac', workernames = ['build-mac'], factory = factory_mac)

    c['builders'].append(builder_mac)

# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import multiprocessing
import bbconf

c = {}

repositories = [
    {'repo':'z', 'args':[], 'requirements':[]},
    {'repo':'openssl', 'args':['-DOPENSSL_NO_DYNAMIC_ENGINE=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON'], 'requirements':['perl']}, # TODO: Install additional programs or requirements
]

max_os_min_version = '10.11'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

release_script_src = 'https://raw.githubusercontent.com/nextgis-borsch/borsch/master/opt/github_release.py'
script_name = 'github_release.py'
username = 'bishopgis'
userkey = bbconf.githubAPIToken

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

for repository in repositories:
    project_name = repository['repo']
    repourl = 'git://github.com/nextgis-borsch/lib_{}.git'.format(project_name)
    git_project_name = 'nextgis-borsch/lib_{}'.format(project_name)
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
                                builderNames=[project_name + "_win"]) # TODO: project_name + "_mac",
    c['schedulers'].append(scheduler1)
    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                builderNames=[project_name + "_win"]) # TODO: project_name + "_mac",
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
    win_cmake_build.append('/m:' + str(multiprocessing.cpu_count()))

    # Mac OS X specific
    mac_run_args = list(run_args)
    mac_cmake_build = list(cmake_build)
    mac_run_args.extend(['-DOSX_FRAMEWORK=ON', '-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + max_os_min_version])
    mac_cmake_build.append('-j' + str(multiprocessing.cpu_count()))

    ############################################################################

    factory_win = util.BuildFactory()
    factory_win.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))
    factory_win.addStep(steps.ShellCommand(command=["curl", release_script_src, '-o', script_name, '-s'],
                                           name="download script",
                                           description=["curl", "download script"],
                                           descriptionDone=["curl", "downloaded script"],
                                           haltOnFailure=True,
                                           workdir=code_dir))

    # Build 32bit ##############################################################
    build_subdir = 'build32'
    build_dir = os.path.join(code_dir, build_subdir)
    env = {'PYTHONPATH': 'C:\\Python27_32', 'LANG': 'en_US'}
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
    factory_win.addStep(steps.ShellCommand(command=['ctest', '.'],
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

    # Build 64bit ##############################################################
    build_subdir = 'build64'
    build_dir = os.path.join(code_dir, build_subdir)
    env = {'PYTHONPATH': 'C:\\Python27', 'LANG': 'en_US'}
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
    factory_win.addStep(steps.ShellCommand(command=['ctest', '.'],
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

    builder_win = util.BuilderConfig(name = project_name + '_win', workernames = ['build-win'], factory = factory_win)

    c['builders'].append(builder_win)

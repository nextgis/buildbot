# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import multiprocessing

c = {}

repositories = [
    {'repo':'z', 'args':[]},
]

for repository in repositories:
    project_name = repository['repo']
    repourl = 'git://github.com/nextgis-borsch/lib_{}.git'.formar(project_name)
    git_project_name = 'nextgis-borsch/lib_{}'.format(project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-workdir',
                           branches = ['master', 'dev'],
                           pollinterval = 600,) # TODO: change 10min on 2 hours (7200)
    c['change_source'].append(git_poller)

    scheduler1 = schedulers.SingleBranchScheduler(
                                name=project_name,
                                change_filter=util.ChangeFilter(project = git_project_name, branch="master"),
                                treeStableTimer=1*60,
                                builderNames=[project_name + "_win"]) # TODO: project_name + "_mac",
    c['schedulers'].append(scheduler1)
    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                builderNames=[project_name + "_win"])) # TODO: project_name + "_mac",
    c['schedulers'].append(forceScheduler)

    code_dir_last = '{}_code'.format(project_name)
    code_dir = 'build/' + code_dir_last

    run_args = repository['args']
    run_args.expand('-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release', '-DSKIP_DEFAULTS=ON')
    cmake_build = ['cmake', '--build', '.', '--config', 'release', '--']

    if sys.platform == 'darwin':
        run_args.append('-DOSX_FRAMEWORK=ON')
        run_args.append('-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk')
        run_args.append('-DCMAKE_OSX_DEPLOYMENT_TARGET=' + max_os_min_version)
        cmake_build.append('-j' + str(multiprocessing.cpu_count()))
    elif sys.platform == 'win32':
        run_args.append('-DBUILD_SHARED_LIBS=TRUE')
        cmake_build.append('/m:' + str(multiprocessing.cpu_count()))

    factory_win = util.BuildFactory()
    factory_win.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))

    # Build 32bit ##############################################################
    build_dir = code_dir + "/build32"
    env = {'PYTHONPATH': 'C:\\Python27_32', 'LANG': 'en_US'}
    # make build dir
    factory_win.addStep(steps.MakeDirectory(dir=build_dir))

    # configure view cmake
    factory_win.addStep(steps.ShellCommand(command=["cmake", run_args, '-G', 'Visual Studio 15 2017', '../'],
                                           name="configure",
                                           description=["cmake", "configure for win32"],
                                           descriptionDone=["cmake", "configured for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make
    factory_win.addStep(steps.ShellCommand(command=cmake_build,
                                           name="make",
                                           description=["cmake", "make for win32"],
                                           descriptionDone=["cmake", "made for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make tests
    factory_win.addStep(steps.ShellCommand(command=['ctest', '.'],
                                           name="make",
                                           description=["test", "for win32"],
                                           descriptionDone=["tested", "for win32"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))
    # TODO: Install and make archive

    # Build 64bit ##############################################################
    build_dir = code_dir + "/build64"
    env = {'PYTHONPATH': 'C:\\Python27', 'LANG': 'en_US'}
    # make build dir
    factory_win.addStep(steps.MakeDirectory(dir=build_dir))

    # configure view cmake
    factory_win.addStep(steps.ShellCommand(command=["cmake", run_args, '-G', 'Visual Studio 15 2017 Win64', '../'],
                                           name="configure step",
                                           description=["cmake", "configure for win64"],
                                           descriptionDone=["cmake", "configured for win64"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

    # make
    factory_win.addStep(steps.ShellCommand(command=cmake_build,
                                       name="make",
                                       description=["cmake", "make for win64"],
                                       descriptionDone=["cmake", "made for win64"], haltOnFailure=True,
                                       workdir=build_dir,
                                       env=env))

    # make tests
    factory_win.addStep(steps.ShellCommand(command=['ctest', '.'],
                                           name="make",
                                           description=["test", "for win64"],
                                           descriptionDone=["tested", "for win64"],
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))
    # TODO: Install and make archive

    # Upload archives

    builder_win = BuilderConfig(name = project_name + '_win', workernames = ['build-win'], factory = factory_win)

    c['builders'].append(builder_win)

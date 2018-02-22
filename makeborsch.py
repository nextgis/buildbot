# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import multiprocessing
import bbconf

c = {}

repositories = [
    {'repo':'lib_z', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_sqlite', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_gif', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_geos', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_qhull', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_expat', 'args':[], 'requirements':[], 'skip':[]},
    {'repo':'lib_jsonc', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_opencad', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_jpeg', 'args':['-DBUILD_TESTING=ON', '-DBUILD_JPEG_12=ON', '-DBUILD_JPEG_8=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_proj', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_iconv', 'args':['-DBUILD_TESTING=ON'], 'requirements':[], 'skip':['mac']},
    {'repo':'lib_png', 'args':['-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_freetype', 'args':['-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DWITH_PNG=ON', '-DWITH_PNG_EXTERNAL=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_agg', 'args':['-DWITH_Freetype=ON', '-DWITH_Freetype_EXTERNAL=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_openssl', 'args':['-DOPENSSL_NO_DYNAMIC_ENGINE=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_curl', 'args':['-DENABLE_INET_PTON=OFF', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DHTTP_ONLY=ON', '-DCMAKE_USE_OPENSSL=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DBUILD_TESTING=ON'], 'requirements':[], 'skip':[]},
    {'repo':'lib_pq', 'args':['-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON'], 'requirements':[], 'skip':[]},
    # {'repo':'lib_qt5', 'args':['-DCREATE_CPACK=ON','-DQT_CONFIGURE_ARGS=-accessibility;...'], 'requirements':[]},
]

vm_cpu_count = 8

mac_os_min_version = '10.11'
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

platforms = [
    {'name' : 'win32', 'worker' : 'build-win'},
    {'name' : 'win64', 'worker' : 'build-win'},
    {'name' : 'mac', 'worker' : 'build-mac'} ]

logfile = 'stdio'

def install_dependencies(factory, requirements, os):
    for requirement in requirements:
        if requirement == 'perl' and 'win' in os: # This is example. Perl already installed in VM.
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

# Create builders
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

    builderNames = []
    for platform in platforms:
        if platform in repository['skip']:
            continue
        builderNames.append(project_name + "_" + platform['name'])

    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name,
                                change_filter=util.ChangeFilter(project = git_project_name, branch="master"),
                                treeStableTimer=1*60,
                                builderNames=builderNames,)
    c['schedulers'].append(scheduler)

    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                label="Force build",
                                buttonName="Force build",
                                builderNames=builderNames,)
    c['schedulers'].append(forceScheduler)

    run_args = repository['args']
    run_args.extend(['-DSUPPRESS_VERBOSE_OUTPUT=ON', '-DCMAKE_BUILD_TYPE=Release', '-DSKIP_DEFAULTS=ON'])
    cmake_build = ['cmake', '--build', '.', '--config', 'release', '--']

    for platform in platforms:
        if platform in repository['skip']:
            continue

        code_dir_last = '{}_{}_code'.format(project_name, platform['name'])
        code_dir = os.path.join('build', code_dir_last)
        build_subdir = 'build'
        build_dir = os.path.join(code_dir, build_subdir)

        run_args_ex = list(run_args)
        cmake_build_ex = list(cmake_build)
        env = {}

        if 'win' in platform['name']:
            run_args_ex.append('-DBUILD_SHARED_LIBS=TRUE')
            cmake_build_ex.append('/m:' + str(vm_cpu_count))
            env = {
                'LANG': 'en_US',
                'PATH': [
                            "C:\\buildbot\worker\\" + project_name + "_" + platform['name'] + "\\build\\" + code_dir_last + "\\" + build_subdir + "\\release",
                            "${PATH}"
                        ],
            }
            if 'win32' == platform['name']:
                env['PYTHONPATH'] = 'C:\\Python27_32'
                run_args_ex.extend(['-G', 'Visual Studio 15 2017'])
            else:
                env['PYTHONPATH'] = 'C:\\Python27'
                run_args_ex.extend(['-G', 'Visual Studio 15 2017 Win64'])
        elif 'mac' == platform['name']:
            run_args_ex.extend(['-DOSX_FRAMEWORK=ON', '-DCMAKE_OSX_SYSROOT=' + mac_os_sdks_path + '/MacOSX.sdk', '-DCMAKE_OSX_DEPLOYMENT_TARGET=' + mac_os_min_version])
            cmake_build_ex.append('-j' + str(vm_cpu_count))
            env = {
                'PATH': [
                            "/usr/local/bin",
                            "${PATH}"
                        ],
                'MACOSX_DEPLOYMENT_TARGET': mac_os_min_version,
            }

        factory = util.BuildFactory()

        install_dependencies(factory, repository['requirements'], platform['name'])

        factory.addStep(steps.Git(repourl=repourl, mode='full', shallow=True,
                                method='clobber', submodules=False, workdir=code_dir))

        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=["curl", release_script_src, '-o', script_name, '-s', '-L'], logfile=logfile),
                util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s'], logfile=logfile),
            ],
            name="Download scripts",
            haltOnFailure=True,
            workdir=code_dir,
            env=env))

        factory.addStep(steps.MakeDirectory(dir=build_dir, name="Make build directory"))

        # configure view cmake
        factory.addStep(steps.ShellCommand(command=["cmake", run_args_ex, '..'],
                                           name="configure",
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

        # make
        factory.addStep(steps.ShellCommand(command=cmake_build_ex,
                                           name="make",
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

        # make tests
        factory.addStep(steps.ShellCommand(command=['ctest', '-C', 'release'],
                                           name="test",
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

        # make package
        factory.addStep(steps.ShellCommand(command=['cpack', '.'],
                                           name="pack",
                                           haltOnFailure=True,
                                           workdir=build_dir,
                                           env=env))

        # send package to github
        factory.addStep(steps.ShellCommand(command=['python', script_name, '--login',
                                                    username, '--key', userkey, '--build_path', build_subdir
                                                    ],
                                           name="send package to github",
                                           haltOnFailure=True,
                                           workdir=code_dir))

        # upload to ftp
        factory.addStep(steps.ShellCommand(command=['python', upload_script_name,
                                                    '--ftp_user', ngftp_user, '--ftp',
                                                    ngftp + project_name + '_' + platform['name'],
                                                    '--build_path', build_subdir],
                                           name="send package to ftp",
                                           haltOnFailure=True,
                                           workdir=code_dir))

        # create installer trigger
        factory.addStep(steps.Trigger(schedulerNames=[ci_project_name + '_' + platform['name']],
                                      waitForFinish=False,
                                      set_properties={ 'suffix' : '-dev' }))

        builder = util.BuilderConfig(name = project_name + '_' + platform['name'],
                                    workernames = [platform['worker']],
                                    factory = factory,
                                    description="Make {} on {}".format(project_name, platform['name']),)

        c['builders'].append(builder)

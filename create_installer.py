# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import time

c = {}

vm_cpu_count = 8

mac_os_min_version = '10.14'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

ngftp2 = 'ftp://192.168.6.7:8121/software/installer'
ngftp = 'ftp://192.168.6.1:10411/software/installer'
ngftp_user = os.environ.get("BUILDBOT_MYFTP_USER")
ngftp2_user = os.environ.get("BUILDBOT_FTP_USER")
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/ftp_uploader.py'
upload_script_name = 'ftp_upload.py'
repka_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/repka_release.py'
repka_script_name = 'repka_release.py'
if_project_name = 'inst_framework'
login_keychain = os.environ.get("BUILDBOT_MACOSX_LOGIN_KEYCHAIN")
username = 'buildbot' # username = 'bishopgis'
userkey = os.environ.get("BUILDBOT_PASSWORD") # userkey = os.environ.get("BUILDBOT_APITOKEN_GITHUB")

installer_git = 'git://github.com/nextgis/nextgis_installer.git'

timeout = 180
max_time = 240

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

project_name = 'create_installer'
generator = 'Visual Studio 16 2019'
create_updater_package = False
binary_repo_refix = "https://rm.nextgis.com/api/repo" 
#"http://nextgis.com/programs/desktop/repository-" // 
# https://rm.nextgis.com/api/repo/4/installer/devel/repository-win32-dev/Updates.xml https://rm.nextgis.com/api/repo/4/installer/stable/repository-win32/Updates.xml


build_lock = util.WorkerLock("create_installer_worker_builds",
    maxCount=1,
    maxCountForWorker={'build-win': 1, 'build-mac': 1}
)

forceScheduler_create = schedulers.ForceScheduler(
    name=project_name + "_update",
    label="Update installer",
    buttonName="Update installer",
    builderNames=[
        project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ],
    properties=[
        util.StringParameter(
            name="force",
            label="Force update specified packages even not any changes exists:",
            default="all", 
            size=280),
        util.StringParameter(
            name="url",
            label="Installer URL (without ending slash):",
            default=binary_repo_refix, 
            size=40),
        util.StringParameter(
            name="suffix",
            label="Installer name and URL path suffix (use '-dev' for default):",
            default="", 
            size=40),
        util.TextParameter(
            name="notes",
            label="Release notes to be displayed in update available dialog",
            default="", 
            cols=80, 
            rows=5),
    ],
)

forceScheduler_update = schedulers.ForceScheduler(
    name=project_name + "_create",
    label="Create installer", 
    buttonName="Create installer",
    builderNames=[
        project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ],
    properties=[
        util.StringParameter(
            name="url", 
            label="Installer URL (without ending slash):",
            default=binary_repo_refix, 
            size=40),
        util.StringParameter(
            name="suffix",
            label="Installer name and URL path suffix (use '-dev' for default):",
            default="", 
            size=40),
        util.TextParameter(
            name="notes",
            label="Release notes to be displayed in update available dialog",
            default="", 
            cols=80, 
            rows=5),
    ],
)

forceScheduler_standalone = schedulers.ForceScheduler(
    name=project_name + "_standalone",
    label="Create standalone installer",
    buttonName="Create standalone installer",
    builderNames=[
        project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ],
    properties=[
        util.StringParameter(
            name="suffix",
            label="Installer name and URL path suffix (use '-dev' for default):",
            default="", 
            size=40),
    ],
)

forceScheduler_standalone_ex = schedulers.ForceScheduler(
    name=project_name + "_brand_standalone",
    label="Create branded standalone installer",
    buttonName="Create branded installer",
    builderNames=[
        project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ],
    properties=[
        util.StringParameter(
            name="suffix",
            label="Installer name and URL path suffix (use '-dev' for default):",
            default="", 
            size=40),
        util.StringParameter(
            name="plugins",
            label="Plugins names separated by comma to include to installer:",
            default="", 
            size=80),
        util.StringParameter(
            name="valid_user",
            label="User name for supported dialog:",
            default="", 
            size=80),
        util.StringParameter(
            name="valid_date",
            label="Validity period for supported functions (YYYY-MM-DD):",
            default="2024-01-01", 
            size=40),
    ],
)

forceScheduler_local = schedulers.ForceScheduler(
    name=project_name + "_local",
    label="Create intranet installer",
    buttonName="Create intranet installer",
    builderNames=[
        project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ],
    properties=[
        util.StringParameter(
            name="url", 
            label="Installer URL (without ending slash):",
            default=binary_repo_refix, 
            size=40),
        util.StringParameter(
            name="suffix",
            label="Installer name and URL path suffix (use '-dev' for default):",
            default="-local", 
            size=40),
    ],
)

c['schedulers'].append(forceScheduler_create)
c['schedulers'].append(forceScheduler_update)
c['schedulers'].append(forceScheduler_standalone)
c['schedulers'].append(forceScheduler_standalone_ex)
c['schedulers'].append(forceScheduler_local)

@util.renderer
def now(props):
    return time.strftime('%Y%m%d')

@util.renderer
def commandArgs(props):
    command = []
    if props.getProperty('scheduler') == project_name + "_create":
        command.append('create')
    elif props.getProperty('scheduler').endswith("_standalone"):
        command.append('create')    
    elif props.getProperty('scheduler').endswith("_local"):
        command.append('create')
    elif props.getProperty('scheduler') == project_name + "_update":
        command.extend(['update', '--force', props.getProperty('force'),])
    else:
        command.append('update')

    return command

@util.renderer
def repoUrl(props, platform):
    url = props.getProperty('url')
    if url is None:
        return ""
    suffix = props.getProperty('suffix')
    if url.startswith('https://rm.nextgis.com'):
        repo_id = platform['repo_id'] 
        repka_suffix = 'devel' if suffix == '-dev' else 'stable'
        return '{}/{}/installer/{}/repository-{}{}'.format(url, repo_id, repka_suffix, platform['name'], suffix)
    elif suffix == '-local':
        return '{}/{}'.format(url, platform['name'])
    else:
        return '{}/{}{}'.format(url, platform['name'], suffix)

platforms = [
    {'name' : 'win32', 'worker' : 'build-win', 'repo_id': 4},
    {'name' : 'win64', 'worker' : 'build-win', 'repo_id': 5},
    {'name' : 'mac', 'worker' : 'build-mac', 'repo_id': 6} 
]

# Create triggerable shcedulers
for platform in platforms:
    triggerScheduler = schedulers.Triggerable(
        name=project_name + "_" + platform['name'],
        builderNames=[ project_name + "_" + platform['name'], ])
    c['schedulers'].append(triggerScheduler)

# Create builders
for platform in platforms:
    code_dir_last = '{}_{}_code'.format('installer', platform['name'])
    code_dir = os.path.join('build', code_dir_last)
    build_dir_name = 'build'
    build_dir = os.path.join(code_dir, build_dir_name)

    factory = util.BuildFactory()

    # Radically clean all
    factory.addStep(steps.RemoveDirectory(dir=code_dir, name="Clean all"))

    factory.addStep(steps.Git(repourl=installer_git,
                               mode='full',
                               shallow=True,
                               method='clobber',
                               submodules=False,
                               alwaysUseLatest=True,
                               workdir=code_dir))

    factory.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make build directory"))

    # 1. Get and unpack installer and qt5 static from ftp
    if_prefix = '_mac'
    separator = '/'
    env = {
        'PATH': [
                    "/usr/local/bin",
                    "${PATH}"
                ],
    }
    installer_ext = '.dmg'
    if 'win' in platform['name']:
        if_prefix = '_win'
        separator = '\\'
        env = {'PYTHONHTTPSVERIFY': '0'}
        installer_ext = '.exe'
        # if 'win32' == platform['name']:
        #     env = { 
        #         'PYTHONPATH': 'C:\\Python27_32',
        #         'PYTHONHTTPSVERIFY': '0'
        #     }

    repo_name_base = 'repository-' + platform['name']
    logname = 'stdio'

    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp2_user, ngftp2 + '/src/' + if_project_name + if_prefix + '/package.zip', '-o', 'package.zip', '-s'], logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'], logname=logname),
        ],
        name="Download installer package",
        haltOnFailure=True,
        workdir=build_dir,
        env=env))
    factory.addStep(steps.CopyDirectory(src=build_dir + "/qtifw_build", dest=code_dir + "/qtifw_pkg"))
    factory.addStep(steps.RemoveDirectory(dir=build_dir + "/qtifw_build"))

    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp2_user, ngftp2 + '/src/' + if_project_name + if_prefix + '/qt/package.zip', '-o', 'package.zip', '-s'], logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'], logname=logname),
        ],
        name="Download qt package",
        haltOnFailure=True,
        workdir=build_dir,
        env=env))
    factory.addStep(steps.CopyDirectory(src=build_dir + "/inst", dest=code_dir + "/qt"))
    factory.addStep(steps.RemoveDirectory(dir=build_dir + "/inst"))

    # 2. Get repository from ftp
    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp2_user,
                                    '-o', util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip',
                                        basename=repo_name_base),
                                    '-s', util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip',
                                        basename=ngftp2 + '/src/' + 'repo_' + platform['name'] + '/' + repo_name_base),
                                    ],
                            logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf',
                                    util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip',
                                        basename=repo_name_base)],
                            logname=logname),
        ],
        name="Download repository",
        haltOnFailure=True,
        doStepIf=(lambda step: not (step.getProperty("scheduler") == project_name + "_create" or step.getProperty("scheduler") == project_name + "_local")),
        workdir=build_dir,
        env=env))

    factory.addStep(steps.ShellSequence(
        commands=[
            util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s'], logname=logname),
        ],
        name="Download scripts",
        haltOnFailure=True,
        doStepIf=(lambda step: step.getProperty("scheduler") == project_name + "_create"),
        workdir=code_dir,
        env=env))

    factory.addStep(steps.ShellSequence(
        commands=[
            util.ShellArg(command=["curl", repka_script_src, '-o', repka_script_name, '-s'], logname=logname),
        ],
        name="Download scripts",
        haltOnFailure=True,
        doStepIf=(lambda step: not step.getProperty("scheduler").endswith("_standalone")),
        workdir=code_dir,
        env=env))

    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp2_user, '-o', 'versions.pkl', '-s',
                                                util.Interpolate('%(kw:basename)s%(prop:suffix)s.pkl',
                                                    basename=ngftp2 + '/src/' + 'repo_' + platform['name'] + '/versions'),
                                                ],
                                        name="Download versions.pkl",
                                        # haltOnFailure=False, warnOnWarnings=True,
                                        # flunkOnFailure=False, warnOnFailure=True,
                                        # haltOnFailure=True, # The repository may not be exists
                                        doStepIf=(lambda step: not step.getProperty("scheduler") == project_name + "_local"),
                                        workdir=code_dir,
                                        env=env))

    # if 'win' in platform['name']:
    #     factory.addStep(steps.ShellSequence(commands=[
    #                                         util.ShellArg(command=['pip', 'install', '--user', 'pytz'], logname=logname),
    #                                     ],
    #                                     name="Install pytz python package",
    #                                     haltOnFailure=True,
    #                                     workdir=code_dir,
    #                                     env=env))

    create_opt = []
    if 'win64' == platform['name']:
        create_opt.append('-G')
        create_opt.append(generator)
        create_opt.append('-A')
        create_opt.append('x64')
        # create_opt.append('-w64')
    elif 'win32' == platform['name']:
        create_opt.append('-g')
        create_opt.append(generator)
        create_opt.append('-A')
        create_opt.append('Win32')

    installer_name_base = 'nextgis-setup-' + platform['name']

    # 3. Get compiled libraries
    factory.addStep(
        steps.ShellCommand(
            command=[
                "python3", 'opt' + separator + 'create_installer.py',
                '-s', 'inst', '-q', 'qt/bin', '-t', build_dir_name,
                '-n', '-r', repoUrl.withArgs(platform),
                '-i', util.Interpolate('%(kw:basename)s%(prop:suffix)s',  basename=installer_name_base),
                create_opt, 'prepare', '--ftp_user', ngftp2_user,
                '--ftp', ngftp2 + '/src/', 
                '-p', util.Interpolate('%(prop:plugins)s'),
                '-vd', util.Interpolate('%(prop:valid_date)s'),
                '-vu', util.Interpolate('%(prop:valid_user)s'),
                '--sign_pwd','{}:{}'.format(username, userkey),
            ],
            name="Prepare packages data",
            maxTime=max_time * 60,
            timeout=timeout * 60,
            haltOnFailure=True,
            workdir=code_dir,
            env=env
        )
    )

    # 4. Create or update repository
    # Install NextGIS sign sertificate
    if 'mac' == platform['name']:
        # Try to pip2 and pip install

        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=['pip2', 'install', '--user', 'dmgbuild'],
                                haltOnFailure=False, flunkOnWarnings=False, # Don't fail here
                                flunkOnFailure=False, warnOnWarnings=False,
                                warnOnFailure=False,
                                logname=logname),
                util.ShellArg(command=['pip', 'install', '--user', 'dmgbuild'],
                                logname=logname),
            ],
            name="Install dmgbuild python package",
            haltOnFailure=True,
            workdir=code_dir,
            env=env))

        # factory.addStep(steps.FileDownload(mastersrc="/opt/buildbot/dev.p12",
        #                                     workerdest=code_dir_last + "/dev.p12",
        #                                     ))
        keychain_name = 'cs.keychain'
        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=["curl", '-u', ngftp2_user, ngftp2 + '/dev.p12', '-o', 'dev.p12', '-s'], logname=logname),
                # For use in separate keychain
                util.ShellArg(command=['security', 'create-keychain', '-p', login_keychain, keychain_name],
                              logname=logname,
                              haltOnFailure=False, flunkOnWarnings=False, flunkOnFailure=False,
                              warnOnWarnings=False, warnOnFailure=False),
                util.ShellArg(command=['security', 'default-keychain', '-s', keychain_name], logname=logname),
                util.ShellArg(command=['security', 'unlock-keychain', '-p', login_keychain, keychain_name], logname=logname),
                util.ShellArg(command=['security', 'import', './dev.p12', '-k', keychain_name, '-P', '', '-A'], logname=logname),
                util.ShellArg(command=['security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-k', login_keychain, '-s',  keychain_name,], logname=logname),
                util.ShellArg(command=['security', 'list-keychains', '-s', keychain_name], logname=logname),
                util.ShellArg(command=['security', 'list-keychains'], logname=logname),
            ],
            name="Install NextGIS sign sertificate",
            haltOnFailure=True,
            workdir=code_dir,
            env=env))

    factory.addStep(
        steps.ShellCommand(
            command=[
                "python3", 'opt' + separator + 'create_installer.py', '-s', 'inst',
                '-q', 'qt/bin', '-t', build_dir_name, '-n', 
                '-r', repoUrl.withArgs(platform), '-i', 
                util.Interpolate('%(kw:basename)s%(prop:suffix)s', basename=installer_name_base),
                create_opt, commandArgs,
            ],
            name="Create/Update repository",
            doStepIf=(lambda step: not step.getProperty("scheduler").endswith("_standalone")),
            haltOnFailure=True,
            maxTime=max_time * 60,
            timeout=timeout * 60,
            workdir=code_dir,
            env=env
        )
    )

    factory.addStep(steps.ShellCommand(command=["python3", 'opt' + separator + 'create_installer.py',
                                                '-s', 'inst',
                                                '-q', 'qt/bin',
                                                '-t', build_dir_name,
                                                '-i', util.Interpolate('%(kw:basename)s%(prop:suffix)s-%(kw:now)s', basename=installer_name_base + '-standalone', now=now),
                                                create_opt, commandArgs,
                                                ],
                                        name="Create/Update repository",
                                        doStepIf=(lambda step: step.getProperty("scheduler").endswith("_standalone")),
                                        maxTime=max_time * 60,
                                        timeout=timeout * 60,
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    # 5. Upload installer to ftp
    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp_user, '-T',
                                                util.Interpolate('%(kw:basename)s%(prop:suffix)s' + installer_ext,
                                                    basename=installer_name_base),
                                                '-s', '--ftp-create-dirs', ngftp + '/'],
                                       name="Upload installer to ftp",
                                       haltOnFailure=True,
                                       doStepIf=(lambda step: (step.getProperty("scheduler") == project_name + "_create" or step.getProperty("scheduler") == project_name + "_local")),
                                       workdir=build_dir,
                                       env=env))

    factory.addStep(
        steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp_user, '-T',
                util.Interpolate('%(kw:basename)s%(prop:suffix)s-%(kw:now)s' + installer_ext, basename=installer_name_base + '-standalone', now=now),
                                '-s', '--ftp-create-dirs', ngftp + '/'
            ],
            logname=logname),
            util.ShellArg(command=["echo",
                util.Interpolate('Download standalone installer from this url: https://my.nextgis.com/downloads/software/installer/%(kw:basename)s%(prop:suffix)s-%(kw:now)s' + installer_ext,
                    basename=installer_name_base + '-standalone', now=now)
            ],
            logname=logname),
        ],
        name="Upload standalone installer to ftp",
        haltOnFailure=True,
        doStepIf=(lambda step: step.getProperty("scheduler").endswith("_standalone")),
        workdir=build_dir,
        env=env)
    )

    # 6. Create zip from repository
    factory.addStep(
        steps.ShellCommand(
            command=[
                "cmake", '-E', 'tar', 'cfv',
                util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip', basename=repo_name_base), 
                '--format=zip',
                util.Interpolate('%(kw:basename)s%(prop:suffix)s', basename=repo_name_base)
            ],
            name="Create zip from repository",
            haltOnFailure=True,
            doStepIf=(lambda step: not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler") == project_name + "_local")),
            workdir=build_dir,
            env=env
        )
    )

    # 7. Upload repository archive to ftp
    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp2_user, '-T',
                                        util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip',
                                            basename=repo_name_base),
                                        '-s', '--ftp-create-dirs',
                                        ngftp2 + '/src/' + 'repo_' + platform['name'] + '/',],
                                       name="Upload repository archive to ftp",
                                       haltOnFailure=True,
                                       doStepIf=(lambda step: not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler") == project_name + "_local")),
                                       workdir=build_dir,
                                       env=env))
                                       
    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp2_user, '-T',
                                                'versions.pkl', '-s', '--ftp-create-dirs',
                                                util.Interpolate('%(kw:basename)s%(prop:suffix)s.pkl',
                                                    basename=ngftp2 + '/src/' + 'repo_' + platform['name'] + '/versions'),
                                                ],
                                       name="Upload versions.pkl to ftp",
                                       doStepIf=(lambda step: not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler") == project_name + "_local")),
                                       workdir=code_dir,
                                       env=env))
    if create_updater_package:
        # If create installer - upload updater.zip + version.str to ftp
        factory.addStep(steps.ShellCommand(command=['python3', upload_script_name,
                                                    '--ftp_user', ngftp2_user, '--ftp',
                                                    ngftp2 + '/src/nextgis_updater_' + platform['name'],
                                                    '--build_path', build_dir_name],
                                           name="send package to ftp",
                                           doStepIf=(lambda step: step.getProperty("scheduler") == project_name + "_create"),
                                           haltOnFailure=True,
                                           workdir=code_dir,
                                           env=env))

    # 8. Create new release in repka
    factory.addStep(steps.ShellCommand(
        command=["python3", repka_script_name, '--repo_id', platform['repo_id'],
            '--description', util.Interpolate('%(prop:notes)s'),
            '--asset_path', util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip', basename=build_dir_name + separator + repo_name_base),
            '--login', username, '--password', userkey],
        name="Create release in repka",
        doStepIf=(lambda step: not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler") == project_name + "_local")),
        haltOnFailure=True,
        workdir=code_dir,
        env=env))

    builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
                                 workernames = [platform['worker']],
                                 factory = factory,
                                 locks = [build_lock.access('counting')],
                                 description="Create/update installer on " + platform['name'],)

    c['builders'].append(builder)

# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import os
import time
import json

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

c = {}

vm_cpu_count = 8

mac_os_min_version = '10.14'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

ngftp = 'ftp://my-ftp-storage.vpn.nextgis.net:10411/software/installer'
ngftp_user = os.environ.get("BUILDBOT_MYFTP_USER")
# upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/ftp_uploader.py'
# upload_script_name = 'ftp_upload.py'
repka_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/repka_release.py'
repka_script_name = 'repka_release.py'
if_project_name = 'inst_framework'
login_keychain = os.environ.get("BUILDBOT_MACOSX_LOGIN_KEYCHAIN")
username = 'buildbot' # username = 'bishopgis'
userkey = os.environ.get("BUILDBOT_PASSWORD") # userkey = os.environ.get("BUILDBOT_APITOKEN_GITHUB")
https_proxy = os.environ.get("BUILDBOT_HTTPS_PROXY")
installer_git = 'https://github.com/nextgis/nextgis_installer.git'

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
# https://rm.nextgis.com/api/repo/4/installer/devel/repository-win32-dev/Updates.xml 
# https://rm.nextgis.com/api/repo/4/installer/stable/repository-win32/Updates.xml

repka_endpoint = 'https://rm.nextgis.com'

build_lock = util.WorkerLock("create_installer_worker_builds",
    maxCount=1,
    maxCountForWorker={'build-win-py3': 1, 'build-mac-py3': 1}
)

builder_names=[
        # project_name + "_win32",
        project_name + "_win64",
        project_name + "_mac",
    ]

forceScheduler_create = schedulers.ForceScheduler(
    name=project_name + "_update",
    label="Update installer",
    buttonName="Update installer",
    builderNames=builder_names,
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
    builderNames=builder_names,
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
    builderNames=builder_names,
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
    builderNames=builder_names,
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
    builderNames=builder_names,
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

def get_repka_suffix(suffix):
    return 'devel' if suffix == '-dev' else 'stable_new'

@util.renderer
def get_packet_name(props):
    suffix = props.getProperty('suffix')
    return get_repka_suffix(suffix)

@util.renderer
def now(props):
    return time.strftime('%Y%m%d')

@util.renderer
def commandArgs(props):
    command = []
    if props.getProperty('scheduler') == project_name + "_create":
        command.append('create')
    elif props.getProperty('scheduler').endswith("_standalone"):
        #command.append('create')
        command.append('create_from_repository')
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
    suffix_tmp = props.getProperty('suffix')
    if url.startswith('https://rm.nextgis.com'):
        repo_id = platform['repo_id'] 
        repka_suffix = get_repka_suffix(suffix_tmp)
        return '{}/{}/installer/{}/repository-{}{}'.format(url, repo_id, repka_suffix, platform['name'], suffix_tmp)
    elif suffix_tmp == '-local':
        return '{}/repository-{}'.format(url, platform['name'])
    else:
        return '{}/{}'.format(url, platform['name'] + suffix_tmp)

def get_packet_id(repo_id, packet_name):
    url =  repka_endpoint + '/api/packet?repository={}&filter={}'.format(repo_id, packet_name)
    response = urlopen(url)
    packets = json.loads(response.read())
    for packet in packets:
        if packet['name'] == packet_name:
            return packet['id']
    return -1

def get_release(packet_id, tag):
    url =  repka_endpoint + '/api/release?packet={}'.format(packet_id)
    response = urlopen(url)
    releases = json.loads(response.read())
    if releases is None:
        return None
    
    for release in releases:
        if tag in release['tags']:
            return release
    return None

def get_file_id(release, name):
    for file in release['files']:
        if file['name'].endswith(name):
            return file['id']
    return -1

def get_packet_url(platform, packet_name, filename):
    packet_id = get_packet_id(platform['repo_id'], packet_name)
    if packet_id == -1:
        return ''
    
    release = get_release(packet_id, 'latest')
    if release == None:
        return ''
    
    file_id = get_file_id(release, filename)
    
    return repka_endpoint + '/api/asset/{}/download'.format(file_id)

def skip_step(step, which):
    if which == 'standalone+local':
        return not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler").endswith("_local"))
    if which == 'standalone+update':
        return not (step.getProperty("scheduler").endswith("_standalone") or step.getProperty("scheduler").endswith("_update"))
    if which == 'create+local':
        return not (step.getProperty("scheduler").endswith("_create") or step.getProperty("scheduler").endswith("_local"))

@util.renderer
def get_repository_http_url(props, platform):
    suffix = props.getProperty('suffix')
    repka_suffix = get_repka_suffix(suffix)
    
    suffix_tmp = '-dev' if suffix == '-dev' else '' 
    
    return get_packet_url(platform, repka_suffix, platform['name'] + suffix_tmp + '.zip')

@util.renderer
def get_installer_name(props, basename, suffix = ''):
    suffix_tmp = props.getProperty('suffix')
    # repka_suffix = get_repka_suffix(suffix_tmp)

    return basename + suffix_tmp + suffix

@util.renderer
def get_versions_url(props, platform):
    suffix = props.getProperty('suffix')
    repka_suffix = get_repka_suffix(suffix)
    return get_packet_url(platform, repka_suffix, 'versions.pkl')

@util.renderer
def get_installer_package_url(props, platform):
    return get_packet_url(platform, 'inst_framework', 'package.zip')

@util.renderer
def get_qt_package_url(props, platform):
    return get_packet_url(platform, 'inst_framework_qt', 'package.zip')

@util.renderer
def get_updater_package_path(props, platform):
    version_file = os.path.join(build_dir_name, 'version.str')
    with open(version_file) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    
    release_file = os.path.join(build_dir_name, content[2]) + '.zip'
    package_file = os.path.join(build_dir_name, 'package.zip')
    os.rename(release_file, package_file)
    return package_file

platforms = [
    # {'name' : 'win32', 'worker' : 'build-win', 'repo_id': 4},
    {'name' : 'win64', 'worker' : 'build-win-py3', 'repo_id': 5},
    {'name' : 'mac', 'worker' : 'build-mac-py3', 'repo_id': 6} 
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

    # 1. Get and unpack installer and qt5 static from repka
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
        env['PYTHONPATH'] = 'C:\\Python38'
        env['FLANG_HOME'] = 'C:\\Users\\root\\conda\\Library'
        installer_ext = '.exe'
        # if 'win32' == platform['name']:
        #     env = { 
        #         'PYTHONPATH': 'C:\\Python27_32',
        #         'PYTHONHTTPSVERIFY': '0'
        #     }

    repo_name_base = 'repository-' + platform['name']
    logname = 'stdio'

    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", get_installer_package_url.withArgs(platform), '-o', 'package.zip', '-s'], logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'], logname=logname),
        ],
        name="Download installer package",
        haltOnFailure=True,
        workdir=build_dir,
        env=env))
    factory.addStep(steps.CopyDirectory(src=build_dir + "/qtifw_build", dest=code_dir + "/qtifw_pkg"))
    factory.addStep(steps.RemoveDirectory(dir=build_dir + "/qtifw_build"))

    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", get_qt_package_url.withArgs(platform), '-o', 'package.zip', '-s'], logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'], logname=logname),
        ],
        name="Download qt package",
        haltOnFailure=True,
        workdir=build_dir,
        env=env))
    factory.addStep(steps.CopyDirectory(src=build_dir + "/inst", dest=code_dir + "/qt"))
    factory.addStep(steps.RemoveDirectory(dir=build_dir + "/inst"))

    # 2. Get repository from
    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=["curl",
                                    '-o', get_installer_name.withArgs(repo_name_base, '.zip'), #  util.Interpolate('%(kw:basename)s%prop:suffix)s.zip', basename=repo_name_base),
                                    '-s', get_repository_http_url.withArgs(platform),
                                    ],
                            logname=logname),
            util.ShellArg(command=["cmake", '-E', 'tar', 'xzf',
                                    get_installer_name.withArgs(repo_name_base, '.zip'), # util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip', basename=repo_name_base)],
                                  ],
                            logname=logname),
        ],
        name="Download repository",
        haltOnFailure=True,
        # doStepIf=(lambda step: not step.getProperty("scheduler").endswith("_standalone")),
        workdir=build_dir,
        env=env))

    # factory.addStep(steps.ShellSequence(
    #     commands=[
    #         util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s'], logname=logname),
    #     ],
    #     name="Download upload script",
    #     haltOnFailure=True,
    #     doStepIf=(lambda step: step.getProperty("scheduler").endswith("_create")),
    #     workdir=code_dir,
    #     env=env))

    factory.addStep(steps.ShellSequence(
        commands=[
            util.ShellArg(command=["curl", repka_script_src, '-o', repka_script_name, '-s'], logname=logname),
        ],
        name="Download repka script",
        haltOnFailure=True,
        doStepIf=(lambda step: skip_step(step, 'standalone+local')),
        workdir=code_dir,
        env=env))

    factory.addStep(steps.ShellCommand(command=["curl",
                                                '-o', 'versions.pkl',
                                                '-s', get_versions_url.withArgs(platform),
                                                ],
                                        name="Download versions.pkl",
                                        haltOnFailure=True,
                                        # doStepIf=(lambda step: not step.getProperty("scheduler").endswith("_standalone")),
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
        create_opt.append('-g')
        create_opt.append(generator)
        create_opt.append('-w64')
        if https_proxy is not None:
            env['https_proxy'] = https_proxy
    # elif 'win32' == platform['name']:
    #     create_opt.append('-g')
    #     create_opt.append(generator)
    #     create_opt.append('-A')
    #     create_opt.append('Win32')

    installer_name_base = 'nextgis-setup-' + platform['name']


    # 3. Get compiled libraries
    factory.addStep(
        steps.ShellCommand(
            command=[
                "python3", 'opt' + separator + 'create_installer.py',
                '-s', 'inst', '-q', 'qt/bin', '-t', build_dir_name,
                '-n', '-r', repoUrl.withArgs(platform),
                '-i', get_installer_name.withArgs(installer_name_base), # util.Interpolate('%(kw:basename)s%(prop:suffix)s',  basename=installer_name_base),
                create_opt, 'prepare',
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
            env=env,
            doStepIf=(lambda step: not step.getProperty("scheduler").endswith("_standalone"))
        )
    )

    # 4. Create or update repository
    # Install NextGIS sign sertificate
    if 'mac' == platform['name']:
        # Try to pip2 and pip install

        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=['pip3', 'install', '--user', 'dmgbuild'],
                                # haltOnFailure=False, flunkOnWarnings=False, # Don't fail here
                                # flunkOnFailure=False, warnOnWarnings=False,
                                # warnOnFailure=False,
                                logname=logname),
                # util.ShellArg(command=['pip', 'install', '--user', 'dmgbuild'],
                #                 logname=logname),
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
                util.ShellArg(command=["curl", '-u', 'https://rm.nextgis.com/api/apple_cert/dev.p12', '-o', 'dev.p12', '-s'], logname=logname),
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
                get_installer_name.withArgs(installer_name_base), # util.Interpolate('%(kw:basename)s%(prop:suffix)s', basename=installer_name_base),
                create_opt, commandArgs,
            ],
            name="Create/Update repository network",
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
                                                '-i', get_installer_name.withArgs(installer_name_base + '-standalone', util.Interpolate('-%(kw:now)s', now=now)), # util.Interpolate('%(kw:basename)s%(prop:suffix)s-%(kw:now)s', basename=installer_name_base + '-standalone', now=now),
                                                create_opt, commandArgs,
                                                ],
                                        name="Create/Update repository standalone",
                                        doStepIf=(lambda step: step.getProperty("scheduler").endswith("_standalone")),
                                        maxTime=max_time * 60,
                                        timeout=timeout * 60,
                                        haltOnFailure=True,
                                        workdir=code_dir,
                                        env=env))

    # remove https_proxy
    del env["https_proxy"]

    # 5. Upload installer to ftp
    # TODO: upload to repka
    factory.addStep(
        steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp_user, '-T',
                get_installer_name.withArgs(installer_name_base, installer_ext), #util.Interpolate('%(kw:basename)s%(prop:suffix)s' + installer_ext, basename=installer_name_base),
                            '-s', '--ftp-create-dirs', ngftp + '/'],
            logname=logname),
            util.ShellArg(command=["echo",
                get_installer_name.withArgs('Download installer from this url: https://my.nextgis.com/downloads/software/installer/{}'.format(installer_name_base),  installer_ext)],
            logname=logname),
        ],
        name="Upload installer to ftp",
        haltOnFailure=True,
        doStepIf=(lambda step: not skip_step(step, 'create+local')),
        workdir=build_dir,
        env=env)
    )

    factory.addStep(
        steps.ShellSequence(commands=[
            util.ShellArg(command=["curl", '-u', ngftp_user, '-T',
                get_installer_name.withArgs(installer_name_base + '-standalone', util.Interpolate('-%(kw:now)s%(kw:ext)s', now=now, ext=installer_ext)),
                # util.Interpolate('%(kw:basename)s%(prop:suffix)s-%(kw:now)s' + installer_ext, basename=installer_name_base + '-standalone', now=now),
                                '-s', '--ftp-create-dirs', ngftp + '/'
            ],
            logname=logname),
            util.ShellArg(command=["echo",
                get_installer_name.withArgs('Download standalone installer from this url: https://my.nextgis.com/downloads/software/installer/{}-standalone'.format(installer_name_base), util.Interpolate('-%(kw:now)s%(kw:ext)s', now=now, ext=installer_ext)),
                #util.Interpolate('Download standalone installer from this url: https://my.nextgis.com/downloads/software/installer/%(kw:basename)s%(prop:suffix)s-%(kw:now)s' + installer_ext,  basename=installer_name_base + '-standalone', now=now)
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
                get_installer_name.withArgs(repo_name_base, '.zip'),
                # util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip', basename=repo_name_base), 
                '--format=zip',
                get_installer_name.withArgs(repo_name_base),
                # util.Interpolate('%(kw:basename)s%(prop:suffix)s', basename=repo_name_base)
            ],
            name="Create zip from repository",
            haltOnFailure=True,
            doStepIf=(lambda step: skip_step(step, 'standalone+local')),
            workdir=build_dir,
            env=env
        )
    )

    if create_updater_package:
        # Create zip
        factory.addStep(
            steps.ShellCommand(
                command=[
                    "cmake", '-E', 'tar', 'cfv', 'package.zip', '--format=zip',
                    'packages/com.nextgis.nextgis_updater',
                ],
                name="Create updater package",
                haltOnFailure=True,
                doStepIf=(lambda step: step.getProperty("scheduler").endswith("_create")),
                workdir=build_dir,
                env=env
            )
        )
        
        factory.addStep(steps.ShellCommand(
            command=["python3", repka_script_name, '--repo_id', platform['repo_id'],
                '--asset_path', build_dir + '/package.zip',
                '--packet_name', 'updater',
                '--login', username, '--password', userkey],
            name="Send updater package to repka",
            doStepIf=(lambda step: step.getProperty("scheduler").endswith("_create")),
            haltOnFailure=True,
            workdir=code_dir,
            env=env))

    # 8. Create new release in repka
    factory.addStep(steps.ShellCommand(
        command=["python3", repka_script_name, '--repo_id', platform['repo_id'],
            '--description', util.Interpolate('%(prop:notes)s'),
            '--asset_path', get_installer_name.withArgs(build_dir_name + separator + repo_name_base, '.zip'), # util.Interpolate('%(kw:basename)s%(prop:suffix)s.zip', basename=build_dir_name + separator + repo_name_base),
            '--asset_path', 'versions.pkl',
            '--packet_name', get_packet_name,
            '--login', username, '--password', userkey],
        name="Create release in repka",
        doStepIf=(lambda step: skip_step(step, 'standalone+local')),
        haltOnFailure=True,
        workdir=code_dir,
        env=env))

    builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
                                 workernames = [platform['worker']],
                                 factory = factory,
                                 locks = [build_lock.access('counting')],
                                 description="Create/update installer on " + platform['name'],)

    c['builders'].append(builder)

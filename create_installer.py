# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import bbconf

c = {}

vm_cpu_count = 8

mac_os_min_version = '10.11'
mac_os_sdks_path = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs'

ngftp = 'ftp://192.168.255.51/software/installer/src/'
ngftp_user = bbconf.ftp_mynextgis_user
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/ftp_uploader.py'
upload_script_name = 'ftp_upload.py'
if_project_name = 'inst_framework'

installer_git = 'git://github.com/nextgis/nextgis_installer.git'

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

project_name = 'create_installer'

forceScheduler_create = schedulers.ForceScheduler(
                            name=project_name + "_update",
                            label="Update installer",
                            buttonName="Update installer",
                            builderNames=[
                                            project_name + "_win32",
                                            project_name + "_win64",
                                            project_name + "_mac",
                                        ],
                            properties=[util.StringParameter(name="force",
                                            label="Force update specified packages even not any changes exists :",
                                            default="all", size=280),
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
                        )
c['schedulers'].append(forceScheduler_create)
c['schedulers'].append(forceScheduler_update)

platforms = [
    {'name' : 'win32', 'worker' : 'build-win'},
    {'name' : 'win64', 'worker' : 'build-win'},
    {'name' : 'mac', 'worker' : 'build-mac'} ]

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
    build_dir_name = 'inst'
    build_dir = os.path.join(code_dir, build_dir_name)

    factory = util.BuildFactory()

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
    if 'win' in platform['name']:
        if_prefix = '_win'
        separator = '\\'

    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp_user, ngftp + if_project_name + if_prefix + '/package.zip', '-o', 'package.zip', '-s'],
                                           name="Download installer package",
                                           haltOnFailure=True,
                                           workdir=build_dir))
    factory.addStep(steps.ShellCommand(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'],
                                           name="Extract installer package",
                                           haltOnFailure=True,
                                           workdir=build_dir))

    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp_user, ngftp + if_project_name + if_prefix + '/qt/package.zip', '-o', 'package.zip', '-s'],
                                           name="Download qt package",
                                           haltOnFailure=True,
                                           workdir=build_dir))
    factory.addStep(steps.ShellCommand(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'],
                                           name="Extract qt package",
                                           haltOnFailure=True,
                                           workdir=build_dir))

    # 2. Get repository from ftp
    factory.addStep(steps.ShellCommand(command=["curl", '-u', ngftp_user, ngftp + 'repo_' + platform['name'] + '/package.zip', '-o', 'package.zip', '-s'],
                                           name="Download repository",
                                           haltOnFailure=False, # The repository may not be exists
                                           workdir=build_dir))
    factory.addStep(steps.ShellCommand(command=["cmake", '-E', 'tar', 'xzf', 'package.zip'],
                                           name="Extract repository from archive",
                                           haltOnFailure=False, # The repository may not be exists
                                           workdir=build_dir))

    # 3. Get compiled libraries
    factory.addStep(steps.ShellCommand(command=["python", 'opt' + separator + 'create_installer.py',
        'prepare', '--ftp_user', ngftp_user, '--ftp', ngftp, '--target_dir', build_dir_name],
                                           name="Prepare packages data",
                                           haltOnFailure=True,
                                           workdir=code_dir))
    # 4. Create or update repository

    # 5. Upload repository archive to site

    # 6. Upload repository archive to ftp

    builder = util.BuilderConfig(name = "Create/update installer on " + platform['name'], #project_name + "_" + platform['name'],
                                 workernames = [platform['worker']],
                                 factory = factory)

    c['builders'].append(builder)

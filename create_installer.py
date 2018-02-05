# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import sys
import os
import bbconf

c = {}

vm_cpu_count = 8

max_os_min_version = '10.11'
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

forceScheduler = schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[
                                            project_name + "_win32",
                                            project_name + "_win64",
                                            project_name + "_mac",
                                        ])
c['schedulers'].append(forceScheduler)

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
    build_dir = os.path.join(code_dir, 'build')
    build_qt_dir = os.path.join(code_dir, 'qt')

    factory = util.BuildFactory()

    factory.addStep(steps.Git(repourl=installer_git,
                               mode='full',
                               submodules=False,
                               workdir=code_dir))

    factory.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make build directory"))
    factory.addStep(steps.MakeDirectory(dir=build_qt_dir,
                                        name="Make qt static directory"))

    # 1. Get and unpack installer and qt5 static from ftp
    if_prefix = '_mac'
    if 'win' in platform['name']:
        if_prefix = '_win'

    factory.addStep(steps.ShellCommand(command=["curl", ngftp + if_project_name + if_prefix + '/package.zip', '-o', 'package.zip', '-s'],
                                           name="Download installer package",
                                           haltOnFailure=True,
                                           workdir=build_dir))

    factory.addStep(steps.ShellCommand(command=["curl", ngftp + if_project_name + if_prefix + '/qt/package.zip', '-o', 'package.zip', '-s'],
                                           name="Download qt package",
                                           haltOnFailure=True,
                                           workdir=build_qt_dir))

    # 2. Get repository from ftp
    
    # 3. Get compiled libraries
    # 4. Create or update repository
    # 5. Upload repository archive to site
    # 6. Upload repository archive to ftp

    builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
                                 workernames = [platform['worker']],
                                 factory = factory)

    c['builders'].append(builder)

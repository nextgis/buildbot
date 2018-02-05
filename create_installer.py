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
    {'name' : 'win64', 'worker' : 'build-win' },
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

    factory = util.BuildFactory()

    factory.addStep(steps.Git(repourl=installer_git,
                               mode='full',
                               submodules=False,
                               workdir=code_dir))

    factory.addStep(steps.MakeDirectory(dir=build_dir,
                                        name="Make"))
    # 1. Get repository
    # 2. Get compiled libraries

    builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
                                 workernames = [platform['worker']],
                                 factory = factory)

    c['builders'].append(builder)

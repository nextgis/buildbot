# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
from buildbot.steps.source.git import Git
from buildbot.steps.python import Sphinx
from buildbot.steps.transfer import DirectoryUpload
from buildbot.changes.gitpoller import GitPoller
from buildbot.schedulers.basic  import SingleBranchScheduler
from buildbot.config import BuilderConfig
from buildbot.steps.master import MasterShellCommand
from buildbot.status.mail import MailNotifier

import bbconf

c = {}

repourl = 'git://github.com/nextgis/android_nextgis_mobile.git'
project_name = 'ngm3'
ftp = 'ftp://192.168.255.1/'
myftp = 'ftp://192.168.255.51/'

git_poller = GitPoller(
    project = project_name,
    repourl = repourl,
    workdir = project_name + '-workdir',
    branch = 'master',
    pollinterval = 3600 # each 1 hour
)
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
    name=project_name,
    change_filter=util.ChangeFilter(project = project_name),
    treeStableTimer=2*60,
    builderNames=[project_name]
)
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
    name=project_name + "_force",
    builderNames=[project_name]
))

#### build NextGIS Mobile v3 release apk

factory = util.BuildFactory()

factory.addStep(steps.Git(
    repourl=repourl,
    mode='incremental', #mode='full', method='clobber'
    submodules=True))

#factory.addStep(steps.ShellCommand(
#    command=['chmod', '+x', 'gradlew'],
#    name='Fix premissions',
#    description=["fix", "permissions"],
#    descriptionDone=["fixed", "permissions"],
#    haltOnFailure=True
#))

# Clean. Do not clean app/.externalNativeBuild/third-party-src
factory.addStep(steps.RemoveDirectory(dir="build/.gradle"))
factory.addStep(steps.RemoveDirectory(dir="build/app/build"))
factory.addStep(steps.RemoveDirectory(dir="build/app/.externalNativeBuild/cmake"))
factory.addStep(steps.RemoveDirectory(dir="build/build"))
factory.addStep(steps.RemoveDirectory(dir="build/libngui/build"))

factory.addStep(steps.ShellCommand(
    command=["cp", "--remove-destination", "../sentry.properties.ngm3", "build/sentry.properties"],
    name='Copy sentry.properties',
    description=["Copy", "sentry.properties"],
    descriptionDone=["Copied", "sentry.properties"],
    haltOnFailure=True
))
factory.addStep(steps.ShellCommand(
    command=["/bin/bash", "gradlew", "--info", "assembleRelease"],
    name='create apk',
    description=["prepare", "environment for build"],
    descriptionDone=["prepared", "environment for build"],
    env={
        'ANDROID_HOME': '/opt/android-sdk-linux',
        'ANDROID_NDK_HOME': '/opt/android-sdk-linux/ndk-bundle'
    },
    haltOnFailure=True
))
factory.addStep(steps.ShellCommand(
    command=['dch.py', '-n', 'test', '-a', 'NextGIS Mobile v3', '-p', 'simple',
        '-f', '.', '-o', 'app/build/outputs/apk/git.log'],
    name='log last comments',
    description=["log", "last comments"],
    descriptionDone=["logged", "last comments"],
    haltOnFailure=True
))

# Simlink is needed from testfairy-upload-android-ngm3.sh to virtual env/bin
# ln -s /full/path/to/testfairy-upload-android-ngm3.sh env/bin/
#factory.addStep(steps.ShellCommand(
#    command=['/bin/bash', 'testfairy-upload-android-ngm3.sh', 'app/build/outputs/apk'],
#    description=["upload", "testfairy"],
#    descriptionDone=["uploaded", "testfairy"],
#    haltOnFailure=True
#))

# Upload apk to ftp
#ftp_upload_command = "curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T file ftp://nextgis.ru/programs/ngm3/"
#upld_file_lst = ['app/build/outputs/apk/ngmobile3-' + project_ver + '.apk']
upld_file_lst = ['app/build/outputs/apk/ngmobile3-0.4.apk']
for upld_file in upld_file_lst:
    factory_win.addStep(steps.ShellCommand(
        command=['curl', '-u', bbconf.ftp_mynextgis_user, '-T', upld_file, '--ftp-create-dirs', myftp + 'ngm3/'],
        name="upload to ftp",
        description=["upload", "to ftp " + upld_file],
        descriptionDone=["uploaded", "NGM3 files to ftp"],
        haltOnFailure=False,
        workdir="build/"
    ))

factory.addStep(steps.ShellCommand(
    command=['dch.py', '-n', 'test', '-a', 'NextGIS Mobile v3', '-p', 'store', '-f', '.'],
    name='log last comments',
    description=["log", "last comments"],
    descriptionDone=["logged", "last comments"],
    haltOnFailure=True
))


builder = BuilderConfig(name = project_name, slavenames = ['build-nix'], factory = factory)
c['builders'] = [builder]

# NOTIFIER
ngm3_mn = MailNotifier(fromaddr='buildbot@nextgis.com',
                       sendToInterestedUsers=True,
                       builders=[builder.name],
                       mode=('all'),
                       extraRecipients=bbconf.ngm_email_recipients,
                       relayhost='192.168.255.1',
                       useTls=True
                      )

c['status'] = [ngm3_mn]

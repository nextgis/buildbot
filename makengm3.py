# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import bbconf

c = {}

repourl = 'git://github.com/nextgis/android_nextgis_mobile.git'
project_name = 'ngm3'
git_project_name = 'nextgis/android_nextgis_mobile'
apk_ver = '0.5'
apk_file_name_unsigned = 'ngmobile3-' + apk_ver + '.apk'
apk_file_name_signed = 'ngmobile3-' + apk_ver + '-release.apk'

android_home = '/opt/android-sdk-linux'
android_ndk_home = android_home + '/ndk-bundle'
# We are using apksigner, then the min version of the build tools is 24.0.3
android_build_tools_version = '25.0.2'
android_build_tools = android_home + '/build-tools/' + android_build_tools_version

myftp = 'ftp://192.168.255.51/'


git_poller = changes.GitPoller(
    project = git_project_name,
    repourl = repourl,
    workdir = project_name + '-workdir',
    branch = 'master',
    pollinterval = 3600 # each 1 hour
)
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
    name=project_name,
    change_filter=util.ChangeFilter(project = git_project_name),
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
    command=["cp", "--remove-destination", "../../sentry.properties.ngm3", "sentry.properties"],
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
        'ANDROID_HOME': android_home,
        'ANDROID_NDK_HOME': android_ndk_home
    },
    haltOnFailure=True
))
# Simlink is needed from apk-signer.sh to virtual env/bin
# ln -s /full/path/to/apk-signer.sh env/bin/
factory.addStep(steps.ShellCommand(
    command=["/bin/bash", "apk-signer.sh", "app/build/outputs/apk/" + apk_file_name_unsigned, "app/build/outputs/apk/" + apk_file_name_signed],
    name='create apk',
    description=["prepare", "environment for build"],
    descriptionDone=["prepared", "environment for build"],
    env={
        'ANDROID_BUILD_TOOLS': android_build_tools
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
upld_file_lst = ['app/build/outputs/apk/' + apk_file_name_signed]
for upld_file in upld_file_lst:
    factory.addStep(steps.ShellCommand(
        command=['curl', '-u', bbconf.ftp_mynextgis_user, '-T', upld_file, '--ftp-create-dirs', myftp + 'software/' + project_name + '-dev/'],
        name="upload to ftp, folder 'software'",
        description=["upload", "to ftp " + upld_file],
        descriptionDone=["uploaded", "NGM3 files to ftp"],
        haltOnFailure=False,
        workdir="build/"
    ))
    factory.addStep(steps.ShellCommand(
        command=['curl', '-u', bbconf.ftp_mynextgis_user, '-T', upld_file, '--ftp-create-dirs', myftp + 'software_supported/' + project_name + '-dev/'],
        name="upload to ftp, folder 'software_supported'",
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


builder = util.BuilderConfig(name = project_name, slavenames = ['build-nix'], factory = factory)
c['builders'] = [builder]

# NOTIFIER
ngm3_mn = reporters.MailNotifier(
    fromaddr='buildbot@nextgis.com',
    sendToInterestedUsers=True,
    builders=[builder.name],
    mode=('all'),
    extraRecipients=bbconf.ngm_email_recipients,
    relayhost='192.168.255.1',
    useTls=True
)

c['status'] = [ngm3_mn]

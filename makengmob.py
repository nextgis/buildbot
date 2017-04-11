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

import bbconf

c = {}

repourl = 'git://github.com/nextgis/android_gisapp.git'
project_name = 'ngmob'

git_poller = GitPoller(project = project_name,
                       repourl = repourl,
                       workdir = project_name + '-workdir',
                       branch = 'master',
                       pollinterval = 7200,) # each 2 hours
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = project_name),
                            treeStableTimer=2*60,
                            builderNames=[project_name])
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[project_name],
))
#### build docs

factory = util.BuildFactory()

factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True)) #mode='full', method='clobber'

factory.addStep(steps.ShellCommand(command=['chmod', '+x', 'gradlew'],
                                 name='fix premissions',
                                 description=["fix", "permissions"],
                                 descriptionDone=["fixed", "permissions"], haltOnFailure=True))
factory.addStep(steps.RemoveDirectory(dir="build/app/build/outputs/apk"))
factory.addStep(steps.ShellCommand(command=["/bin/bash", "gradlew", "assembleRelease"],
                                            name='create apk' ,
                                            description=["prepare", "environment for build"],
                                            descriptionDone=["prepared", "environment for build"],
                                            env={'ANDROID_HOME': '/opt/android-sdk-linux'}))
factory.addStep(steps.ShellCommand(command=['dch.py', '-n', 'test', '-a', 'NextGIS Mobile', '-p', 'simple', '-f', '.', '-o', 'app/build/outputs/apk/git.log'],
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"], haltOnFailure=True))
factory.addStep(steps.ShellCommand(command=['/bin/bash', 'testfairy-upload-android.sh', 'app/build/outputs/apk'],
                                 description=["upload", "testfairy"],
                                 descriptionDone=["uploaded", "testfairy"], haltOnFailure=True))
factory.addStep(steps.ShellCommand(command=['dch.py', '-n', 'test', '-a', 'NextGIS Mobile', '-p', 'store', '-f', '.'],
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],
                                 haltOnFailure=True))


builder = BuilderConfig(name = project_name, workernames = ['build-nix'], factory = factory)
c['builders'] = [builder]

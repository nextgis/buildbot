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

repourl = 'git@github.com:nextgis/android_gisapp.git'

git_poller = GitPoller(project = 'makengmob',
                       repourl = repourl,
                       workdir = 'makengmob-workdir',
                       branch = 'master',
                       pollinterval = 36000,)

scheduler = schedulers.SingleBranchScheduler(
                            name="makengmob",
                            change_filter=util.ChangeFilter(project = 'makengmob'),
                            treeStableTimer=None,
                            builderNames=["makengmob"])
                            
#### build docs

factory = util.BuildFactory()

factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True)) #mode='full', method='clobber'

factory.addStep(steps.ShellCommand(command=["/bin/bash", "-c", "chmod +x gradlew"], 
                                 description=["fix", "permissions"],
                                 descriptionDone=["fixed", "permissions"], haltOnFailure=True))                                 
factory.addStep(steps.RemoveDirectory(dir="build/app/build/outputs/apk"))                                 
factory.addStep(steps.ShellCommand(command=["/bin/bash", "gradlew", "assembleRelease" ], 
                                            description=["make", "prepare environment for build"],
                                            descriptionDone=["made", "prepared environment for build"],
                                            env={'ANDROID_HOME': '/opt/android-sdk-linux'}))
# android_gisapp/app/build/outputs/apk generate and upload
factory.addStep(steps.ShellCommand(command=["/bin/bash", "-c", "git log --pretty=format:\"%h - %an, %ar : %s\" -2 > app/build/outputs/apk/git.log"], 
                                 description=["log", "comments"],
                                 descriptionDone=["logged", "comments"], haltOnFailure=True))  
                                            
builder = BuilderConfig(name = 'makengmob', slavenames = ['build-nix'], factory = factory)
                            

# -*- python -*-
# ex: set syntax=python:
    
from buildbot.plugins import *
from buildbot.steps.source.git import Git
from buildbot.steps.python import Sphinx
from buildbot.steps.transfer import FileUpload
from buildbot.steps.transfer import DirectoryUpload
from buildbot.changes.gitpoller import GitPoller
from buildbot.schedulers.basic  import SingleBranchScheduler
from buildbot.config import BuilderConfig
from buildbot.steps.master import MasterShellCommand
from buildbot.steps.shell import WithProperties

repourl = 'git://github.com/nextgis/buildbot.git'

git_poller = GitPoller(project = 'selfupdate',
                       repourl = repourl,
                       workdir = 'selfupdate-workdir',
                       branch = 'master',
                       pollinterval = 600,)                  
                       
scheduler = schedulers.SingleBranchScheduler(
                            name="selfupdate",
                            change_filter=util.ChangeFilter(project = 'selfupdate'),
                            treeStableTimer=None,
                            builderNames=["selfupdate"])                       
                            
#### self update
factory = util.BuildFactory()
factory.addStep(steps.Git(repourl=repourl,  mode='incremental'))
factory.addStep(FileUpload(slavesrc="master.cfg", masterdest="/home/bishop/buildbot/master/master.cfg", mode=0644))
factory.addStep(MasterShellCommand(name="reconfig", description=["reconfig", "buildbot"],
                                 descriptionDone=["reconfig", "buildbot"], haltOnFailure=True,
                                 command=["buildbot", "reconfig", "/home/bishop/buildbot/master"]))
                                 
builder = BuilderConfig(name = 'selfupdate', slavenames = ['build-nix'], factory = factory)     
                            

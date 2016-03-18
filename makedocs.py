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

repourl = 'git://github.com/nextgis/docs_ng.git'

git_poller = GitPoller(project = 'makedocs',
                       repourl = repourl,
                       workdir = 'makedocs-workdir',
                       branch = 'master',
                       pollinterval = 3600,)
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
                            name="makedocs",
                            change_filter=util.ChangeFilter(project = 'makedocs'),
                            treeStableTimer=5*60,
                            builderNames=["makedocs"])
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name="makedocs_force",
                            builderNames=["makedocs"],
))

#### build docs

factory = util.BuildFactory()
# 1. check out the source
factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True)) #mode='full', method='clobber'

# 2. build pdf for each doc except dev
factory.addStep(steps.ShellCommand(command=["sh", "make_javadoc.sh"], 
                                            description=["make", "javadoc for mobile (android)"],
                                            descriptionDone=["made", "javadoc for mobile (android)"], 
                                            workdir="build/source/ngmobile_dev"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS Mobile"],
                                            workdir="build/source/docs_ngmobile"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS Web"],
                                            workdir="build/source/docs_ngweb"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS Manager"],
                                            workdir="build/source/docs_ngmanager"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS FormBuilder"],
                                            workdir="build/source/docs_formbuilder"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS Bio"],
                                            workdir="build/source/docs_ngbio"))
factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                            description=["make", "pdf for NextGIS QGIS"],
                                            workdir="build/source/docs_ngqgis"))


# 3. build html
factory.addStep(Sphinx(sphinx_builddir="_build/html",sphinx_sourcedir="source",sphinx_builder="html"))
factory.addStep(DirectoryUpload(slavesrc="_build/html", masterdest="/usr/share/nginx/doc"))
factory.addStep(MasterShellCommand(name="chmod", description=["fixing", "permissions"],
                                 descriptionDone=["fix", "permissions"], haltOnFailure=True,
                                 command=["/bin/bash", "-c", "chmod -R 0755 /usr/share/nginx/doc/*"]))

ftp_upload_command = "find . -type f -exec curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T {} ftp://nextgis.ru/{} \;"

# 4. upload to ftp
factory.addStep(MasterShellCommand(name="upload to ftp", description=["upload", "docs directory to ftp"],
                                 descriptionDone=["upload", "docs directory to ftp"], haltOnFailure=True,
                                 command = ftp_upload_command,
                                 path="/usr/share/nginx/doc",
                                 want_stdout = False))

builder = BuilderConfig(name = 'makedocs', slavenames = ['build-nix'], factory = factory)
c['builders'] = [builder]                         

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
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repourl = 'git://github.com/nextgis/docs_ng.git'
langs = ['ru', 'en']

poller_name = 'docs'
git_poller = GitPoller(project = poller_name,
                   repourl = repourl,
                   workdir = poller_name + '-workdir',
                   branches = langs,
                   pollinterval = 1800,)
c['change_source'].append(git_poller)

for lang in langs:
    project_name = 'docs_' + lang
    
    scheduler = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = poller_name,
                                                            branch=lang),
                            treeStableTimer=5*60,
                            builderNames=[project_name])
    c['schedulers'].append(scheduler)
    c['schedulers'].append(schedulers.ForceScheduler(
                                name=project_name + "_force",
                                builderNames=[project_name],
    ))

    #### build docs

    factory = util.BuildFactory()
    # 1. check out the source
    factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True)) #mode='full', method='clobber'
    factory.addStep(steps.ShellCommand(command=["sh", "make_javadoc.sh"], 
                                      description=["make", "javadoc for mobile (android)"],
                                      descriptionDone=["made", "javadoc for mobile (android)"], 
                                      workdir="build/source/ngmobile_dev"))
    
    # 2. build pdf for each doc except dev
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
    factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                      description=["make", "pdf for NextGIS open geodata portal"],
                                      workdir="build/source/docs_ogportal"))
    factory.addStep(steps.ShellCommand(command=["make", "latexpdf"], 
                                      description=["make", "pdf for NextGIS forest inspector"],
                                      workdir="build/source/docs_forestinspector"))
    # 3. build html
    factory.addStep(Sphinx(sphinx_builddir="_build/html",sphinx_sourcedir="source",sphinx_builder="html"))
    # 4. upload to ftp
    factory.addStep(steps.ShellCommand(command=["sync.sh", lang], 
                                       description=["sync", "to web server"]))

    builder = BuilderConfig(name = project_name, slavenames = ['build-nix'], factory = factory)
    c['builders'].append(builder)
    

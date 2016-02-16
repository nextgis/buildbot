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

repourl = 'git://github.com/nextgis-extra/lib_gdal.git'

git_poller = GitPoller(project = 'makegdal',
                       repourl = repourl,
                       workdir = 'makegdal-workdir',
                       branch = 'master',
                       pollinterval = 7200,) 
                       
scheduler = schedulers.SingleBranchScheduler(
                            name="makegdal",
                            change_filter=util.ChangeFilter(project = 'makegdal'),
                            treeStableTimer=None,
                            builderNames=["makegdal"])                       
                            
#### build gdal

factory = util.BuildFactory()
# 1. check out the source
factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True)) #mode='full', method='clobber'

# 2. build gdal
# make build dir

# configure view cmake
factory.addStep(steps.ShellCommand(command=["cmake", "-DBUIDL_SHARED_LIBS=ON"], 
                                            description=["make", "javadoc for mobile (android)"],
                                            descriptionDone=["made", "javadoc for mobile (android)"], 
                                            workdir="build/source/ngmobile_dev"))
# make
# make tests
# make package
# upload package
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
                                 command=["/bin/bash", "-c", "chmod -R 0755 /usr/share/nginx/doc/"]))

ftp_upload_command = "find . -type f -exec curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T {} ftp://nextgis.ru/{} \;"

# 4. upload to ftp
factory.addStep(MasterShellCommand(name="upload to ftp", description=["upload", "docs directory to ftp"],
                                 descriptionDone=["upload", "docs directory to ftp"], haltOnFailure=True,
                                 command = ftp_upload_command,
                                 path="/usr/share/nginx/doc"))

builder = BuilderConfig(name = 'makegdal', slavenames = ['build-nix', 'build-ngq-win7', ], factory = factory)
                                                        

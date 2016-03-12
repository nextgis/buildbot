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

import bbconf

c = {}

repourl = 'git://github.com/nextgis-extra/lib_gdal.git'

git_poller = GitPoller(project = 'makegdal',
                       repourl = repourl,
                       workdir = 'makegdal-workdir',
                       branch = 'master', #TODO: buildbot
                       pollinterval = 7200,) 
c['change_source'] = [git_poller]
                       
scheduler = schedulers.SingleBranchScheduler(
                            name="makegdal",
                            change_filter=util.ChangeFilter(project = 'makegdal'),
                            treeStableTimer=1*60,
                            builderNames=["makegdal_win"])                       
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name="makegdal_force",
                            builderNames=["makegdal_win"]))      

#, "makegdal_lin"                      
#### build gdal

## common steps
cmake_config = ['-DBUILD_SHARED_LIBS=ON', '-DWITH_EXPAT=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GeoTIFF=ON', '-DWITH_GeoTIFF_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DWITH_ICONV_EXTERNAL=ON', '-DWITH_JSONC=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_LibXml2=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_PROJ4=ON', '-DWITH_PROJ4_EXTERNAL=ON', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON']
cmake_build = ['--build', '.', '--config release', '--clean-first']
cmake_pack = ['--build', '.', '--target package', '--config release']

## build win

factory_win = util.BuildFactory()
# 1. check out the source
factory_win.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=False)) #mode='full', method='clobber'

# 2. build gdal 32
# make build dir
factory_win.addStep(steps.MakeDirectory(dir="build/build32"))
# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G"Visual Studio 10"', '../'], 
                                            description=["cmake", "configure for win32"],
                                            descriptionDone=["cmake", "configured for win32"], 
                                            workdir="build/build32"))
# make
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build], 
                                            description=["cmake", "make for win32"],
                                            descriptionDone=["cmake", "made for win32"], 
                                            workdir="build/build32"))
# make tests
# make package
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack], 
                                            description=["cmake", "pack for win32"],
                                            descriptionDone=["cmake", "packed for win32"], 
                                            workdir="build/build32"))
                                            
# 3. build gdal 64
# make build dir
factory_win.addStep(steps.MakeDirectory(dir="build/build64"))
# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G"Visual Studio 10 Win64"', '../'], 
                                            description=["cmake", "configure for win64"],
                                            descriptionDone=["cmake", "configured for win64"], 
                                            workdir="build/build64"))
# make
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build], 
                                            description=["cmake", "make for win64"],
                                            descriptionDone=["cmake", "made for win64"], 
                                            workdir="build/build64"))
# make tests
# make package
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack], 
                                            description=["cmake", "pack for win64"],
                                            descriptionDone=["cmake", "packed for win64"], 
                                            workdir="build/build64"))                                            
# upload package
# TODO:
#ftp_upload_command = "find . -type f -exec curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T {} ftp://nextgis.ru/{} \;"

#factory_win.addStep(MasterShellCommand(name="upload to ftp", 
#                                 description=["upload", "docs directory to ftp"],
#                                 descriptionDone=["uploaded", "docs directory to ftp"], haltOnFailure=True,
#                                 command = ftp_upload_command,
#                                 path="/usr/share/nginx/doc"))

builder_win = BuilderConfig(name = 'makegdal_win', slavenames = ['build-ngq-win7'], factory = factory_win)

# 1. check out the source
# pack
# deb
# upload to launchpad

c['builders'] = [builder_win]                                                        

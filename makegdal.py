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
gdal_ver = '2.1.0'
deb_repourl = 'git://github.com/nextgis/ppa.git'

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
                            builderNames=["makegdal_win", "makegdal_deb"])                       
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name="makegdal_force",
                            builderNames=["makegdal_win", "makegdal_deb"]))      

#, "makegdal_lin"                      
#### build gdal

## common steps
cmake_config = ['-DBUILD_SHARED_LIBS=ON', '-DWITH_EXPAT=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GeoTIFF=ON', '-DWITH_GeoTIFF_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DWITH_ICONV_EXTERNAL=ON', '-DWITH_JSONC=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_LibXml2=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_PROJ4=ON', '-DWITH_PROJ4_EXTERNAL=ON', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DWITH_JBIG=ON', '-DWITH_JBIG_EXTERNAL=ON', '-DWITH_JPEG=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_JPEG12=ON', '-DWITH_JPEG12_EXTERNAL=ON', '-DWITH_LibLZMA=ON', '-DWITH_LibLZMA_EXTERNAL=ON', '-DPACKAGE_VENDOR=NextGIS', '-DPACKAGE_INSTALL_DIRECTORY=nextgis']
cmake_build = ['--build', '.', '--config', 'release', '--clean-first']
cmake_pack = ['--build', '.', '--target', 'package', '--config', 'release']

## build win

factory_win = util.BuildFactory()
# 1. check out the source

code_dir_last = 'gdal_code'
code_dir = 'build/' + code_dir_last
factory_win.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=False, workdir=code_dir)) #mode='full', method='clobber'

# 2. build gdal 32
# make build dir
factory_win.addStep(steps.MakeDirectory(dir=code_dir + "/build32"))
# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013', '../'], 
                                       name="configure step 1",
                                       description=["cmake", "configure for win32"],
                                       descriptionDone=["cmake", "configured for win32"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True,
                                       workdir=code_dir + "/build32"))
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013', '../'], 
                                       name="configure step 2",
                                       description=["cmake", "configure for win32"],
                                       descriptionDone=["cmake", "configured for win32"], haltOnFailure=True, 
                                       workdir=code_dir + "/build32"))
# make
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build], 
                                       name="make",
                                       description=["cmake", "make for win32"],
                                       descriptionDone=["cmake", "made for win32"], haltOnFailure=True, 
                                       workdir=code_dir + "/build32",
                                       env={'LANG': 'en_US'}))
# make tests
# make package
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack], 
                                       name="make package",
                                       description=["cmake", "pack for win32"],
                                       descriptionDone=["cmake", "packed for win32"], haltOnFailure=True, 
                                       workdir=code_dir + "/build32",
                                       env={'LANG': 'en_US'}))
                                            
# 3. build gdal 64
# make build dir
factory_win.addStep(steps.MakeDirectory(dir=code_dir + "/build64"))
# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013 Win64', '../'], 
                                       name="configure step 1",
                                       description=["cmake", "configure for win64"],
                                       descriptionDone=["cmake", "configured for win64"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True, 
                                       workdir=code_dir + "/build64"))
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013 Win64', '../'], 
                                       name="configure step 2",
                                       description=["cmake", "configure for win64"],
                                       descriptionDone=["cmake", "configured for win64"], haltOnFailure=True, 
                                       workdir=code_dir + "/build64"))                                            
# make
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build], 
                                       name="make",
                                       description=["cmake", "make for win64"],
                                       descriptionDone=["cmake", "made for win64"], haltOnFailure=True, 
                                       workdir=code_dir + "/build64",
                                       env={'LANG': 'en_US'}))
# make tests
# make package
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack], 
                                       name="make package",
                                       description=["cmake", "pack for win64"],
                                       descriptionDone=["cmake", "packed for win64"], haltOnFailure=True, 
                                       workdir=code_dir + "/build64",
                                       env={'LANG': 'en_US'}))                                            
# upload package
#ftp_upload_command = "curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T file ftp://nextgis.ru/programs/gdal/"
upld_file_lst = ['build32/GDAL-' + gdal_ver + '-win32.exe', 'build32/GDAL-' + gdal_ver + '-win32.zip', 'build64/GDAL-' + gdal_ver + '-win64.exe', 'build64/GDAL-' + gdal_ver + '-win64.zip']
for upld_file in upld_file_lst:
    factory_win.addStep(steps.ShellCommand(command=['curl', '-u', bbconf.ftp_upldsoft_user, 
                                           '-T', upld_file, '--ftp-create-dirs', 'ftp://nextgis.ru/programs/gdal/'],
                                           name="upload to ftp " + upld_file, 
                                           description=["upload", "gdal files to ftp"],
                                           descriptionDone=["uploaded", "gdal files to ftp"], haltOnFailure=False, 
                                           workdir= code_dir ))

builder_win = BuilderConfig(name = 'makegdal_win', slavenames = ['build-ngq-win7'], factory = factory_win)

# 1. check out the source
factory_deb = util.BuildFactory()
ubuntu_distributions = ['trusty', 'wily']
# 1. check out the source
deb_dir = 'build/gdal_deb'

factory_deb.addStep(steps.Git(repourl=deb_repourl, mode='incremental', submodules=False, workdir=deb_dir, alwaysUseLatest=True))
factory_deb.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))
# tar orginal sources
factory_deb.addStep(steps.ShellCommand(command=["rm", '-rf', 'gdal_' + gdal_ver + '.orig.tar.gz'], 
                                       name="rm",
                                       description=["rm", "delete"],
                                       descriptionDone=["rm", "deleted"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True))
factory_deb.addStep(steps.ShellCommand(command=["tar", '-caf', 'gdal_' + gdal_ver + '.orig.tar.gz', code_dir_last, '--exclude-vcs'], 
                                       name="tar",
                                       description=["tar", "compress"],
                                       descriptionDone=["tar", "compressed"], haltOnFailure=True))
# copy lib_gdal -> debian
factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/gdal/debian", dest=code_dir + "/debian", 
                                        name="add debian folder", haltOnFailure=True))
# update changelog
for ubuntu_distribution in ubuntu_distributions:
    factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', gdal_ver, '-a', 
                                                'gdal', '-p', 'fill', '-f', 
                                                code_dir_last,'-o', 'changelog', '-d', 
                                                ubuntu_distribution], 
                                        name='create changelog',
                                        description=["create", "changelog"],
                                        descriptionDone=["created", "changelog"],
                                        env={'DEBEMAIL': 'dmitry.baryshnikov@nextgis.com', 'DEBFULLNAME':'Dmitry Baryshnikov'},           
                                        haltOnFailure=True)) 
    # deb ?
    # upload to launchpad

# store changelog
factory_deb.addStep(steps.ShellCommand(command=['dch.py' '-n', gdal_ver, '-a', 'gdal', '-p', 'store', '-f', code_dir_last,'-o', 'changelog'], 
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],           
                                 haltOnFailure=True))  
                                       
builder_deb = BuilderConfig(name = 'makegdal_deb', slavenames = ['build-nix'], factory = factory_deb)

c['builders'] = [builder_win, builder_deb]                                                        

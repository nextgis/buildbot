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

repourl = 'git://github.com/nextgis-borsch/lib_gdal.git'
project_ver = '2.1.1'
deb_repourl = 'git://github.com/nextgis/ppa.git'
project_name = 'gdal'

git_poller = GitPoller(project = project_name,
                       repourl = repourl,
                       workdir = project_name + '-workdir',
                       branches = ['master', 'dev'],
                       pollinterval = 7200,) 
c['change_source'] = [git_poller]
                       
scheduler1 = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = project_name, branch="master"),
                            treeStableTimer=1*60,
                            builderNames=[project_name + "_win", project_name + "_deb"])                       
scheduler2 = schedulers.SingleBranchScheduler(
                            name=project_name + "_dev",
                            change_filter=util.ChangeFilter(project = project_name, branch="dev"),
                            treeStableTimer=1*60,
                            builderNames=[project_name + "_debdev"])                       
c['schedulers'] = [scheduler1, scheduler2]
c['schedulers'].append(schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[project_name + "_win", project_name + "_deb"]))      

#### build gdal

## common steps

## maximum formats even disabled in oficial build should be present here
cmake_config = ['-DBUILD_SHARED_LIBS=ON', '-DWITH_EXPAT=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GeoTIFF=ON', '-DWITH_GeoTIFF_EXTERNAL=ON', '-DWITH_ICONV=ON', '-DWITH_ICONV_EXTERNAL=ON', '-DWITH_JSONC=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_LibXml2=ON', '-DWITH_LibXml2_EXTERNAL=ON', '-DWITH_PROJ4=ON', '-DWITH_PROJ4_EXTERNAL=ON', '-DWITH_TIFF=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_ZLIB=ON', '-DWITH_ZLIB_EXTERNAL=ON', '-DWITH_JBIG=ON', '-DWITH_JBIG_EXTERNAL=ON', '-DWITH_JPEG=ON', '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_JPEG12=ON', '-DWITH_JPEG12_EXTERNAL=ON', '-DWITH_LibLZMA=ON', '-DWITH_LibLZMA_EXTERNAL=ON', '-DWITH_GEOS=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DPACKAGE_VENDOR=NextGIS', '-DPACKAGE_INSTALL_DIRECTORY=nextgis', '-DWITH_PYTHON=ON', '-DWITH_PYTHON3=OFF', '-DWITH_SQLite3=ON', '-DWITH_SQLite3_EXTERNAL=ON', '-DWITH_PNG=ON', '-DWITH_PNG_EXTERNAL=ON', '-DWITH_CURL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DWITH_OpenSSL=ON', '-DWITH_OpenSSL_EXTERNAL=ON', '-DENABLE_OZI=ON', '-DWITH_PostgreSQL=ON', '-DWITH_PostgreSQL_EXTERNAL=ON', '-DENABLE_NITF_RPFTOC_ECRGTOC=ON', '-DENABLE_HDF4=ON', '-DWITH_HDF4=ON', '-DWITH_HDF4_EXTERNAL=ON', '-DGDAL_ENABLE_GNM=ON']
cmake_build = ['--build', '.', '--config', 'release', '--clean-first']
cmake_pack = ['--build', '.', '--target', 'package', '--config', 'release']
ftp = 'ftp://192.168.255.1/'
myftp = 'ftp://192.168.255.51/'

## build windows ###############################################################

factory_win = util.BuildFactory()
# 1. check out the source

code_dir_last = 'gdal_code'
code_dir = 'build/' + code_dir_last
factory_win.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=False, workdir=code_dir)) #mode='full', method='clobber'

# fill log file
gdal_latest_file = 'gdal_latest.log'
factory_win.addStep(steps.ShellCommand(command=['c:\Python2712\python', '../../dch.py', 
                                                '-n', project_ver, '-a', 'GDAL', '-p', 
                                                'simple', '-f', code_dir_last, '-o', 
                                                gdal_latest_file], 
                                        name='log last comments',
                                        description=["log", "last comments"],
                                        descriptionDone=["logged", "last comments"], haltOnFailure=True))  

# 2. build gdal 32
# make build dir
factory_win.addStep(steps.MakeDirectory(dir=code_dir + "/build32"))
# configure view cmake
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013', '-T', 'v120_xp', '../'], 
                                       name="configure step 1",
                                       description=["cmake", "configure for win32"],
                                       descriptionDone=["cmake", "configured for win32"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True,
                                       workdir=code_dir + "/build32"))
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013', '-T', 'v120_xp', '../'], 
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
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013 Win64', '-T', 'v120_xp', '../'], 
                                       name="configure step 1",
                                       description=["cmake", "configure for win64"],
                                       descriptionDone=["cmake", "configured for win64"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True, 
                                       workdir=code_dir + "/build64"))
factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config, '-G', 'Visual Studio 12 2013 Win64', '-T', 'v120_xp', '../'], 
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
upld_file_lst = ['build32/GDAL-' + project_ver + '-win32.exe', 'build32/GDAL-' + project_ver + '-win32.zip', 'build64/GDAL-' + project_ver + '-win64.exe', 'build64/GDAL-' + project_ver + '-win64.zip']
for upld_file in upld_file_lst:
    factory_win.addStep(steps.ShellCommand(command=['curl', '-u', bbconf.ftp_mynextgis_user, 
                                           '-T', upld_file, '--ftp-create-dirs', myftp + 'gdal/'],
                                           name="upload to ftp", 
                                           description=["upload", "to ftp " + upld_file],
                                           descriptionDone=["uploaded", "gdal files to ftp"], haltOnFailure=False, 
                                           workdir= code_dir ))
#generate and load gdal_latest.log
factory_win.addStep(steps.ShellCommand(command=['curl', '-u', bbconf.ftp_upldsoft_user, 
                                           '-T', gdal_latest_file, '--ftp-create-dirs', ftp + 'qgis/'],
                                           name="upload to ftp gdal_latest.log", 
                                           description=["upload", "gdal files to ftp"],
                                           descriptionDone=["uploaded", "gdal files to ftp"], haltOnFailure=False))
         
factory_win.addStep(steps.ShellCommand(command=['c:\Python2712\python', '../../dch.py', 
                                                '-n', project_ver, '-a', 'GDAL', '-p', 
                                                'store', '-f', code_dir_last], 
                                       name='log last comments',
                                       description=["log", "last comments"],
                                       descriptionDone=["logged", "last comments"], haltOnFailure=True))  
                                                                            
builder_win = BuilderConfig(name = project_name + '_win', slavenames = ['build-ngq-win7'], factory = factory_win)

## release build ###############################################################
factory_deb = util.BuildFactory()
ubuntu_distributions = ['trusty', 'xenial']
# check out the source
deb_name = 'gdal'
deb_dir = 'build/gdal_deb'
deb_email = 'dmitry.baryshnikov@nextgis.com'
deb_fullname = 'Dmitry Baryshnikov'

factory_deb.addStep(steps.Git(repourl=deb_repourl, mode='incremental', submodules=False, workdir=deb_dir, alwaysUseLatest=True))
factory_deb.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))
#cleanup
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']
for clean_ext in clean_exts:
    factory_deb.addStep(steps.ShellCommand(command=['/bin/bash', '-c', 'rm *' + clean_ext], 
                                       name="rm of " + clean_ext,
                                       description=["rm", "delete"],
                                       descriptionDone=["rm", "deleted"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True))
# tar orginal sources
factory_deb.addStep(steps.ShellCommand(command=["dch.py", '-n', project_ver, '-a', 
                                                deb_name, '-p', 'tar', '-f', 
                                                code_dir_last], 
                                       name="tar",
                                       description=["tar", "compress"],
                                       descriptionDone=["tar", "compressed"], haltOnFailure=True))
# copy lib_gdal2 -> debian
factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/" + deb_name + "/master/debian", dest=code_dir + "/debian", 
                                        name="add debian folder", haltOnFailure=True))
# update changelog
for ubuntu_distribution in ubuntu_distributions:
    factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', 
                                                deb_name, '-p', 'fill', '-f', 
                                                code_dir_last,'-o', 'changelog', '-d', 
                                                ubuntu_distribution], 
                                        name='create changelog for ' + ubuntu_distribution,
                                        description=["create", "changelog"],
                                        descriptionDone=["created", "changelog"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 
                                        
    # debuild -us -uc -d -S
    factory_deb.addStep(steps.ShellCommand(command=['debuild', '-us', '-uc', '-S'], 
                                        name='debuild for ' + ubuntu_distribution,
                                        description=["debuild", "package"],
                                        descriptionDone=["debuilded", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True,
                                        workdir=code_dir)) 
                                                                       
    factory_deb.addStep(steps.ShellCommand(command=['debsign.sh', project_name + "_deb"], 
                                        name='debsign for ' + ubuntu_distribution,
                                        description=["debsign", "package"],
                                        descriptionDone=["debsigned", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 
    # upload to launchpad
    factory_deb.addStep(steps.ShellCommand(command=['/bin/bash','-c',
                                        'dput ppa:nextgis/ppa ' +  deb_name + '*' + ubuntu_distribution + '1_source.changes'], 
                                        name='dput for ' + ubuntu_distribution,
                                        description=["dput", "package"],
                                        descriptionDone=["dputed", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 

# store changelog
factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last,'-o', 'changelog'], 
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],           
                                 env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                 haltOnFailure=True))  
                                       
builder_deb = BuilderConfig(name = project_name + '_deb', slavenames = ['build-nix'], factory = factory_deb)

## development build ###########################################################
factory_debdev = util.BuildFactory()
ubuntu_distributions_dev = ['precise', 'trusty', 'xenial']
# check out the source
debdev_dir = 'build/gdal_debdev'

factory_debdev.addStep(steps.Git(repourl=deb_repourl, mode='incremental', submodules=False, workdir=debdev_dir, alwaysUseLatest=True))
factory_debdev.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))
#cleanup
for clean_ext in clean_exts:
    factory_debdev.addStep(steps.ShellCommand(command=['/bin/bash', '-c', 'rm *' + clean_ext], 
                                       name="rm of " + clean_ext,
                                       description=["rm", "delete"],
                                       descriptionDone=["rm", "deleted"], 
                                       haltOnFailure=False, warnOnWarnings=True, 
                                       flunkOnFailure=False, warnOnFailure=True))
# tar orginal sources
factory_debdev.addStep(steps.ShellCommand(command=["dch.py", '-n', project_ver, '-a', 
                                                deb_name, '-p', 'tar', '-f', 
                                                code_dir_last], 
                                       name="tar",
                                       description=["tar", "compress"],
                                       descriptionDone=["tar", "compressed"], haltOnFailure=True))
# copy lib_gdal2 -> debian
factory_debdev.addStep(steps.CopyDirectory(src=debdev_dir + "/" + deb_name + "/dev/debian", dest=code_dir + "/debian", 
                                        name="add debian folder", haltOnFailure=True))
# update changelog
for ubuntu_distribution in ubuntu_distributions_dev:
    factory_debdev.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', 
                                                deb_name, '-p', 'fill', '-f', 
                                                code_dir_last,'-o', 'changelog', '-d', 
                                                ubuntu_distribution], 
                                        name='create changelog for ' + ubuntu_distribution,
                                        description=["create", "changelog"],
                                        descriptionDone=["created", "changelog"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 
                                        
    # debuild -us -uc -d -S
    factory_debdev.addStep(steps.ShellCommand(command=['debuild', '-us', '-uc', '-S'], 
                                        name='debuild for ' + ubuntu_distribution,
                                        description=["debuild", "package"],
                                        descriptionDone=["debuilded", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True,
                                        workdir=code_dir)) 
                                                                       
    factory_debdev.addStep(steps.ShellCommand(command=['debsign.sh', project_name + "_debdev"], 
                                        name='debsign for ' + ubuntu_distribution,
                                        description=["debsign", "package"],
                                        descriptionDone=["debsigned", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 
    # upload to launchpad
    factory_debdev.addStep(steps.ShellCommand(command=['/bin/bash','-c',
                                        'dput ppa:nextgis/dev ' +  deb_name + '*' + ubuntu_distribution + '1_source.changes'], 
                                        name='dput for ' + ubuntu_distribution,
                                        description=["dput", "package"],
                                        descriptionDone=["dputed", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                        haltOnFailure=True)) 

# store changelog
factory_debdev.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last,'-o', 'changelog'], 
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],           
                                 env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                 haltOnFailure=True))  
                                       
builder_debdev = BuilderConfig(name = project_name + '_debdev', slavenames = ['build-nix'], factory = factory_debdev)

c['builders'] = [builder_win, builder_deb, builder_debdev]                                                        

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

repourl = 'git://github.com/nextgis-borsch/postgis.git'
project_ver = '2.2.2'
deb_repourl = 'git://github.com/nextgis/ppa.git'
project_name = 'postgis'

git_poller = GitPoller(project = project_name,
                       repourl = repourl,
                       workdir = project_name + '-workdir',
                       branch = 'master', #TODO: buildbot
                       pollinterval = 7200,) 
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = project_name),
                            treeStableTimer=1*60,
                            builderNames=[project_name + "_deb"])                       
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[project_name + "_deb"]))      

deb_name = 'postgis'

code_dir_last = deb_name + '_code'
code_dir = 'build/' + code_dir_last

# 1. check out the source
factory_deb = util.BuildFactory()
ubuntu_distributions = ['trusty', 'xenial']
postgis_versions = ['9.3', '9.5']
# 1. check out the source
deb_dir = 'build/' + deb_name + '_deb'
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

for ubuntu_distribution, postgis_version in (zip(ubuntu_distributions, postgis_versions)):	 
                                          
    # copy lib_gdal2 -> debian
    factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/" + deb_name + "/pg" + postgis_version + "/debian", dest=code_dir + "/debian", 
                                            name="add debian folder for " + postgis_version, haltOnFailure=True))

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
    # delete code_dir + "/debian"
    factory_deb.addStep(steps.RemoveDirectory(dir=code_dir + "/debian", 
                                              name="remove debian folder for " + postgis_version, 
                                              haltOnFailure=True))
    
# store changelog
factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last,'-o', 'changelog'], 
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],           
                                 env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},           
                                 haltOnFailure=True))  
                                       
builder_deb = BuilderConfig(name = project_name + '_deb', slavenames = ['build-nix'], factory = factory_deb)

c['builders'] = [builder_deb]     

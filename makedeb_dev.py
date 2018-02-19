# -*- python -*-
# ex: set syntax=python:
# opencad developer build into nextgis dev ppa

from buildbot.plugins import *

c = {}

repositories = [
    {'repo':'lib_gdal', 'version':'2.3.4', 'deb':'gdal'},
    {'repo':'lib_opencad','version':'0.3.3', 'deb':'opencad'},
]

deb_repourl = 'git://github.com/nextgis/ppa.git'
ubuntu_distributions = ['trusty', 'xenial', 'artful']
deb_email = 'dmitry.baryshnikov@nextgis.com'
deb_fullname = 'Dmitry Baryshnikov'
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

# Create builders
for repository in repositories:
    project_name = repository['repo']
    repourl = 'git://github.com/nextgis-borsch/{}.git'.format(project_name)
    project_ver = repository['version']
    git_project_name = 'nextgis-borsch/{}'.format(project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-dev' + '-workdir',
                           branches = ['dev'],
                           pollinterval = 7200,)
    c['change_source'].append(git_poller)

    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name + "_debdev",
                                change_filter=util.ChangeFilter(project = git_project_name, branch="dev"),
                                treeStableTimer=1*60,
                                builderNames=[project_name + "_debdev"])
    c['schedulers'].append(scheduler)

    c['schedulers'].append(schedulers.ForceScheduler(
                                name=project_name + "_force_debdev",
                                builderNames=[project_name + "_debdev"]))

    deb_name = repository['deb']

    code_dir_last = deb_name + '_code'
    code_dir = 'build/' + code_dir_last

    ## release build ###############################################################
    factory_deb = util.BuildFactory()

    # 1. check out the source
    deb_dir = 'build/' + deb_name + '_debdev'

    factory_deb.addStep(steps.Git(repourl=deb_repourl,
                                mode='incremental',
                                submodules=False,
                                workdir=deb_dir,
                                alwaysUseLatest=True))
    factory_deb.addStep(steps.Git(repourl=repourl,
                                mode='full',
                                submodules=False,
                                workdir=code_dir))

    #cleanup
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

    for ubuntu_distribution in ubuntu_distributions:

        # copy lib_opencad -> debian
        factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/" + deb_name + "/master/debian",
                                               dest=code_dir + "/debian",
                                               name="add debian folder for " + deb_name,
                                               description=["copy", "debian folder"],
                                               descriptionDone=["copied", "debian folder"],
                                               haltOnFailure=True))

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
                                        'dput ppa:nextgis/dev ' +  deb_name + '*' + ubuntu_distribution + '1_source.changes'],
                                        name='dput for ' + ubuntu_distribution,
                                        description=["dput", "package"],
                                        descriptionDone=["dputed", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                        haltOnFailure=True))
        # delete code_dir + "/debian"
        factory_deb.addStep(steps.RemoveDirectory(dir=code_dir + "/debian",
                                              name="remove debian folder for " + deb_name,
                                              haltOnFailure=True))

    # store changelog
    factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last,'-o', 'changelog'],
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],
                                 env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                 haltOnFailure=True))

    builder_deb = util.BuilderConfig(name = project_name + '_debdev',
        workernames = ['build-nix'], factory = factory_deb,
        description =  "Make NextGIS dev Ubuntu ppa package")

    c['builders'].append(builder_deb)

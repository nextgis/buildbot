# -*- python -*-
# ex: set syntax=python:
# opencad developer build into nextgis dev ppa

from buildbot.plugins import *

c = {}

repositories = [
    {'repo':'lib_geos', 'version':'3.7.0', 'deb':'geos', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'lib_gdal', 'version':'2.4.0', 'deb':'gdal', 'subdir': 'master', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'lib_qscintilla', 'version':'2.10.4', 'deb':'qscintilla', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'py_future', 'version':'0.17.1', 'deb':'python-future', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/90/52/e20466b85000a181e1e144fd8305caf2cf475e2f9674e797b222f8105f5f/future-0.17.1.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'py_raven', 'version':'6.9.0', 'deb':'python-raven', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/8f/80/e8d734244fd377fd7d65275b27252642512ccabe7850105922116340a37b/raven-6.9.0.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'py_setuptools', 'version':'40.6.3', 'deb':'python-setuptools', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/setuptools-40.6.3.zip', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'lib_opencad','version':'0.3.4', 'deb':'opencad', 'subdir': 'master', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'lib_oci','version':'12.2.0.1', 'deb':'oci', 'subdir': '', 'org':'nextgis-borsch', 'url': 'http://dev.nextgis.com/third-party/oci/current/lin/lib.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'postgis','version':'2.4.4', 'deb':'postgis', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'nextgisutilities','version':'0.1.0', 'deb':'nextgisutilities', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'dante','version':'1.4.2', 'deb':'dante', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'pam-pgsql','version':'0.7.3.3', 'deb':'pam-pgsql', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'nextgisqgis','version':'18.12.0', 'deb':'nextgisqgis', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'lib_ngstd','version':'0.9.1', 'deb':'ngstd', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'formbuilder','version':'2.2', 'deb':'formbuilder', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['bionic']},
    {'repo':'protobuf-c','version':'1.3.0', 'deb':'protobuf-c', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'protobuf','version':'3.5.1', 'deb':'protobuf', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'mapserver','version':'7.2.1', 'deb':'mapserver', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    {'repo':'manuscript','version':'0.1.0', 'deb':'manuscript', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['bionic']},
]

deb_repourl = 'git://github.com/nextgis/ppa.git'
deb_email = 'dmitry.baryshnikov@nextgis.com'
deb_fullname = 'Dmitry Baryshnikov'
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

env = {'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname}

# Create builders
for repository in repositories:
    project_name = repository['repo']
    org = repository['org']
    repourl = 'git://github.com/{}/{}.git'.format(org, project_name)
    project_ver = repository['version']
    git_project_name = '{}/{}'.format(org, project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-workdir',
                           branches = ['master'],
                           pollinterval = 5400,)
    c['change_source'].append(git_poller)

    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name + "_deb",
                                change_filter=util.ChangeFilter(project = git_project_name, branch="master"),
                                treeStableTimer=1*60,
                                builderNames=[project_name + "_deb"])
    c['schedulers'].append(scheduler)

    c['schedulers'].append(schedulers.ForceScheduler(
                                name=project_name + "_force_deb",
                                builderNames=[project_name + "_deb"]))

    deb_name = repository['deb']

    code_dir_last = deb_name + '_code'
    code_dir = 'build/' + code_dir_last

    ## release build ###############################################################
    factory_deb = util.BuildFactory()

    # 1. check out the source
    deb_dir = 'build/' + deb_name + '_deb'

    factory_deb.addStep(steps.Git(repourl=deb_repourl,
                                mode='incremental',
                                submodules=False,
                                workdir=deb_dir,
                                alwaysUseLatest=True))
    factory_deb.addStep(steps.Git(repourl=repourl,
                                mode='full',
                                submodules=False,
                                workdir=code_dir))

    if repository['url']:
        url = repository['url']
        file_name = url[url.rfind("/")+1:]
        file_name = file_name.replace('.zip', '.tar.gz')
        factory_deb.addStep(steps.ShellCommand(command=["curl", url, '-o', file_name, '-s', '-L'],
            name='get package sources',
            env=env,
            workdir=code_dir,
            haltOnFailure=True))

    if deb_name == 'nextgisqgis':
        factory_deb.addStep(steps.ShellCommand(command=["python", 'opt/ppa_prepare.py'],
            name='Get local copy of plugins sources',
            env=env,
            workdir=code_dir,
            haltOnFailure=True))

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



    for ubuntu_distribution in repository['ubuntu_distributions']:
        # For postgis
        if repository['repo'] == 'postgis':
            if ubuntu_distribution == 'trusty':
                repository['subdir'] = 'pg9.3'
            elif ubuntu_distribution == 'xenial':
                repository['subdir'] = 'pg9.5'
            elif ubuntu_distribution == 'artful':
                repository['subdir'] = 'pg9.6'
            elif ubuntu_distribution == 'bionic':
                repository['subdir'] = 'pg10.0'

        # For qscintilla
        if repository['repo'] == 'lib_qscintilla' or repository['repo'] == 'protobuf' or repository['repo'] == 'protobuf-c' or repository['repo'] == 'mapserver':
            if ubuntu_distribution == 'trusty':
                repository['subdir'] = 'trusty'
            elif ubuntu_distribution == 'xenial':
                repository['subdir'] = 'xenial'
            elif ubuntu_distribution == 'bionic':
                repository['subdir'] = 'bionic'

        # copy lib_opencad -> debian
        factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/" + deb_name + "/" + repository['subdir'] + "/debian",
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
                                        env=env,
                                        haltOnFailure=True))

        # debuild -us -uc -d -S
        factory_deb.addStep(steps.ShellCommand(command=['debuild', '-us', '-uc', '-S'],
                                        name='debuild for ' + ubuntu_distribution,
                                        description=["debuild", "package"],
                                        descriptionDone=["debuilded", "package"],
                                        env=env,
                                        haltOnFailure=True,
                                        workdir=code_dir))
        factory_deb.addStep(steps.ShellCommand(command=['debsign.sh', project_name + "_deb"],
                                        name='debsign for ' + ubuntu_distribution,
                                        description=["debsign", "package"],
                                        descriptionDone=["debsigned", "package"],
                                        env=env,
                                        haltOnFailure=True))
        # upload to launchpad
        factory_deb.addStep(steps.ShellCommand(command=['/bin/bash','-c',
                                        'dput ppa:nextgis/ppa ' +  deb_name + '*' + ubuntu_distribution + '1_source.changes'],
                                        name='dput for ' + ubuntu_distribution,
                                        description=["dput", "package"],
                                        descriptionDone=["dputed", "package"],
                                        env=env,
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
                                 env=env,
                                 haltOnFailure=True))

    builder_deb = util.BuilderConfig(name = project_name + '_deb',
        workernames = ['build-nix'],
        factory = factory_deb,
        description =  "Make NextGIS Ubuntu ppa package")

    c['builders'].append(builder_deb)

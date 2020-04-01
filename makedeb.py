# -*- python -*-
# ex: set syntax=python:
# production builds into nextgis ppa

from buildbot.plugins import *
import os

c = {}

repositories = [
    {'repo':'lib_geos', 'deb':'geos', 'subdir': '', 'org':'nextgis-borsch', 'os': ['xenial', 'bionic', 'stretch', 'buster'], 'repo_id': 11},
    # {'repo':'lib_gdal', 'version':'2.4.0', 'deb':'gdal', 'subdir': 'master', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'lib_qscintilla', 'version':'2.10.4', 'deb':'qscintilla', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'py_future', 'version':'0.17.1', 'deb':'python-future', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/90/52/e20466b85000a181e1e144fd8305caf2cf475e2f9674e797b222f8105f5f/future-0.17.1.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'py_raven', 'version':'6.10.0', 'deb':'python-raven', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/79/57/b74a86d74f96b224a477316d418389af9738ba7a63c829477e7a86dd6f47/raven-6.10.0.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'py_setuptools', 'version':'40.6.3', 'deb':'python-setuptools', 'subdir': '', 'org':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/setuptools-40.6.3.zip', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'lib_opencad','version':'0.3.4', 'deb':'opencad', 'subdir': 'master', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'lib_oci','version':'12.2.0.1', 'deb':'oci', 'subdir': '', 'org':'nextgis-borsch', 'url': 'http://dev.nextgis.com/third-party/oci/current/lin/lib.tar.gz', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'postgis','version':'2.4.4', 'deb':'postgis', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'nextgisutilities','version':'0.1.0', 'deb':'nextgisutilities', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'dante','version':'1.4.2', 'deb':'dante', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'pam-pgsql','version':'0.7.3.3', 'deb':'pam-pgsql', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'nextgisqgis','version':'19.1.0', 'deb':'nextgisqgis', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'lib_ngstd','version':'0.11.0', 'deb':'ngstd', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'formbuilder','version':'3.0', 'deb':'formbuilder', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['bionic']},
    # {'repo':'protobuf-c','version':'1.3.0', 'deb':'protobuf-c', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'protobuf','version':'3.5.1', 'deb':'protobuf', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'mapserver','version':'7.2.1', 'deb':'mapserver', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'xenial', 'bionic']},
    # {'repo':'manuscript','version':'0.1.0', 'deb':'manuscript', 'subdir': '', 'org':'nextgis', 'url': '', 'ubuntu_distributions': ['bionic']},
    # {'repo':'osrm-backend','version':'0.1', 'deb':'osrm-backend', 'subdir': '', 'org':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['bionic']},
]

c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

platforms = [
    {'name' : 'bionic', 'worker' : 'deb-build-bionic'},
    {'name' : 'xenial', 'worker' : 'deb-build-xenial'},
    {'name' : 'trusty', 'worker' : 'deb-build-trusty'},
    {'name' : 'stretch', 'worker' : 'deb-build-stretch'},
    {'name' : 'buster', 'worker' : 'deb-build-buster'},
    {'name' : 'sid', 'worker' : 'deb-build-sid'},
]

build_lock = util.MasterLock("deb_worker_builds")

script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/deb_util.py'
script_name = 'deb_util.py'
logfile = 'stdio'
username = 'buildbot'
userkey = os.environ.get("BUILDBOT_PASSWORD")

# Create builders
for repository in repositories:

    project_name = repository['repo']
    org = repository['org']
    repourl = 'git://github.com/{}/{}.git'.format(org, project_name)
    git_project_name = '{}/{}'.format(org, project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                           workdir = project_name + '-workdir',
                           branches = ['master'],
                           pollinterval = 5400,)
    c['change_source'].append(git_poller)

    builderNames = []
    for platform in platforms:
        if platform['name'] not in repository['os']:
            continue
        builderNames.append(project_name + "_" + platform['name'])

    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name + "_deb",
                                change_filter=util.ChangeFilter(project = git_project_name, branch="master"),
                                treeStableTimer=1*60,
                                builderNames=builderNames,)
    c['schedulers'].append(scheduler)

    c['schedulers'].append(schedulers.ForceScheduler(
                                name=project_name + "_force_deb",
                                builderNames=builderNames,))

    deb_name = repository['deb']

    root_dir = 'build'
    code_dir_last = deb_name + '_code'
    code_dir = root_dir + '/' + code_dir_last

    ## release build ###############################################################
    factory = util.BuildFactory()

    for platform in platforms:
        if platform['name'] not in repository['os']:
            continue

        # 1. checkout the source
        factory.addStep(steps.Git(repourl=repourl,
            mode='full', shallow=True, submodules=False, 
            workdir=code_dir))
        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=["curl", script_src, '-o', script_name, '-s', '-L'], 
                logfile=logfile),
            ],
            name="Download scripts",
            haltOnFailure=True,
            workdir=root_dir))

        # 2. Make configure to generate version.str 
        ver_dir = root_dir + '/ver'
        factory.addStep(steps.MakeDirectory(dir=ver_dir, name="Make ver directory"))
        factory.addStep(steps.ShellCommand(command=["cmake", '../' + code_dir_last],
            name="Make configure to generate version.str",
            haltOnFailure=True, timeout=125 * 60, maxTime=5 * 60 * 60,
            workdir=ver_dir))

        # 3. Create debian folder
        factory.addStep(steps.ShellCommand(command=['python', script_name, '-op', 'create_debian', '-vf', 'ver/version.str', 
                '-rp', code_dir_last, '-dp', '.', '-pn', deb_name, '--repo_id', repository['repo_id'], '--login', username, 
                '--password', userkey
            ],
            name="Create debian folder", haltOnFailure=True, timeout=125 * 60,
            maxTime=5 * 60 * 60, workdir=root_dir))

        # 4. Create packages
        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=['mk-build-deps', '--install', 
                    '--tool=\'apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes\'', 'debian/control'], 
                    logfile=logfile),
                util.ShellArg(command=["dpkg-buildpackage", '-b', '-us', '-uc'], 
                    logfile=logfile),
            ],
            name="Create packages", haltOnFailure=True, timeout=125 * 60,
            maxTime=5 * 60 * 60, workdir=code_dir
            ))

        # 5. Upload to repka
        factory.addStep(steps.ShellCommand(command=['python', script_name, '-op', 'make_release', '-vf', 'ver/version.str', 
                '-rp', code_dir_last, '-dp', '.', '-pn', deb_name, '--repo_id', repository['repo_id'], '--login', username, 
                '--password', userkey
            ],
            name="Upload to repka", haltOnFailure=True, timeout=125 * 60,
            maxTime=5 * 60 * 60, workdir=root_dir))
        
        builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
            workernames = [platform['worker']],
            factory = factory,
            locks = [build_lock.access('exclusive')], # counting
            description="Make {} on {}".format(project_name, platform['name']),)

        c['builders'].append(builder)

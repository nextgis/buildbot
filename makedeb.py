# -*- python -*-
# ex: set syntax=python:
# production builds into nextgis ppa

import os

from buildbot.plugins import changes, schedulers, steps, util

from nextgis_utils import create_tags

c = {}

# fmt: off
repositories = [
    {'repo':'lib_geos', 'deb':'geos', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bionic', 'bullseye', 'focal', 'jammy', 'astra', ], 'repo_id':11},
    {'repo':'lib_proj', 'deb':'proj', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bionic', 'bullseye', 'focal', 'jammy', 'astra', ], 'repo_id':11},
    {'repo':'lib_geotiff', 'deb':'libgeotiff', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bullseye', 'focal', 'jammy', 'astra', ], 'repo_id':11},
    {'repo':'lib_opencad', 'deb':'opencad', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bionic', 'bullseye', 'focal', 'jammy', 'astra', ], 'repo_id':11},
    {'repo':'lib_oci', 'deb':'oci', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bionic', 'bullseye', 'focal', 'jammy', 'astra',], 'repo_id':11},
    {'repo':'lib_gdal', 'deb':'gdal', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bullseye', 'focal', 'jammy', 'astra',], 'repo_id':11},
    {'repo':'lib_spatialite', 'deb':'spatialite', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bullseye', 'focal', 'jammy', 'astra', ], 'repo_id':11},
    {'repo':'mapserver', 'deb':'mapserver', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['bionic', 'bullseye', 'focal', 'jammy', ], 'repo_id':11},
    {'repo':'nextgisutilities', 'deb':'nextgisutilities', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal','bullseye', 'jammy',], 'repo_id':12, 'apt_repos':[{
            'repka_id':11,
            'type':'repka',
        },]
    },
    {'repo':'postgis', 'deb':'postgis', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os': ['focal', 'bullseye', 'jammy',], 'repo_id':11, 'apt_repos':[{
            'deb':'deb http://apt.postgresql.org/pub/repos/apt/ {}-pgdg main',
            'key':'B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8',
            'keyserver':'keyserver.ubuntu.com',
            'type':'deb',
        },]
    },
    {'repo':'lib_ngstd', 'deb':'ngstd', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal', 'jammy', 'astra',], 'repo_id':11},
    {'repo':'formbuilder', 'deb':'formbuilder', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal', 'jammy',], 'repo_id':11},
    # {'repo':'manuscript', 'deb':'manuscript', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal', 'jammy', ], 'repo_id':11},
    {'repo':'mapnik-german-l10n', 'deb':'osml10n', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal','bullseye', 'jammy',], 'repo_id':11, 'apt_repos':[{
            'deb':'deb http://apt.postgresql.org/pub/repos/apt/ {}-pgdg main',
            'key':'B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8',
            'keyserver':'keyserver.ubuntu.com',
            'type':'deb',
        },]
    },
    {'repo':'nextgisqgis', 'deb':'nextgisqgis', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal', 'jammy', 'astra',], 'repo_id':11, 'branch': 'master'},
    {'repo':'qgis_headless', 'deb':'qgis-headless', 'repo_root':'https://github.com', 'org': 'nextgis', 'os': ['focal', 'bullseye', 'jammy',], 'repo_id':11, 'branch': 'master'},
    {'repo':'terratile', 'deb':'python-terratile', 'repo_root':'https://github.com', 'org': 'nextgis', 'os':['focal', 'bullseye', 'jammy'], 'repo_id':11, 'branch': 'gdal3'},
    {'repo':'lib_sentrynative', 'deb':'sentry-native', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['focal', 'bullseye', 'jammy', 'astra',], 'repo_id':11, 'branch': 'master'},
    {'repo':'lib_jsonc', 'deb':'jsonc', 'repo_root':'https://github.com', 'org': 'nextgis-borsch', 'os':['focal', 'bullseye', 'jammy', 'astra',], 'repo_id':11, 'branch': 'master'},
    # {'repo':'lib_qscintilla', 'version':'2.10.4', 'deb':'qscintilla', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'py_future', 'version':'0.17.1', 'deb':'python-future', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/90/52/e20466b85000a181e1e144fd8305caf2cf475e2f9674e797b222f8105f5f/future-0.17.1.tar.gz', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'py_raven', 'version':'6.10.0', 'deb':'python-raven', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/79/57/b74a86d74f96b224a477316d418389af9738ba7a63c829477e7a86dd6f47/raven-6.10.0.tar.gz', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'py_setuptools', 'version':'40.6.3', 'deb':'python-setuptools', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': 'https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/setuptools-40.6.3.zip', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'dante','version':'1.4.2', 'deb':'dante', 'subdir': '', 'repo_root':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'pam-pgsql','version':'0.7.3.3', 'deb':'pam-pgsql', 'subdir': '', 'repo_root':'nextgis', 'url': '', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'protobuf-c','version':'1.3.0', 'deb':'protobuf-c', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'protobuf','version':'3.5.1', 'deb':'protobuf', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['trusty', 'focal', 'bionic']},
    # {'repo':'osrm-backend','version':'0.1', 'deb':'osrm-backend', 'subdir': '', 'repo_root':'nextgis-borsch', 'url': '', 'ubuntu_distributions': ['bionic']},
]
# fmt: on

c["change_source"] = []
c["schedulers"] = []
c["builders"] = []

platforms = [
    {"name": "focal", "worker": "deb-build-focal"},
    # {'name' : 'bionic', 'worker' : 'deb-build-bionic'},
    # {'name' : 'xenial', 'worker' : 'deb-build-xenial'},
    # {'name' : 'trusty', 'worker' : 'deb-build-trusty'},
    # {'name' : 'stretch', 'worker' : 'deb-build-stretch'},
    # {'name' : 'buster', 'worker' : 'deb-build-buster'},
    {"name": "bullseye", "worker": "deb-build-bullseye"},
    # {'name' : 'sid', 'worker' : 'deb-build-sid'},
    {"name": "jammy", "worker": "deb-build-jammy"},
    {"name": "astra", "worker": "deb-build-astra"},
]

build_lock = util.MasterLock("deb_worker_builds")

script_src = (
    "https://raw.githubusercontent.com/nextgis/buildbot/master/worker/deb_util.py"
)
script_name = "deb_util.py"
logname = "stdio"
username = "buildbot"
userkey = os.environ.get("BUILDBOT_PASSWORD")

root_dir = "build"
ver_dir = root_dir + "/ver"


def get_env(os):
    env = {
        "BUILDBOT_USERPWD": "{}:{}".format(username, userkey),
    }
    return env


# Create builders
for repository in repositories:
    project_name = repository["repo"]
    org = repository["org"]
    repourl = "{}/{}/{}.git".format(repository["repo_root"], org, project_name)
    branch = "master"
    if "branch" in repository:
        branch = repository["branch"]
    git_project_name = "{}/{}".format(org, project_name)
    git_poller = changes.GitPoller(
        project=git_project_name,
        repourl=repourl,
        #    workdir = project_name + '-workdir',
        branches=[branch],
        pollinterval=5400,
    )
    c["change_source"].append(git_poller)

    builderNames = []
    for platform in platforms:
        if platform["name"] in repository["os"]:
            builderNames.append(project_name + "_" + platform["name"])

    scheduler = schedulers.SingleBranchScheduler(
        name=project_name + "_deb",
        change_filter=util.ChangeFilter(project=git_project_name, branch=branch),
        treeStableTimer=1 * 60,
        builderNames=builderNames,
    )
    c["schedulers"].append(scheduler)

    c["schedulers"].append(
        schedulers.ForceScheduler(
            name=project_name + "_force_deb",
            builderNames=builderNames,
        )
    )

    deb_name = repository["deb"]
    code_dir_last = deb_name + "_code"
    code_dir = root_dir + "/" + code_dir_last

    for platform in platforms:
        if platform["name"] not in repository["os"]:
            continue

        factory = util.BuildFactory()
        # 1. checkout the source
        factory.addStep(
            steps.Git(
                repourl=repourl,
                mode="full",
                shallow=True,
                submodules=True,
                workdir=code_dir,
            )
        )
        factory.addStep(
            steps.ShellSequence(
                commands=[
                    util.ShellArg(
                        command=["curl", script_src, "-o", script_name, "-s", "-L"],
                        logname=logname,
                    ),
                ],
                name="Download scripts",
                haltOnFailure=True,
                workdir=root_dir,
            )
        )

        factory.addStep(
            steps.ShellCommand(
                command=[
                    "python",
                    script_name,
                    "-op",
                    "add_repka_repo",
                    "--repo_id",
                    repository["repo_id"],
                    "--login",
                    username,
                    "--password",
                    userkey,
                ],
                name="Add apt repository",
                haltOnFailure=True,
                workdir=root_dir,
            )
        )
        if "apt_repos" in repository:
            for apt_repo_info in repository["apt_repos"]:
                if apt_repo_info["type"] == "repka":
                    factory.addStep(
                        steps.ShellCommand(
                            command=[
                                "python",
                                script_name,
                                "-op",
                                "add_repka_repo",
                                "--repo_id",
                                apt_repo_info["repka_id"],
                                "--login",
                                username,
                                "--password",
                                userkey,
                            ],
                            name="Add additional repka apt repository",
                            haltOnFailure=True,
                            workdir=root_dir,
                        )
                    )
                elif apt_repo_info["type"] == "deb":
                    factory.addStep(
                        steps.ShellCommand(
                            command=[
                                "python",
                                script_name,
                                "-op",
                                "add_deb_repo",
                                "--deb",
                                apt_repo_info["deb"].format(platform["name"]),
                                "--deb_key",
                                apt_repo_info["key"],
                                "--deb_keyserver",
                                apt_repo_info["keyserver"],
                            ],
                            name="Add additional deb apt repository",
                            haltOnFailure=True,
                            workdir=root_dir,
                        )
                    )

        factory.addStep(
            steps.ShellCommand(
                command=["apt-get", "-y", "upgrade"],
                env={"DEBIAN_FRONTEND": "noninteractive"},
                name="Upgrade packages",
            )
        )

        factory.addStep(
            steps.ShellCommand(
                command=[
                    "python",
                    script_name,
                    "-op",
                    "create_debian",
                    "-vf",
                    "ver/version.str",
                    "-rp",
                    code_dir_last,
                    "-dp",
                    ".",
                    "-pn",
                    deb_name,
                    "--repo_id",
                    repository["repo_id"],
                    "--login",
                    username,
                    "--password",
                    userkey,
                ],
                name="Create debian directory",
                haltOnFailure=True,
                workdir=root_dir,
            )
        )

        factory.addStep(
            steps.ShellCommand(
                command=[
                    "mk-build-deps",
                    "--install",
                    "--tool=apt -o Debug::pkgProblemResolver=yes --no-install-recommends --yes",
                    "debian/control",
                ],
                name="Install dependencies",
                haltOnFailure=True,
                timeout=25 * 60,
                maxTime=2 * 60 * 60,
                workdir=code_dir,
            )
        )

        # 2. Make configure to generate version.str
        factory.addStep(steps.MakeDirectory(dir=ver_dir, name="Make ver directory"))
        factory.addStep(
            steps.ShellCommand(
                command=[
                    "cmake",
                    "-DBUILD_TESTING=OFF",
                    "-DBUILD_NEXTGIS_PACKAGE=ON",
                    "../" + code_dir_last,
                ],
                name="Make configure to generate version.str",
                workdir=ver_dir,
                warnOnFailure=True,
                env=get_env(platform["name"]),
            )
        )

        # 3. Create debian folder
        factory.addStep(
            steps.ShellCommand(
                command=[
                    "python",
                    script_name,
                    "-op",
                    "changelog",
                    "-vf",
                    "ver/version.str",
                    "-rp",
                    code_dir_last,
                    "-dp",
                    ".",
                    "-pn",
                    deb_name,
                    "--repo_id",
                    repository["repo_id"],
                    "--login",
                    username,
                    "--password",
                    userkey,
                ],
                name="Create debian changelog",
                haltOnFailure=True,
                workdir=root_dir,
            )
        )

        # 4. Create packages
        factory.addStep(
            steps.ShellSequence(
                commands=[
                    util.ShellArg(
                        command=[
                            "dpkg-buildpackage",
                            "-b",
                            "-us",
                            "-uc",
                            "--compression=xz",
                        ],
                        logname=logname,
                    ),
                ],
                name="Create packages",
                haltOnFailure=True,
                timeout=125 * 60,
                maxTime=5 * 60 * 60,
                workdir=code_dir,
                env=get_env(platform["name"]),
            )
        )

        # 5. Upload to repka
        factory.addStep(
            steps.ShellCommand(
                command=[
                    "python",
                    script_name,
                    "-op",
                    "make_release",
                    "-vf",
                    "ver/version.str",
                    "-rp",
                    code_dir_last,
                    "-dp",
                    ".",
                    "-pn",
                    deb_name,
                    "--repo_id",
                    repository["repo_id"],
                    "--login",
                    username,
                    "--password",
                    userkey,
                ],
                name="Upload to repka",
                haltOnFailure=True,
                timeout=125 * 60,
                maxTime=5 * 60 * 60,
                workdir=root_dir,
            )
        )

        builder = util.BuilderConfig(
            name=project_name + "_" + platform["name"],
            workernames=[platform["worker"]],
            factory=factory,
            locks=[build_lock.access("exclusive")],  # counting
            description="Make {} on {}".format(project_name, platform["name"]),
            tags=create_tags(["deb", project_name, platform["name"]]),
        )

        c["builders"].append(builder)

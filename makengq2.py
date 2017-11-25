from buildbot.plugins import *
from buildbot.changes.gitpoller import GitPoller
from buildbot.steps.source.git import Git
from buildbot.config import BuilderConfig
import bbconf

c = {}

ngq_repourl = 'https://github.com/nextgis/nextgisqgis.git'
ngq_branch = 'up_to_2.18'
project_name = 'ngq2'

c['change_source'] = []
ngq_git_poller = GitPoller(
    project=project_name,
    repourl=ngq_repourl,
    workdir='%s-workdir' % project_name,
    branch=ngq_branch,
    pollinterval=3600,
)
c['change_source'].append(ngq_git_poller)

c['schedulers'] = []
c['schedulers'].append(
    schedulers.ForceScheduler(
        name="%s_force" % project_name,
        # builderNames=["makengq2_deb", "makengq2_deb_dev"]
        builderNames=["makengq2_deb_dev"]
    )
)

c['builders'] = []

# deb package --------------------------------------------------
deb_repourl = 'git://github.com/nextgis/ppa.git'

factory_deb = util.BuildFactory()
factory_deb_dev = util.BuildFactory()
ubuntu_distributions = ['trusty', 'xenial', 'artful']

deb_name = 'ngqgis'
deb_dir = 'build/ngq_deb'
code_dir_last = deb_name
code_dir = 'build/%s' % code_dir_last

deb_email = 'alexander.lisovenko@nextgis.com'
deb_fullname = 'Alexander Lisovenko'

env_vars = {'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname}

#project_ver = util.Interpolate('16.3.1-%(prop:buildnumber)s')
project_ver = util.Interpolate('17.11.0')

step_ppa_checkout = steps.Git(
    repourl=deb_repourl,
    mode='incremental',
    submodules=False,
    workdir=deb_dir,
    alwaysUseLatest=True
)
factory_deb.addStep(step_ppa_checkout)
factory_deb_dev.addStep(step_ppa_checkout)

step_ngq_checkout = steps.Git(
    repourl=ngq_repourl,
    branch=ngq_branch,
    mode='full',
    submodules=True,
    workdir=code_dir
)
factory_deb.addStep(step_ngq_checkout)
factory_deb_dev.addStep(step_ngq_checkout)

# cleanup
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']
for clean_ext in clean_exts:
    step_clear = steps.ShellCommand(
        command=['/bin/bash', '-c', 'rm *' + clean_ext],
        name="rm of " + clean_ext,
        description=["rm", "delete"],
        descriptionDone=["rm", "deleted"],
        haltOnFailure=False, warnOnWarnings=True,
        flunkOnFailure=False, warnOnFailure=True
    )
    factory_deb.addStep(step_clear)
    factory_deb_dev.addStep(step_clear)


# tar orginal sources
step_tar = steps.ShellCommand(
    command=[
        "dch.py", '-n', project_ver, '-a',
        deb_name, '-p', 'tar', '-f',
        code_dir_last],
    name="tar",
    description=["tar", "compress"],
    descriptionDone=["tar", "compressed"], haltOnFailure=True
)
factory_deb.addStep(step_tar)
factory_deb_dev.addStep(step_tar)

# update changelog
for ubuntu_distribution in ubuntu_distributions:
    # copy ... -> debian
    step_copy_debian = steps.CopyDirectory(
        src=deb_dir + "/ngq/%s/debian" % ubuntu_distribution,
        dest=code_dir + "/debian",
        name="add debian folder",
        haltOnFailure=True
    )
    factory_deb.addStep(step_copy_debian)
    factory_deb_dev.addStep(step_copy_debian)

    step_create_changelog = steps.ShellCommand(
        command=[
            'dch.py', '-n', project_ver, '-a',
            deb_name, '-p', 'fill', '-f',
            code_dir_last, '-o', 'changelog', '-d',
            ubuntu_distribution
        ],
        name='create changelog for ' + ubuntu_distribution,
        description=["create", "changelog"],
        descriptionDone=["created", "changelog"],
        env=env_vars,
        haltOnFailure=True
    )
    factory_deb.addStep(step_create_changelog)
    factory_deb_dev.addStep(step_create_changelog)

    # debuild -us -uc -d -S
    step_debuild = steps.ShellCommand(
        command=['debuild', '-us', '-uc', '-S'],
        name='debuild for ' + ubuntu_distribution,
        description=["debuild", "package"],
        descriptionDone=["debuilded", "package"],
        env=env_vars,
        haltOnFailure=True,
        workdir=code_dir
    )
    factory_deb.addStep(step_debuild)
    factory_deb_dev.addStep(step_debuild)

    factory_deb.addStep(
        steps.ShellCommand(
            command=['debsign.sh', "makengq2_deb"],
            name='debsign for ' + ubuntu_distribution,
            description=["debsign", "package"],
            descriptionDone=["debsigned", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )
    factory_deb_dev.addStep(
        steps.ShellCommand(
            command=['debsign.sh', "makengq2_deb_dev"],
            name='debsign for ' + ubuntu_distribution,
            description=["debsign", "package"],
            descriptionDone=["debsigned", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )

    # upload to launchpad
    factory_deb.addStep(
        steps.ShellCommand(
            command=[
                '/bin/bash', '-c',
                'dput ppa:nextgis/dev ' + deb_name + '*' + ubuntu_distribution + '1_source.changes'
            ],
            name='dput for ' + ubuntu_distribution,
            description=["dput", "package"],
            descriptionDone=["dputed", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )
    factory_deb_dev.addStep(
        steps.ShellCommand(
            command=[
                '/bin/bash', '-c',
                'dput ppa:nextgis/dev ' + deb_name + '*' + ubuntu_distribution + '1_source.changes'
            ],
            name='dput for ' + ubuntu_distribution,
            description=["dput", "package"],
            descriptionDone=["dputed", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )

    # delete code_dir + "/debian"
    step_clean_debian = steps.RemoveDirectory(
        dir=code_dir + "/debian",
        name="remove debian folder for " + ubuntu_distribution,
        haltOnFailure=True
    )
    factory_deb.addStep(step_clean_debian)
    factory_deb_dev.addStep(step_clean_debian)

# store changelog
step_store_changelog = steps.ShellCommand(
    command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last, '-o', 'changelog'],
    name='log last comments',
    description=["log", "last comments"],
    descriptionDone=["logged", "last comments"],
    env=env_vars,
    haltOnFailure=True
)
factory_deb.addStep(step_store_changelog)
factory_deb_dev.addStep(step_store_changelog)

ngq_deb_release_builder = BuilderConfig(
    name='makengq2_deb',
    slavenames=['build-nix'],
    factory=factory_deb
)
ngq_deb_dev_builder = BuilderConfig(
    name='makengq2_deb_dev',
    slavenames=['build-nix'],
    factory=factory_deb_dev
)

# c['builders'].append(ngq_deb_release_builder)
c['builders'].append(ngq_deb_dev_builder)

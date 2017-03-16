# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

c = {}

# SOURCES
repourl = 'git@github.com:nextgis/nextgisid.git'

project_name = 'nextgisid'
git_project_name = 'nextgis/nextgisid'

git_poller = GitPoller(project=git_project_name,
                       repourl=repourl,
                       workdir=project_name + '-workdir',
                       branch='master',
                       pollinterval=3600, )
c['change_source'] = [git_poller]

# SCHEDULERS
scheduler = schedulers.SingleBranchScheduler(
    name=project_name,
    change_filter=util.ChangeFilter(project=git_project_name),
    treeStableTimer=5 * 60,
    builderNames=[project_name])

force_scheduler = schedulers.ForceScheduler(
    name=project_name + "_force",
    builderNames=[project_name],
)

c['schedulers'] = [scheduler, force_scheduler]

# BUILD FACTORY
factory = util.BuildFactory()

factory.addStep(steps.Git(name='Get source code',
                          description=['Get source code'],
                          descriptionDone=['Get source code'],
                          workdir='build/src',
                          repourl=repourl,
                          mode='incremental',
                          submodules=True)
                )

factory.addStep(steps.ShellCommand(name='Create virtual environment',
                                   description=['Create virtual environment'],
                                   descriptionDone=['Create virtual environment'],
                                   workdir='build',
                                   command=['virtualenv', 'env'])
                )

factory.addStep(steps.ShellCommand(name='Install common requirements',
                                   description=['Install common requirements'],
                                   descriptionDone=['Install common requirements'],
                                   workdir='build',
                                   command=['env/bin/pip', 'install', '-r', 'src/requirements.txt'])
                )

factory.addStep(steps.ShellCommand(name='Install tests requirements',
                                   description=['Install tests requirements'],
                                   descriptionDone=['Install tests requirements'],
                                   workdir='build',
                                   command=['env/bin/pip', 'install', '-r', 'src/requirements-tests.txt'])
                )

factory.addStep(steps.ShellCommand(name='Create tests subconfig',
                                   description=['Create tests subconfig'],
                                   descriptionDone=['Create tests subconfig'],
                                   workdir='build',
                                   command=['cp', 'src/nextgisid_site/nextgisid_site/settings_local.py_server_tests_template', 'src/nextgisid_site/nextgisid_site/settings_local.py'])
                )

factory.addStep(steps.ShellCommand(name='Run behave tests',
                                   description=['Run behave tests'],
                                   descriptionDone=['Run behave tests'],
                                   workdir='build/src/nextgisid_site/',
                                   command=['../../env/bin/python', 'manage.py', 'behave'],
                                   timeout=1200,
                                   env={'LANG': 'en_US.UTF-8'})
                )

# BUILDER
ngid_builder = util.BuilderConfig(name=project_name, slavenames=['build-nix'], factory=factory)
c['builders'] = [ngid_builder]

# NOTIFIER
import bbconf

ngid_mn = reporters.MailNotifier(fromaddr='buildbot@nextgis.com',
                       sendToInterestedUsers=True,
                       builders=[ngid_builder.name],
                       mode=('all'),
                       extraRecipients=bbconf.ngid_email_recipients,
                       relayhost='192.168.255.1',
                       useTls=True
                      )

c['status'] = [ngid_mn]

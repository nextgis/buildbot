# -*- python -*-
# ex: set syntax=python:
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import *
from buildbot.status.mail import MailNotifier

c = {}

# SOURCES
repourl = 'git@github.com:nextgis/nextgisid.git'

git_poller = GitPoller(project='make_ngid_tests',
                       repourl=repourl,
                       workdir='ngid_tests',
                       branch='master',
                       pollinterval=3600, )
c['change_source'] = [git_poller]

# SCHEDULERS
scheduler = schedulers.SingleBranchScheduler(
    name="make_ngid_tests",
    change_filter=util.ChangeFilter(project='make_ngid_tests'),
    treeStableTimer=5 * 60,
    builderNames=["make_ngid_tests_builder"])

force_scheduler = schedulers.ForceScheduler(
    name="make_ngid_tests_force",
    builderNames=["make_ngid_tests_builder"],
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
ngid_builder = BuilderConfig(name='make_ngid_tests_builder', slavenames=['build-nix'], factory=factory)
c['builders'] = [ngid_builder]

# NOTIFIER
import bbconf

ngid_mn = MailNotifier(fromaddr='buildbot@nextgis.ru',
                       sendToInterestedUsers=True,
                       builders=[ngid_builder.name],
                       mode=('all'),
                       extraRecipients=bbconf.ngid_email_recipients,
                       relayhost='mail.gis-lab.info',
                       useTls=False,
                       smtpPort=2525,
                       smtpUser=bbconf.email_user,
                       smtpPassword=bbconf.email_passwd)

c['status'] = [ngid_mn]

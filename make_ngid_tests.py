# -*- python -*-
# ex: set syntax=python:
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import *

from buildbot.process.buildstep import LoggingBuildStep
from buildbot.status.results import SUCCESS

# CUSTOM BuildSteps (BAD - need tto move to separate file)


class CreateSubConfig(LoggingBuildStep):
    name = "create_sub_config"

    config_text = """
TEST_ENV = True

if TEST_ENV:
    from settings import INSTALLED_APPS
    import os
    DJANGO_LIVE_TEST_SERVER_ADDRESS = 'localhost:9200-9300'
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = DJANGO_LIVE_TEST_SERVER_ADDRESS
    TESTS_BROWSER_DRIVER_NAME = 'phantomjs'  # use acceptable drivers for Splinter
    INSTALLED_APPS += ('behave_django',)
    """

    def __init__(self,  out_file_path, **kwargs):

        self.out_file_path = out_file_path
        # call parent
        LoggingBuildStep.__init__(self, **kwargs)

    def start(self):
        # try:
        #
        # except Exception as ex:
        #     self.finished()
        with open(self.out_file_path, mode='w', encoding='utf8') as out_file:
            out_file.write(self.config_text)
        self.finished(SUCCESS)


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
                          workdir='build/src',
                          repourl=repourl,
                          mode='incremental',
                          submodules=True)
                )

factory.addStep(steps.ShellCommand(name='Create virtual environment',
                                   workdir='build',
                                   command=['virtualenv', 'env'])
                )

factory.addStep(steps.ShellCommand(name='Install common requirements',
                                   workdir='build',
                                   command=['env/bin/pip', 'install', '-r', 'src/requirements.txt'])
                )

factory.addStep(steps.ShellCommand(name='Install tests requirements',
                                   workdir='build',
                                   command=['env/bin/pip', 'install', '-r', 'src/requirements-tests.txt'])
                )

factory.addStep(CreateSubConfig('src/nextgisid_site/nextgisid_site/settings_local.py',
                                name='Create test subconfig',
                                #workdir='build'
                                )
                )

factory.addStep(steps.ShellCommand(name='Run behave tests',
                                   workdir='build',
                                   command=['env/bin/python', 'src/nextgisid_site/manage.py', 'behave'])
                )

# BUILDER
builder = BuilderConfig(name='make_ngid_tests_builder', slavenames=['build-nix'], factory=factory)
c['builders'] = [builder]

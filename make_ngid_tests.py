# -*- python -*-
# ex: set syntax=python:
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import *

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
# 1. check out the source
factory.addStep(steps.Git(name='Get source code',
                          workdir='src',
                          repourl=repourl,
                          mode='incremental',
                          submodules=True)
                )

# 2. Create virt env
factory.addStep(steps.ShellCommand(name='Create virtual environment',
                                   workdir='',
                                   command=['virtualenv', 'env'])
                )

#3. Install requrements
factory.addStep(steps.ShellCommand(name='Install common requirements',
                                   workdir='',
                                   command=['env/bin/pip', 'install', '-r', 'src/requirements.txt'])
                )

# BUILDER
builder = BuilderConfig(name='make_ngid_tests_builder', slavenames=['build-nix'], factory=factory)
c['builders'] = [builder]

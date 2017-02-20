# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
from buildbot.steps.source.git import Git
from buildbot.steps.python import Sphinx
from buildbot.steps.transfer import DirectoryUpload
from buildbot.changes.gitpoller import GitPoller
from buildbot.schedulers.basic  import SingleBranchScheduler
from buildbot.config import BuilderConfig
from buildbot.steps.master import MasterShellCommand

import bbconf

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

# 'git://github.com/nextgis/docs_howto.git',
repos = [
    'docs_howto',
    'docs_ngcom',
    'docs_ngmobile',
    'docs_ngqgis',
    'docs_ngweb'
]

main_repourl = 'git://github.com/nextgis/docs_ng.git'

langs = ['ru', 'en']

poller_name = 'updatedocs'

for repo in repos:
    git_poller = GitPoller(project = poller_name + '_' + repo,
                       repourl = 'git://github.com/nextgis/' + repo + '.git',
                       workdir = poller_name + '-' + repo + '-workdir',
                       branches = langs,
                       pollinterval = 900,)
    c['change_source'].append(git_poller)

project_name = 'updatedocs'

for lang in langs:
    scheduler = schedulers.SingleBranchScheduler(
                        name=project_name + '_' + lang,
                        change_filter=util.ChangeFilter(project_re = poller_name + '_*',
                                                        branch=lang),
                        treeStableTimer=2*60,
                        builderNames=[project_name])
    c['schedulers'].append(scheduler)
# c['schedulers'].append(schedulers.ForceScheduler(
#                             name=project_name + "_force",
#                             builderNames=[project_name],
# ))

#### update docs

factory = util.BuildFactory()

factory.addStep(steps.Git(repourl=main_repourl, mode='incremental', submodules=True))
factory.addStep(steps.ShellCommand(command=["git", "config", "user.name", bbconf.git_user_name],
                                  description=["set", "git config username"],
                                  descriptionDone=["set", "git config username"],
                                  workdir="build"))
factory.addStep(steps.ShellCommand(command=["git", "config", "user.email", bbconf.git_user_email],
                                  description=["set", "git config useremail"],
                                  descriptionDone=["set", "git config useremail"],
                                  workdir="build"))

factory.addStep(steps.ShellCommand(command=["git", "submodule", "foreach", "git", "checkout", "master"],
                                  description=["git", "submodule foreach git checkout master"],
                                  workdir="build"))

factory.addStep(steps.ShellCommand(command=["git", "checkout", "3"],
                                  description=["git", "checkout 3"],
                                  workdir="build/source/docs_ngweb_dev"))
for lang in langs:
    factory.addStep(steps.ShellCommand(command=["sh", "switch_lang.sh", lang],
                                      description=["switch", "language to " + lang],
                                      descriptionDone=["switched", "language to " + lang],
                                      workdir="build"))
    factory.addStep(steps.ShellCommand(command=["sh", "update_docs.sh"],
                                      description=["update", lang + " documentation"],
                                      descriptionDone=["updated", lang + " documentation"],
                                      workdir="build"))

builder = BuilderConfig(name = project_name, slavenames = ['build-nix'], factory = factory)
c['builders'].append(builder)

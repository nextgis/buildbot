# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repos = [
    'docs_ngcom',
    'docs_ngmobile',
    'docs_ngqgis',
    'docs_ngweb',
    'docs_toolbox',
]

repos_m = [
    'docs_howto',
]

repourl = 'git@github.com:nextgis/docs_ng.git'

langs = ['ru', 'en']

poller_name = 'updatedocs'

for repo in repos:
    git_poller = changes.GitPoller(project = poller_name + '/' + repo,
                       repourl = 'git://github.com/nextgis/' + repo + '.git',
                       workdir = poller_name + '-' + repo + '-workdir',
                       branches = langs,
                       pollinterval = 900,)
    c['change_source'].append(git_poller)

for repo in repos_m:
    git_poller = changes.GitPoller(project = poller_name + '/' + repo,
                       repourl = 'git://github.com/nextgis/' + repo + '.git',
                       workdir = poller_name + '-' + repo + '-workdir',
                       branches = ['master'],
                       pollinterval = 900,)
    c['change_source'].append(git_poller)


project_name = 'updatedocs'

# RU, EN
for lang in langs:
    scheduler = schedulers.SingleBranchScheduler(
                        name=project_name + '_' + lang,
                        change_filter=util.ChangeFilter(project_re = poller_name + '/*',
                                                        branch=lang),
                        treeStableTimer=2*60,
                        builderNames=[project_name])
    c['schedulers'].append(scheduler)

# Master
scheduler = schedulers.SingleBranchScheduler(
                    name=project_name + '_master',
                    change_filter=util.ChangeFilter(project_re = poller_name + '/*',
                                                    branch='master'),
                    treeStableTimer=2*60,
                    builderNames=[project_name])

c['schedulers'].append(scheduler)
c['schedulers'].append(schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[project_name],
))

#### update docs
git_user_name = "NextGIS BuildBot"
git_user_email = "buildbot@nextgis.com"
logfile = 'stdio'

factory = util.BuildFactory()
factory.addStep(steps.Git(repourl=repourl, mode='full', method='clobber', submodules=True))
factory.addStep(steps.ShellSequence(commands=[
        util.ShellArg(command=["git", "config", "user.name", git_user_name], logfile=logfile),
        util.ShellArg(command=["git", "config", "user.email", git_user_email], logfile=logfile),
    ],
    name="Set git config defaults",
    haltOnFailure=True,
    workdir="build",))

for lang in langs:
    factory.addStep(steps.ShellCommand(command=["sh", "switch_lang.sh", lang],
                                      description=["switch", "language to " + lang],
                                      descriptionDone=["switched", "language to " + lang],
                                      workdir="build"))
    # TODO: github script push
    factory.addStep(steps.ShellCommand(command=["sh", "update_docs.sh"],
                                      description=["update", lang + " documentation"],
                                      descriptionDone=["updated", lang + " documentation"],
                                      workdir="build"))

builder = util.BuilderConfig(name=project_name, workernames=['build-light'], factory=factory)
c['builders'].append(builder)

# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repos = [
    {'repo':'docs_ngcom', 'langs': ['ru', 'en']},
    {'repo':'docs_ngmobile', 'langs': ['ru', 'en']},
    {'repo':'docs_ngqgis', 'langs': ['ru', 'en']},
    {'repo':'docs_ngweb', 'langs': ['ru', 'en']},
    {'repo':'docs_toolbox', 'langs': ['ru', 'en']},
    {'repo':'docs_data', 'langs': ['ru', 'en']},
    {'repo':'docs_collector', 'langs': ['ru', 'en']},
    {'repo':'docs_ngid', 'langs': ['ru', 'en']},
    {'repo':'docs_formbuilder', 'langs': ['ru', 'en']},
    {'repo':'docs_ngcourses', 'langs': ['ru', 'en']},
    {'repo':'docs_howto', 'langs': ['master']},
]

base_repourl = 'https://github.com/nextgis/'
repourl = base_repourl + 'docs_ng.git'
poller_name = 'updatedocs'

for repo in repos:
    git_poller = changes.GitPoller(project = poller_name + '/' + repo['repo'],
                       repourl = base_repourl + repo['repo'] + '.git',
                    #    workdir = poller_name + '-' + repo['repo'] + '-workdir',
                       branches = repo['langs'],
                       pollinterval = 1 * 60 * 60,) # Poll hourly
    c['change_source'].append(git_poller)

project_name = 'updatedocs'

langs = ['ru', 'en']

# scheduler = schedulers.AnyBranchScheduler(
#                         name=project_name,
#                         change_filter=util.ChangeFilter(project_re = poller_name + '/*'),
#                         treeStableTimer=2*60,
#                         builderNames=[project_name])
# c['schedulers'].append(scheduler)

branches = langs + ['master']
for lang in branches:
    scheduler = schedulers.SingleBranchScheduler(
                        name=project_name + '_' + lang,
                        change_filter=util.ChangeFilter(project_re = poller_name + '/*',
                                                        branch=lang),
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
logname = 'stdio'

factory = util.BuildFactory()
factory.addStep(steps.Git(repourl=repourl, mode='full', method='clobber', submodules=True))
factory.addStep(steps.ShellSequence(commands=[
        util.ShellArg(command=["git", "config", "--global", "user.name", git_user_name], logname=logname),
        util.ShellArg(command=["git", "config", "--global", "user.email", git_user_email], logname=logname),
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

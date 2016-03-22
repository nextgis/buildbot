# -*- python -*-
# ex: set syntax=python:
from buildbot.changes.gitpoller import GitPoller
from buildbot.config import BuilderConfig
from buildbot.plugins import *

c = {}

repourl = 'git@github.com:nextgis/nextgisid.git'

git_poller = GitPoller(project='make_ngid_tests',
                       repourl=repourl,
                       workdir='ngid_tests',
                       branch='master',
                       pollinterval=3600, )
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
    name="make_ngid_tests",
    change_filter=util.ChangeFilter(project='make_ngid_tests'),
    treeStableTimer=5 * 60,
    builderNames=["make_ngid_tests_builder"])

c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
    name="make_ngid_tests_force",
    builderNames=["make_ngid_tests_builder"],
))



factory = util.BuildFactory()
# 1. check out the source
factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True))  # mode='full', method='clobber'

# 2. Create virt env
#factory.addStep(steps.MakeDirectory(dir=''))
factory.addStep(steps.ShellCommand(command=['virtualenv', 'env']))
factory.addStep(steps.ShellCommand(command=['env/bin/pip', 'install', 'splinter']))

# 2. build pdf for each doc except dev
# factory.addStep(steps.  ShellCommand(command=["sh", "make_javadoc.sh"],
#                                    description=["make", "javadoc for mobile (android)"],
#                                    descriptionDone=["made", "javadoc for mobile (android)"],
#                                    workdir="build/source/ngmobile_dev"))
# factory.addStep(steps.ShellCommand(command=["make", "latexpdf"],
#                                    description=["make", "pdf for NextGIS Mobile"],
#                                    workdir="build/source/docs_ngmobile"))
#
# # 3. build html
# factory.addStep(Sphinx(sphinx_builddir="_build/html", sphinx_sourcedir="source", sphinx_builder="html"))
# factory.addStep(DirectoryUpload(slavesrc="_build/html", masterdest="/usr/share/nginx/doc"))
# factory.addStep(MasterShellCommand(name="chmod", description=["fixing", "permissions"],
#                                    descriptionDone=["fix", "permissions"], haltOnFailure=True,
#                                    command=["/bin/bash", "-c", "chmod -R 0755 /usr/share/nginx/doc/*"]))
#
#
# builder = BuilderConfig(name='makedocs', slavenames=['build-nix'], factory=factory)
# c['builders'] = [builder]

builder = BuilderConfig(name='make_ngid_tests_builder', slavenames=['build-nix'], factory=factory)
c['builders'] = [builder]

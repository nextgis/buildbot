# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *
import os

repositories = [
    {'repo':'lib_z', 'args':[], 'os':['jammy-crosscompile'], 'repo_root':'https://github.com', 'org':'nextgis-borsch'},
]

c = {
    'change_source': [],
    'schedulers': [],
    'builders': []
}

platforms = [
    {'name' : 'jammy-crosscompile', 'worker' : 'deb-build-jammy-crosscompile'},
]

build_lock = util.MasterLock("crosscompile_worker_builds")

script_name = 'crosscompile.py'
script_src = 'https://github.com/nextgis-borsch/borsch/raw/master/opt/' + script_name

logname = 'stdio'
username = 'buildbot'
userkey = os.environ.get("BUILDBOT_PASSWORD")

def get_env(os):
    env = {
            'BUILDBOT_USERPWD': '{}:{}'.format(username, userkey),
        }
    return env

# Create builders
for repository in repositories:

    project_name = repository['repo']
    org = repository['org']
    repourl = '{}/{}/{}.git'.format(repository['repo_root'], org, project_name)
    branch = 'master'
    if 'branch' in repository:
        branch = repository['branch']
    git_project_name = '{}/{}'.format(org, project_name)
    git_poller = changes.GitPoller(project = git_project_name,
                           repourl = repourl,
                        #    workdir = project_name + '-workdir',
                           branches = [branch],
                           pollinterval = 5400,)
    c['change_source'].append(git_poller)

    builderNames = []
    for platform in platforms:
        if platform['name'] in repository['os']:
            builderNames.append(project_name + "_" + platform['name'])
    
    scheduler = schedulers.SingleBranchScheduler(
                                name=project_name,
                                change_filter=util.ChangeFilter(project = git_project_name, branch=branch),
                                treeStableTimer=1*60,
                                builderNames=builderNames,)
    c['schedulers'].append(scheduler)
    
    forceScheduler = schedulers.ForceScheduler(
                                name=project_name + "_force",
                                label="Force build",
                                buttonName="Force build",
                                builderNames=builderNames,)
    c['schedulers'].append(forceScheduler)

    root_dir = 'build/'
    repo_name = repository['repo']
    code_dir = root_dir + repo_name + '_code'

    for platform in platforms:
        if platform['name'] not in repository['os']:
            continue

        factory = util.BuildFactory()     
        
        # 1. checkout the source
        factory.addStep(steps.Git(repourl=repourl,
            mode='full', shallow=True, submodules=True, 
            workdir=code_dir))
        
        factory.addStep(steps.ShellSequence(commands=[
                util.ShellArg(command=["curl", script_src, '-o', script_name, '-s', '-L'], 
                logname=logname),
            ],
            name="Download scripts",
            haltOnFailure=True,
            workdir=root_dir))
        
        factory.addStep(steps.ShellCommand(command=["python", script_name, '--packages', repo_name, 
                '--login', username, '--password', userkey
            ],
            name="Crosscompile and send to repka", haltOnFailure=True, workdir=root_dir))
        
        builder = util.BuilderConfig(name = project_name + "_" + platform['name'],
            workernames = [platform['worker']],
            factory = factory,
            locks = [build_lock.access('exclusive')], # counting
            description="Make {} on {}".format(project_name, platform['name']),)

        c['builders'].append(builder)

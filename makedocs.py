# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repourl = 'git://github.com/nextgis/docs_ng.git'
ngw_repo = 'https://github.com/nextgis/nextgisweb.git'
langs = ['ru', 'en']

poller_name = 'docs'
git_project_name = 'nextgis/docs_ng'
git_poller = changes.GitPoller(project = git_project_name,
                   repourl = repourl,
                   workdir = poller_name + '-workdir',
                   branches = langs,
                   pollinterval = 600,)
c['change_source'].append(git_poller)

builderNames = []
logfile = 'stdio'

for lang in langs:
    project_name = poller_name + '_' + lang
    builderNames.append(project_name)

    scheduler = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = git_project_name,
                                                            branch=lang),
                            treeStableTimer=5*60,
                            builderNames=[project_name])
    c['schedulers'].append(scheduler)

    #### build docs

    factory = util.BuildFactory()
    # 1. check out the source
    factory.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=True, clobberOnFailure=True, branch=lang))

    # Check documentation errors
    factory.addStep(steps.ShellSequence(commands=[
            util.ShellArg(command=['make', 'spelling'], logfile=logfile),
            util.ShellArg(command=["cat", 'build/spelling/output.txt'], logfile=logfile),
        ],
        name="Check spelling",
        haltOnFailure=True,
        workdir="build",
        env={
            'LANG': 'ru_RU.UTF-8',
        },
        logEncoding='utf-8',)
    )

    # Install NGW
    factory.addStep(steps.Git(repourl=ngw_repo, mode='incremental', clobberOnFailure=True, branch=lang, workdir="build"))
    factory.addStep(steps.ShellSequence(commands=[
        util.ShellArg(command=['2to3', '--output-dir=nextgisweb3', '-W', '-n', 'nextgisweb',], logfile=logfile),
        util.ShellArg(command=['pip3', 'install', '-e', 'nextgisweb3',], logfile=logfile),
        ],
        name="Install NextGIS Web",
        haltOnFailure=True,
        workdir="build",
        env={
            'LANG': 'ru_RU.UTF-8',
        },
        logEncoding='utf-8',)
    )

    # 2. build pdf for each doc except dev
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS Mobile"],
                                      workdir="build/source/docs_ngmobile"))
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS Web"],
                                      workdir="build/source/docs_ngweb"))
    if lang == 'ru':
        factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS Manager"],
                                      workdir="build/source/docs_ngmanager"))
        factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS FormBuilder"],
                                      workdir="build/source/docs_formbuilder"))
        # Create PDF only on common products
        # factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
        #                               description=["make", "pdf for NextGIS Bio"],
        #                               workdir="build/source/docs_ngbio"))
        factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS QGIS"],
                                      workdir="build/source/docs_ngqgis"))
        # factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
        #                               description=["make", "pdf for NextGIS open geodata portal"],
        #                               workdir="build/source/docs_ogportal"))
        # factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
        #                               description=["make", "pdf for NextGIS forest inspector"],
        #                               workdir="build/source/docs_forestinspector"))

    # Skip javadoc for outdated mobile SDK v2
    # factory.addStep(steps.ShellCommand(command=["sh", "make_javadoc.sh"],
    #                                   description=["make", "javadoc for mobile (android)"],
    #                                   descriptionDone=["made", "javadoc for mobile (android)"],
    #                                   workdir="build/source/ngmobile_dev"))
    factory.addStep(steps.ShellCommand(command=["sh", "make_kotlindoc.sh"],
                                      description=["make", "kotlindoc for mobile (android)"],
                                      descriptionDone=["made", "kotlindoc for mobile (android)"],
                                      workdir="build/source/ngmobile_dev"))

    factory.addStep(steps.ShellCommand(command=["anarchysphinx", "--overwrite", "ios_maplib_src", "ios_maplib"],
                                      description=["make", "swiftdoc for mobile (ios)"],
                                      descriptionDone=["made", "swiftdoc for mobile (ios)"],
                                      workdir="build/source/ngmobile_dev"))

    # 3. build html
    factory.addStep(steps.Sphinx(sphinx_builddir="_build/html", sphinx_sourcedir="source", sphinx_builder="html"))
    # 4. upload to ftp
    # TODO:
    # factory.addStep(steps.ShellCommand(command=["sync.sh", lang],
    #                                    description=["sync", "to web server"]))

    builder = util.BuilderConfig(name = project_name, workernames = ['build-doc'],
                                factory = factory,
                                description='Make documentation [' + lang + ']')
    c['builders'].append(builder)

c['schedulers'].append(schedulers.ForceScheduler(
            name=poller_name + "_force",
            label="Force make",
            buttonName="Force make documentation",
            builderNames=builderNames,
))

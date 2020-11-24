# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repourl = 'git://github.com/nextgis/docs_ng.git'
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
upload_script_name = 'ftp_uploader2.py'
upload_script_src = 'https://raw.githubusercontent.com/nextgis/buildbot/master/worker/' + upload_script_name

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
    factory.addStep(steps.Git(repourl=repourl, mode='full', method='clobber', submodules=True, shallow=True, branch=lang))

    # Check documentation errors
    if lang == 'ru':
        env = {
            'LANG': 'ru_RU.UTF-8',
        }
    else:
        env = {
            'LANG': 'en_US.UTF-8',
        }
    factory.addStep(steps.ShellCommand(command=['make', 'spelling'],
        name="Check spelling",
        haltOnFailure=True,
        workdir="build",
        env=env,
        )
    )

    # 2. build pdf for each doc except dev
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                            name="Generate pdf for NextGIS Mobile",
                            description=["make", "pdf for NextGIS Mobile"],
                            workdir="build/source/docs_ngmobile", warnOnFailure=True, 
                            env=env,))
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                            name="Generate pdf for NextGIS Web",
                            description=["make", "pdf for NextGIS Web"],
                            workdir="build/source/docs_ngweb", warnOnFailure=True,
                            env=env,))
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                            name="Generate pdf for NextGIS FormBuilder",
                            description=["make", "pdf for NextGIS FormBuilder"],
                            workdir="build/source/docs_formbuilder", warnOnFailure=True,
                            env=env,))
    factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                            name="Generate pdf for NextGIS QGIS",
                            description=["make", "pdf for NextGIS QGIS"],
                            workdir="build/source/docs_ngqgis", warnOnFailure=True,
                            env=env,))

    factory.addStep(steps.ShellSequence(commands=[
                    util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s', '-L'], logfile=logfile),
                    util.ShellArg(command=['python', upload_script_name, '--build_path', 'build/json', '--ftp', 'ftp://192.168.255.61/data_docs/' + lang], logfile=logfile),
                ],
                name="Generate json for NextGIS Data",
                description=["make", "json for NextGIS Data"],
                workdir="build/source/docs_data", warnOnFailure=True,
                env=env,))

    if lang == 'ru':
        factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
                                      description=["make", "pdf for NextGIS Manager"],
                                      workdir="build/source/docs_ngmanager", warnOnFailure=True,
                                      env=env,))
        # Create PDF only on common products
        # factory.addStep(steps.ShellCommand(command=['make', 'latexpdf', 'LATEXMKOPTS="--interaction=nonstopmode"'],
        #                               description=["make", "pdf for NextGIS Bio"],
        #                               workdir="build/source/docs_ngbio"))

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
                                      workdir="build/source/ngmobile_dev", warnOnFailure=True,
                                      env=env,))

    factory.addStep(steps.ShellCommand(command=["anarchysphinx", "--overwrite", "ios_maplib_src", "ios_maplib"],
                                      description=["make", "swiftdoc for mobile (ios)"],
                                      workdir="build/source/ngmobile_dev", warnOnFailure=True,
                                      env=env,))

    # 3. build html
    factory.addStep(steps.Sphinx(sphinx_builddir="_build/html", sphinx_sourcedir="source", sphinx_builder="html"))
    # 4. upload to data ftp
    # TODO:
    # factory.addStep(steps.ShellCommand(command=["sync.sh", lang],
    #                                    description=["sync", "to web server"]))
    factory.addStep(steps.ShellSequence(commands=[
        util.ShellArg(command=['cp', 'build/spelling/output.txt', '_build/html/',], logfile=logfile),
        util.ShellArg(command=['chmod', '-R', '0755', '_build/html/',], logfile=logfile),
        util.ShellArg(command=['rsync', '-avz', '-e', 'ssh -p 2322 -i /root/.ssh/www', '_build/html/', 'ngw_admin@192.168.245.227:/home/docker/data/www/docs/' + lang,], logfile=logfile),
        ],
        name="Copy documentation to web server",
        haltOnFailure=True,
        workdir="build",
        )
    )

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

# -*- python -*-
# ex: set syntax=python:

import os
from buildbot.plugins import *

c = {}
c['change_source'] = []
c['schedulers'] = []
c['builders'] = []

repourl = 'https://github.com/nextgis/docs_ng.git'
langs = ['ru', 'en']
ssh_user = os.environ.get("DOCS_UPLOADER", "user")
ssh_port = os.environ.get("DOCS_UPLOAD_SERVER_PORT", "11425")
ftp_address = os.environ.get("FTP_DOCS_ADDRESS", "192.168.6.12")
ftp_port = os.environ.get("FTP_DOCS_PORT", "10511")
ftp_user = os.environ.get("FTP_DOCS_USER", "ngid_ftp_admin")
ftp_password = os.environ.get("FTP_DOCS_PASSWORD", "efolsec190")

poller_name = 'docs'
git_project_name = 'nextgis/docs_ng'
git_poller = changes.GitPoller(project = git_project_name,
                   repourl = repourl,
                #    workdir = poller_name + '-workdir',
                   branches = langs,
                   pollinterval = 600,)
c['change_source'].append(git_poller)

builderNames = []
logname = 'stdio'
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
            'LANGUAGE': 'ru_RU:ru',
            'LC_ALL':'ru_RU.UTF-8',
        }
    else:
        env = {
            'LANG': 'en_US.UTF-8',
            'LANGUAGE': 'en_US:en',
            'LC_ALL':'en_US.UTF-8',
        }
    # factory.addStep(steps.ShellCommand(command=['make', 'spelling'],
    #     name="Check spelling",
    #     haltOnFailure=True,
    #     workdir="build",
    #     env=env,
    #     )
    # )

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
                    util.ShellArg(command=['make', 'json'], logname=logname),
                    util.ShellArg(command=["curl", upload_script_src, '-o', upload_script_name, '-s', '-L'], logname=logname),
                    util.ShellArg(command=['python', upload_script_name, '--build_path', 'build/json', '--ftp', 
                                           'ftp://' + ftp_user + ':' + ftp_password + '@' + ftp_address + ':' + ftp_port '/' + lang], 
                                  logname=logname),
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

    # Disable NGM API
    # factory.addStep(steps.ShellCommand(command=["anarchysphinx", "--overwrite", "ios_maplib_src", "ios_maplib"],
    #                                   description=["make", "swiftdoc for mobile (ios)"],
    #                                   workdir="build/source/ngmobile_dev", warnOnFailure=True,
    #                                   env=env,))

    # 3. build html
    factory.addStep(steps.Sphinx(sphinx_builddir="_build/html", sphinx_sourcedir="source", sphinx_builder="html"))

    # 4. upload to web server
    factory.addStep(steps.ShellSequence(commands=[
        # util.ShellArg(command=['cp', '-r', 'build/spelling', '_build/html/',], logname=logname),
        util.ShellArg(command=['chmod', '-R', '0755', '_build/html/',], logname=logname),
        util.ShellArg(command=['rsync', '-avz', '-e', 'ssh -p {} -i /root/.ssh/www'.format(ssh_port), '_build/html/', 
            '{}@docs.nextgis.net:{}/'.format(ssh_user, lang),], 
            logname=logname),
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

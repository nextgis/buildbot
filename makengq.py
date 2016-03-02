from buildbot.plugins import *
from buildbot.changes.gitpoller import GitPoller
from buildbot.steps.source.git import Git
from buildbot.config import BuilderConfig
import bbconf

import ngqwebuilder_scheduler
import ngqwebuilder_status_push

dependent_local_modules = [
    'ngqwebuilder_scheduler.py',
    'ngqwebuilder_status_push.py'
]

reload(ngqwebuilder_scheduler)
reload(ngqwebuilder_status_push)

c = {}

ngq_repourl = 'git@github.com:nextgis/NextGIS-QGIS.git'
installer_repourl = 'git@github.com:nextgis/installer.git'
ngq_branch_for_everyday = 'ngq-15_0'

c['change_source'] = []
ngq_git_poller = GitPoller(
    project='ngq',
    repourl=ngq_repourl,
    workdir='ngq-workdir',
    branch=ngq_branch_for_everyday,
    pollinterval=3600,
)
c['change_source'].append(ngq_git_poller)

installer_git_poller = GitPoller(
    project='installer',
    repourl=installer_repourl,
    workdir='installer-workdir',
    branch='4ngq_autobuild',
    pollinterval=3600,
)
c['change_source'].append(installer_git_poller)

c['schedulers'] = []
c['schedulers'].append(
    schedulers.SingleBranchScheduler(
        name="makengq",
        change_filter=util.ChangeFilter(project=['ngq', 'installer']),
        treeStableTimer=None,
        builderNames=["makengq"]
    )
)

c['schedulers'].append(schedulers.ForceScheduler(
                            name="makengq force",
                            builderNames=["makengq", "makengq-release"],
                            properties=[
                                util.StringParameter(
                                    name="release_ngq_branch",
                                    label="Release NGQ branch:<br>",
                                    default=ngq_branch_for_everyday, size=80),
                            ]
))

c['schedulers'].append(schedulers.ForceScheduler(
                            name="makengq-custom force",
                            builderNames=["makengq-custom"],
                            properties=[
                                util.StringParameter(
                                    name="release_ngq_branch",
                                    label="Release NGQ branch:<br>",
                                    default=ngq_branch_for_everyday, size=80),
                                util.StringParameter(
                                    name="build_order_id",
                                    label="Build order id from ngq build service:<br>",
                                    size=80),
                            ]
))

c['schedulers'].append(
    ngqwebuilder_scheduler.NGQWebBuilderForceScheduler(
        "makengq-custom ngq build service",
        8011,
        ["makengq-custom"]
    )
)

c['builders'] = []
# 0. download configuration
ngq_download_customization_conf = steps.ShellCommand(
    name='download customization configuration',
    haltOnFailure=True,
    command=[
        'wget',
        util.Interpolate(
            'http://192.168.250.160:6543/build_order/%(prop:build_order_id)s/configuration'
        ),
        '-O',
        util.Interpolate('%(prop:workdir)s\\customization_config.zip')
    ],
    workdir=util.Interpolate('%(prop:workdir)s')
)

# 1. check out the source
ngq_get_src_bld_step = Git(
    name='checkout ngq',
    repourl=ngq_repourl,
    branch=ngq_branch_for_everyday,
    mode='full',
    method='clobber',
    submodules=True,
    workdir='ngq_src',
    timeout=1800
)
ngq_get_src_rel_step = Git(
    name='checkout ngq',
    repourl=ngq_repourl,
    branch=util.Interpolate('%(prop:release_ngq_branch)s'),
    mode='full',
    method='clobber',
    submodules=True,
    workdir='ngq_src',
    timeout=1800
)
installer_get_step = Git(
    name='checkout installer',
    repourl=installer_repourl,
    branch='4ngq_autobuild',
    mode='full',
    workdir='installer',
    timeout=1800
)

# 2. patching
ngq_customization_src_step = steps.ShellCommand(
        name='customization ngq src',
        haltOnFailure=True,
        command=[
            'call', 'ngq-patch.bat',
            util.Interpolate('%(prop:workdir)s\\customization_config.zip'),
            util.Interpolate('%(prop:workdir)s\\ngq_src')
        ],
        workdir=".\\installer"
)

# 3. configuration
remove_build_dir_step = steps.RemoveDirectory(
    name='clean prev build',
    dir=".\\ngq-build"
)

ngq_release_conf_step = steps.ShellCommand(
    name='cmake configuration ngq RELEASE',
    haltOnFailure=True,
    command=[
        'call', 'ngq-configurate.bat',
        util.Interpolate('%(prop:workdir)s\\ngq-build'),
        util.Interpolate('%(prop:workdir)s\\ngq-install'),
        util.Interpolate('%(prop:workdir)s\\ngq_src'),
        'RELEASE'
    ],
    env={'BUILDNUMBER': util.Interpolate('%(prop:buildnumber)s')},
    workdir=".\\installer"
)

ngq_build_conf_step = steps.ShellCommand(
    name='cmake configuration ngq BUILD',
    haltOnFailure=True,
    command=[
        'call', 'ngq-configurate.bat',
        util.Interpolate('%(prop:workdir)s\\ngq-build'),
        util.Interpolate('%(prop:workdir)s\\ngq-install'),
        util.Interpolate('%(prop:workdir)s\\ngq_src'),
        'BUILD'
    ],
    env={'BUILDNUMBER': util.Interpolate('%(prop:buildnumber)s')},
    workdir=".\\installer"
)
# 4. build
ngq_build_step = steps.ShellCommand(
    name='build ngq',
    haltOnFailure=True,
    command=[
        'call', 'ngq-build.bat',
        util.Interpolate('%(prop:workdir)s\\ngq-build'),
        "qgis2.8.3.sln"
    ],
    workdir='.\\installer',
    timeout=None
)

# 5. make installer
ngq_make_installer_step = steps.ShellCommand(
    name='make ngq installer',
    haltOnFailure=True,
    command=[
        'call', 'ngq-make-installer.bat',
        util.Interpolate("%(prop:workdir)s\\ngq-install"),
        util.Interpolate("%(prop:workdir)s")
    ],
    workdir=".\\installer",
    timeout=None
)

ngq_customize_make_installer_step = steps.ShellCommand(
    name='make ngq customization installer',
    haltOnFailure=True,
    command=[
        'call', 'ngq-custom-make-installer.bat',
        util.Interpolate('%(prop:workdir)s\\customization_config.zip'),
        util.Interpolate("%(prop:workdir)s\\ngq-install"),
        util.Interpolate("%(prop:workdir)s")
    ],
    workdir=".\\installer",
    timeout=None
)

# 6. upload to ftp
ftp_server = 'nextgis.ru'
ftp_conn_string = 'ftp://%s@%s' % (bbconf.ftp_upldsoft_user, ftp_server)
ngq_ftp_upload_installer_step = steps.ShellCommand(
    name='upload installer to ftp(%s)' % ftp_server,
    haltOnFailure=True,
    command=[
        "call", "ftp_put_installer.bat",
        ftp_conn_string,
        util.Interpolate("%(prop:workdir)s\\.meta-ngq"),
        'qgis/ngq-builds'
    ],
    workdir=".\\installer",
    timeout=None
)


ngq_ftp_upload_meta_bld_step = steps.ShellCommand(
    name='upload meta-file to ftp(%s)' % ftp_server,
    haltOnFailure=True,
    command=[
        "call", "ftp_put_metafile.bat",
        ftp_conn_string,
        util.Interpolate("%(prop:workdir)s\\.meta-ngq"),
        'qgis/.meta-ngq-commercial'
    ],
    workdir=".\\installer",
    timeout=None
)
ngq_ftp_upload_meta_rel_step = steps.ShellCommand(
    name='upload meta-file to ftp(%s)' % ftp_server,
    haltOnFailure=True,
    command=[
        "call", "ftp_put_metafile.bat",
        ftp_conn_string,
        util.Interpolate("%(prop:workdir)s\\.meta-ngq"),
        'qgis/.meta-ngq'
    ],
    workdir=".\\installer",
    timeout=None
)

ngq_custom_put_installer_to_build_service = steps.ShellCommand(
    name='put installer to build service(%s)' % '192.168.250.160:6543',
    haltOnFailure=True,
    command=[
        util.Interpolate("%(prop:workdir)s\\installer\\curl_put.bat"),
        util.Interpolate(
            'http://192.168.250.160:6543/build_order/%(prop:build_order_id)s/installer'
        ),
    ],
    workdir=util.Interpolate("%(prop:workdir)s"),
    timeout=None
)

ngq_release_steps = [
    ngq_get_src_rel_step,
    installer_get_step,
    remove_build_dir_step,
    ngq_release_conf_step,
    ngq_build_step,
    ngq_make_installer_step,
    ngq_ftp_upload_installer_step,
    ngq_ftp_upload_meta_rel_step
]

ngq_release_factory = util.BuildFactory(ngq_release_steps)
ngq_release_builder = BuilderConfig(
    name='makengq-release',
    slavenames=['build-ngq-win7'],
    factory=ngq_release_factory
)
c['builders'].append(ngq_release_builder)

ngq_bld_steps = [
    ngq_get_src_bld_step,
    installer_get_step,
    remove_build_dir_step,
    ngq_build_conf_step,
    ngq_build_step,
    ngq_make_installer_step,
    ngq_ftp_upload_installer_step,
    ngq_ftp_upload_meta_bld_step
]

ngq_comercial_factory = util.BuildFactory(ngq_bld_steps)
ngq_comercial_builder = BuilderConfig(
    name='makengq',
    slavenames=['build-ngq-win7'],
    factory=ngq_comercial_factory
)
c['builders'].append(ngq_comercial_builder)

ngq_custom_bld_steps = [
    ngq_download_customization_conf,
    ngq_get_src_rel_step,
    installer_get_step,
    remove_build_dir_step,
    ngq_customization_src_step,
    ngq_release_conf_step,
    ngq_build_step,
    ngq_customize_make_installer_step,
    ngq_custom_put_installer_to_build_service
]
ngq_custom_factory = util.BuildFactory(ngq_custom_bld_steps)
ngq_custom_builder = BuilderConfig(
    name='makengq-custom',
    slavenames=['build-ngq-win7'],
    factory=ngq_custom_factory,
    mergeRequests=lambda builder, breq1, breq2: False
)
c['builders'].append(ngq_custom_builder)

c['status'] = [
    ngqwebuilder_status_push.NGQWebBuilderNotifier(
        "http://192.168.250.160:6543/buildbot_status",
        ["makengq-custom"]
    )
]

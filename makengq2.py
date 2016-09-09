from buildbot.plugins import *
from buildbot.changes.gitpoller import GitPoller
from buildbot.steps.source.git import Git
from buildbot.config import BuilderConfig
import bbconf

c = {}

ngq_repourl = 'git@github.com:nextgis/NextGIS-QGIS.git'
ngq_branch = 'ngq_borsch'
project_name = 'ngq2'

c['change_source'] = []
ngq_git_poller = GitPoller(
    project=project_name,
    repourl=ngq_repourl,
    workdir='%s-workdir' % project_name,
    branch=ngq_branch,
    pollinterval=3600,
)
c['change_source'].append(ngq_git_poller)

c['schedulers'] = []
c['schedulers'].append(
    schedulers.ForceScheduler(
        name="%s force" % project_name,
        builderNames=["makengq2", "makengq2_deb"]
    )
)

c['builders'] = []

cmake_config = [
    "-DWITH_GRASS=FALSE",
    "-DWITH_GRASS7=FALSE",
    "-DWITH_DESKTOP=TRUE",
    "-DWITH_POSTGRESQL=FALSE",
    "-DWITH_BINDINGS=TRUE",
    "-DWITH_SERVER=FALSE",
    "-DWITH_SERVER=FALSE",
    "-DWITH_CUSTOM_WIDGETS=FALSE",
    "-DWITH_ASTYLE=FALSE",
    "-DWITH_ICONV_EXTERNAL=TRUE",
    "-DWITH_ZLIB_EXTERNAL=TRUE",
    "-DWITH_CURL_EXTERNAL=TRUE",
    "-DWITH_EXPAT_EXTERNAL=TRUE",
    "-DWITH_JSONC_EXTERNAL=TRUE",
    "-DWITH_GDAL_EXTERNAL=TRUE",
    "-DWITH_JPEG_EXTERNAL=TRUE",
    "-DWITH_TIFF_EXTERNAL=TRUE",
    "-DWITH_PROJ4_EXTERNAL=TRUE",
    "-DWITH_GeoTIFF_EXTERNAL=TRUE",
    "-DWITH_PNG_EXTERNAL=TRUE",
    "-DWITH_GEOS_EXTERNAL=TRUE",
    "-DWITH_Sqlite3_EXTERNAL=TRUE",
    "-DWITH_Spatialindex_EXTERNAL=TRUE",
    "-DWITH_Spatialite_EXTERNAL=TRUE",
    "-DWITH_LibXml2_EXTERNAL=TRUE",
    "-DWITH_FREEXL_EXTERNAL=TRUE",
    "-DWITH_FREEXL_EXTERNAL=TRUE",
    "-DWITH_OpenSSL=TRUE",
    "-DWITH_OpenSSL_EXTERNAL=TRUE",
    "-DENABLE_TESTS=FALSE",
    "-DWITH_INTERNAL_QWTPOLAR=FALSE",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DWITH_PYTHON=TRUE",  # for gdal python bindings
]
cmake_build = ['--build', '.', '--config', 'release', '--clean-first']
cmake_pack = ['--build', '.', '--target', 'package', '--config', 'release']
ftp = 'ftp://192.168.255.1'
ftp_myng_server = '192.168.255.51'

build_env = {
    'LANG': 'en_US',
    'BUILDNUMBER': util.Interpolate('%(prop:buildnumber)s'),
}

# 1. check out the source
ngq_get_src_bld_step = Git(
    name='checkout ngq',
    repourl=ngq_repourl,
    branch=ngq_branch,
    mode='incremental',
    submodules=True,
    workdir='ngq_src',
    timeout=1800
)

# 2. configuration
ngq_configrate = steps.ShellCommand(
    command=[
        "cmake",
        cmake_config,
        '-G', 'Visual Studio 12 2013',
        '-T', 'v120_xp',
        util.Interpolate('%(prop:workdir)s\\ngq_src')
    ],
    name="configure",
    description=["cmake", "configure for win32"],
    descriptionDone=["cmake", "configured for win32"],
    haltOnFailure=False, warnOnWarnings=True,
    flunkOnFailure=False, warnOnFailure=True,
    workdir="ngq_build32",
    env=build_env,
)


# 3. build
ngq_make = steps.ShellCommand(
    command=["cmake", cmake_build],
    name="make",
    description=["cmake", "make for win32"],
    descriptionDone=["cmake", "made for win32"],
    haltOnFailure=True,
    workdir="ngq_build32",
    env=build_env,
)

# 4. make installer
ngq_make_package = steps.ShellCommand(
    command=["cmake", cmake_pack],
    name="make package",
    description=["cmake", "pack for win32"],
    descriptionDone=["cmake", "packed for win32"],
    haltOnFailure=True,
    workdir="ngq_build32",
    env=build_env,
)

# 5. upload package

ngq_upload_package = steps.ShellCommand(
    command=["call", "ftp_upload.bat", bbconf.ftp_mynextgis_user, ftp_myng_server + '/qgis/'],
    name="upload to ftp ",
    description=["upload", "ngq files to ftp"],
    descriptionDone=["uploaded", "ngq files to ftp"], haltOnFailure=False,
    workdir="ngq_build32"
)

ngq_steps = [
    ngq_get_src_bld_step,
    ngq_configrate,
    ngq_configrate,  # hak for borsch
    ngq_make,
    ngq_make_package,
    ngq_upload_package,
]

ngq_factory = util.BuildFactory(ngq_steps)
ngq_release_builder = BuilderConfig(
    name='makengq2',
    slavenames=['build-ngq2-win7'],
    factory=ngq_factory
)
c['builders'].append(ngq_release_builder)


# deb package --------------------------------------------------
deb_repourl = 'git://github.com/nextgis/ppa.git'

factory_deb = util.BuildFactory()
ubuntu_distributions = ['trusty', 'xenial']

deb_name = 'ngqgis'
deb_dir = 'build/ngq_deb'
code_dir_last = deb_name
code_dir = 'build/%s' % code_dir_last

deb_email = 'alexander.lisovenko@nextgis.com'
deb_fullname = 'Alexander Lisovenko'

env_vars = {'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname}

project_ver = util.Interpolate('16.1.%(prop:buildnumber)s')

factory_deb.addStep(
    steps.Git(
        repourl=deb_repourl,
        mode='incremental',
        submodules=False,
        workdir=deb_dir,
        alwaysUseLatest=True
    )
)
factory_deb.addStep(
    steps.Git(
        repourl=ngq_repourl,
        branch=ngq_branch,
        mode='full',
        submodules=True,
        workdir=code_dir
    )
)

# cleanup
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']
for clean_ext in clean_exts:
    factory_deb.addStep(
        steps.ShellCommand(
            command=['/bin/bash', '-c', 'rm *' + clean_ext],
            name="rm of " + clean_ext,
            description=["rm", "delete"],
            descriptionDone=["rm", "deleted"],
            haltOnFailure=False, warnOnWarnings=True,
            flunkOnFailure=False, warnOnFailure=True
        )
    )

# tar orginal sources
factory_deb.addStep(
    steps.ShellCommand(
        command=[
            "dch.py", '-n', project_ver, '-a',
            deb_name, '-p', 'tar', '-f',
            code_dir_last],
        name="tar",
        description=["tar", "compress"],
        descriptionDone=["tar", "compressed"], haltOnFailure=True
    )
)

# update changelog
for ubuntu_distribution in ubuntu_distributions:
    # copy ... -> debian
    factory_deb.addStep(
        steps.CopyDirectory(
            src=deb_dir + "/ngq/%s/debian" % ubuntu_distribution,
            dest=code_dir + "/debian",
            name="add debian folder",
            haltOnFailure=True
        )
    )

    factory_deb.addStep(
        steps.ShellCommand(
            command=[
                'dch.py', '-n', project_ver, '-a',
                deb_name, '-p', 'fill', '-f',
                code_dir_last, '-o', 'changelog', '-d',
                ubuntu_distribution
            ],
            name='create changelog for ' + ubuntu_distribution,
            description=["create", "changelog"],
            descriptionDone=["created", "changelog"],
            env=env_vars,
            haltOnFailure=True
        )
    )

    # debuild -us -uc -d -S
    factory_deb.addStep(
        steps.ShellCommand(
            command=['debuild', '-us', '-uc', '-S'],
            name='debuild for ' + ubuntu_distribution,
            description=["debuild", "package"],
            descriptionDone=["debuilded", "package"],
            env=env_vars,
            haltOnFailure=True,
            workdir=code_dir
        )
    )

    factory_deb.addStep(
        steps.ShellCommand(
            command=['debsign.sh', "makengq2_deb"],
            name='debsign for ' + ubuntu_distribution,
            description=["debsign", "package"],
            descriptionDone=["debsigned", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )

    # upload to launchpad
    factory_deb.addStep(
        steps.ShellCommand(
            command=[
                '/bin/bash', '-c',
                'dput ppa:nextgis/ppa ' + deb_name + '*' + ubuntu_distribution + '1_source.changes'
            ],
            name='dput for ' + ubuntu_distribution,
            description=["dput", "package"],
            descriptionDone=["dputed", "package"],
            env=env_vars,
            haltOnFailure=True
        )
    )
    
    # delete code_dir + "/debian"
    factory_deb.addStep(
        steps.RemoveDirectory(
            dir=code_dir + "/debian", 
            name="remove debian folder for " + ubuntu_distribution, 
            haltOnFailure=True
        )
    )

# store changelog
factory_deb.addStep(
    steps.ShellCommand(
        command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last, '-o', 'changelog'],
        name='log last comments',
        description=["log", "last comments"],
        descriptionDone=["logged", "last comments"],
        env=env_vars,
        haltOnFailure=True
    )
)

ngq_deb_release_builder = BuilderConfig(
    name='makengq2_deb',
    slavenames=['build-nix'],
    factory=factory_deb
)
c['builders'].append(ngq_deb_release_builder)

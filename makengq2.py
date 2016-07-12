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
        builderNames=["makengq2"]
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
    "-DENABLE_TESTS=FALSE",
    "-DWITH_INTERNAL_QWTPOLAR=FALSE",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DWITH_PYTHON=TRUE",
]
cmake_build = ['--build', '.', '--config', 'release', '--clean-first']
cmake_pack = ['--build', '.', '--target', 'package', '--config', 'release']
ftp = 'ftp://192.168.255.1'

build_env = {
    "INCLUDE": "c:\\Qwt-6.1.2\\include;c:\\QwtPolar-1.1.1\\include;c:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v7.1A\\Include",
    "LIB": "c:\\Qwt-6.1.2\\lib;c:\\QwtPolar-1.1.1\\lib;c:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v7.1A\\lib",
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
    env = build_env,
)


# 3. build
ngq_make = steps.ShellCommand(
    command=["cmake", cmake_build],
    name="make",
    description=["cmake", "make for win32"],
    descriptionDone=["cmake", "made for win32"],
    haltOnFailure=True,
    workdir="ngq_build32",
    env= build_env,
)

# 4. make installer
ngq_make_package = steps.ShellCommand(
    command=["cmake", cmake_pack],
    name="make package",
    description=["cmake", "pack for win32"],
    descriptionDone=["cmake", "packed for win32"],
    haltOnFailure=True,
    workdir="ngq_build32",
    env = build_env,
)

# 5. upload package
cmd = 'for /F "tokens=*" %A in (packages.txt) do (curl -u "' + bbconf.ftp_upldsoft_user + '" -T %A "'+ ftp + '/qgis/ngq-builds/")'
ngq_upload_package = steps.ShellCommand(
    command=cmd,
    name="upload to ftp ", 
    description=["upload", "ngq files to ftp"],
    descriptionDone=["uploaded", "ngq files to ftp"], haltOnFailure=False, 
    workdir= "ngq_build32" 
)
                                           
ngq_steps = [
    ngq_get_src_bld_step,
    ngq_configrate,
    #ngq_configrate, # hak for borsch
    #ngq_make,
    #ngq_make_package,
    ngq_upload_package,
]

ngq_factory = util.BuildFactory(ngq_steps)
ngq_release_builder = BuilderConfig(
    name='makengq2',
    slavenames=['build-ngq-win7'],
    factory=ngq_factory
)
c['builders'].append(ngq_release_builder)

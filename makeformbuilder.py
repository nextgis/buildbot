# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import *

# import bbconf

c = {}

repourl = 'git://github.com/nextgis/formbuilder.git'
project_ver = '2.1.0'
deb_repourl = 'git://github.com/nextgis/ppa.git'
project_name = 'formbuilder'
git_project_name = 'nextgis/formbuilder'

git_poller = changes.GitPoller(project = git_project_name,
                       repourl = repourl,
                       workdir = project_name + '-workdir',
                       branch = 'master', #TODO: buildbot
                       pollinterval = 7200,)
c['change_source'] = [git_poller]

scheduler = schedulers.SingleBranchScheduler(
                            name=project_name,
                            change_filter=util.ChangeFilter(project = git_project_name),
                            treeStableTimer=1*60,
                            builderNames=[project_name + "_deb"]) # TODO: project_name + "_win",
c['schedulers'] = [scheduler]
c['schedulers'].append(schedulers.ForceScheduler(
                            name=project_name + "_force",
                            builderNames=[project_name + "_deb"])) # TODO: project_name + "_win",

#### build fb

## common steps

# ## maximum formats even disabled in oficial build should be present here
# cmake_config_x86 = ['-DQT_DIR_PREFIX_PATH=C:/Qt/5.7/msvc2013', '-DWITH_GDAL_EXTERNAL=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GeoTIFF_EXTERNAL=ON', '-DWITH_ICONV_EXTERNAL=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_PROJ4_EXTERNAL=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_ZLIB_EXTERNAL=ON',  '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DWITH_OpenSSL_EXTERNAL=ON']
# cmake_config_x64 = ['-DQT_DIR_PREFIX_PATH=C:/Qt/5.7/msvc2013_64', '-DWITH_GDAL_EXTERNAL=ON', '-DWITH_EXPAT_EXTERNAL=ON', '-DWITH_GeoTIFF_EXTERNAL=ON', '-DWITH_ICONV_EXTERNAL=ON', '-DWITH_JSONC_EXTERNAL=ON', '-DWITH_PROJ4_EXTERNAL=ON', '-DWITH_TIFF_EXTERNAL=ON', '-DWITH_ZLIB_EXTERNAL=ON',  '-DWITH_JPEG_EXTERNAL=ON', '-DWITH_GEOS_EXTERNAL=ON', '-DWITH_CURL_EXTERNAL=ON', '-DWITH_OpenSSL_EXTERNAL=ON']
# cmake_build = ['--build', '.', '--config', 'release', '--clean-first']
# cmake_pack = ['--build', '.', '--target', 'package', '--config', 'release']
# ftp = 'ftp://192.168.255.1/'
# myftp = 'ftp://192.168.255.51/'
#
# ## build win
#
# factory_win = util.BuildFactory()
# # 1. check out the source

code_dir_last = 'formbuilder_code'
code_dir = 'build/' + code_dir_last
# factory_win.addStep(steps.Git(repourl=repourl, mode='incremental', submodules=False, workdir=code_dir)) #mode='full', method='clobber'
#
# # fill log file
# formbuilder_latest_file = 'formbuilder_latest.log'
# factory_win.addStep(steps.ShellCommand(command=['c:\Python2712\python', '../../dch.py',
#                                                 '-n', project_ver, '-a', 'formbuilder', '-p',
#                                                 'simple', '-f', code_dir_last, '-o',
#                                                 formbuilder_latest_file],
#                                         name='log last comments',
#                                         description=["log", "last comments"],
#                                         descriptionDone=["logged", "last comments"], haltOnFailure=True))
#
# # 2. build fb 32
#
# # make build dir
#
# factory_win.addStep(steps.MakeDirectory(dir=code_dir + "/build32"))
# # configure view cmake
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config_x86, '-G', 'Visual Studio 12 2013', '-T', 'v120_xp', '../'],
#                                        name="configure step 1",
#                                        description=["cmake", "configure for win32"],
#                                        descriptionDone=["cmake", "configured for win32"],
#                                        haltOnFailure=False, warnOnWarnings=True,
#                                        flunkOnFailure=False, warnOnFailure=True,
#                                        workdir=code_dir + "/build32"))
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config_x86, '-G', 'Visual Studio 12 2013', '-T', 'v120_xp', '../'],
#                                        name="configure step 2",
#                                        description=["cmake", "configure for win32"],
#                                        descriptionDone=["cmake", "configured for win32"], haltOnFailure=True,
#                                        workdir=code_dir + "/build32"))
# # make
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build],
#                                        name="make",
#                                        description=["cmake", "make for win32"],
#                                        descriptionDone=["cmake", "made for win32"], haltOnFailure=True,
#                                        workdir=code_dir + "/build32",
#                                        env={'LANG': 'en_US'}))
# # make tests
# # ...
#
# # make package
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack],
#                                        name="make package",
#                                        description=["cmake", "pack for win32"],
#                                        descriptionDone=["cmake", "packed for win32"], haltOnFailure=True,
#                                        workdir=code_dir + "/build32",
#                                        env={'LANG': 'en_US'}))
#
# # 3. build fb 64
#
# # make build dir
# factory_win.addStep(steps.MakeDirectory(dir=code_dir + "/build64"))
#
# # configure view cmake
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config_x64, '-G', 'Visual Studio 12 2013 Win64', '-T', 'v120_xp', '../'],
#                                        name="configure step 1",
#                                        description=["cmake", "configure for win64"],
#                                        descriptionDone=["cmake", "configured for win64"],
#                                        haltOnFailure=False, warnOnWarnings=True,
#                                        flunkOnFailure=False, warnOnFailure=True,
#                                        workdir=code_dir + "/build64"))
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_config_x64, '-G', 'Visual Studio 12 2013 Win64', '-T', 'v120_xp', '../'],
#                                        name="configure step 2",
#                                        description=["cmake", "configure for win64"],
#                                        descriptionDone=["cmake", "configured for win64"], haltOnFailure=True,
#                                        workdir=code_dir + "/build64"))
# # make
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_build],
#                                        name="make",
#                                        description=["cmake", "make for win64"],
#                                        descriptionDone=["cmake", "made for win64"], haltOnFailure=True,
#                                        workdir=code_dir + "/build64",
#                                        env={'LANG': 'en_US'}))
# # make tests
# # ...
#
# # make package
# factory_win.addStep(steps.ShellCommand(command=["cmake", cmake_pack],
#                                        name="make package",
#                                        description=["cmake", "pack for win64"],
#                                        descriptionDone=["cmake", "packed for win64"], haltOnFailure=True,
#                                        workdir=code_dir + "/build64",
#                                        env={'LANG': 'en_US'}))
#
# # upload packages
# #ftp_upload_command = "curl -u " + bbconf.ftp_user + " --ftp-create-dirs -T file ftp://nextgis.ru/programs/formbuilder/"
# upld_file_lst = ['build32/Formbuilder-' + project_ver + '-win32.exe', 'build64/Formbuilder-' + project_ver + '-win64.exe']
# for upld_file in upld_file_lst:
#     factory_win.addStep(steps.ShellCommand(command=['curl', '-u', bbconf.ftp_mynextgis_user,
#                                            '-T', upld_file, '--ftp-create-dirs', myftp + 'formbuilder/'],
#                                            name="upload to ftp",
#                                            description=["upload", "to ftp " + upld_file],
#                                            descriptionDone=["uploaded", "formbuilder files to ftp"], haltOnFailure=False,
#                                            workdir= code_dir ))
# #generate and load formbuilder_latest.log
# factory_win.addStep(steps.ShellCommand(command=['curl', '-u', bbconf.ftp_upldsoft_user,
#                                            '-T', formbuilder_latest_file, '--ftp-create-dirs', ftp + 'qgis/'],
#                                            name="upload to ftp formbuilder_latest.log",
#                                            description=["upload", "formbuilder files to ftp"],
#                                            descriptionDone=["uploaded", "formbuilder files to ftp"], haltOnFailure=False))
#
# factory_win.addStep(steps.ShellCommand(command=['c:\Python2712\python', '../../dch.py',
#                                                 '-n', project_ver, '-a', 'formbuilder', '-p',
#                                                 'store', '-f', code_dir_last],
#                                        name='log last comments',
#                                        description=["log", "last comments"],
#                                        descriptionDone=["logged", "last comments"], haltOnFailure=True))
#
# builder_win = BuilderConfig(name = project_name + '_win', slavenames = ['build-ngq-win7'], factory = factory_win)

# build for debian

# 1. check out the source
factory_deb = util.BuildFactory()
ubuntu_distributions = ['trusty', 'xenial', 'zesty']
# 1. check out the source
deb_name = 'formbuilder'
deb_dir = 'build/formbuilder_deb'
deb_email = 'gusevmihs@gmail.com'
deb_fullname = 'Mikhail Gusev'

factory_deb.addStep(steps.Git(repourl=deb_repourl, mode='incremental', submodules=False, workdir=deb_dir, alwaysUseLatest=True))
factory_deb.addStep(steps.Git(repourl=repourl, mode='full', submodules=False, workdir=code_dir))
#cleanup
clean_exts = ['.tar.gz', '.changes', '.dsc', '.build', '.upload']
for clean_ext in clean_exts:
    factory_deb.addStep(steps.ShellCommand(command=['/bin/bash', '-c', 'rm *' + clean_ext],
                                       name="rm of " + clean_ext,
                                       description=["rm", "delete"],
                                       descriptionDone=["rm", "deleted"],
                                       haltOnFailure=False, warnOnWarnings=True,
                                       flunkOnFailure=False, warnOnFailure=True))
# tar orginal sources
factory_deb.addStep(steps.ShellCommand(command=["dch.py", '-n', project_ver, '-a',
                                                deb_name, '-p', 'tar', '-f',
                                                code_dir_last],
                                       name="tar",
                                       description=["tar", "compress"],
                                       descriptionDone=["tar", "compressed"], haltOnFailure=True))
# copy lib_gdal2 -> debian
factory_deb.addStep(steps.CopyDirectory(src=deb_dir + "/" + deb_name + "/debian", dest=code_dir + "/debian",
                                        name="add debian folder", haltOnFailure=True))
# update changelog
for ubuntu_distribution in ubuntu_distributions:
    factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a',
                                                deb_name, '-p', 'fill', '-f',
                                                code_dir_last,'-o', 'changelog', '-d',
                                                ubuntu_distribution],
                                        name='create changelog for ' + ubuntu_distribution,
                                        description=["create", "changelog"],
                                        descriptionDone=["created", "changelog"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                        haltOnFailure=True))

    # debuild -us -uc -d -S
    factory_deb.addStep(steps.ShellCommand(command=['debuild', '-us', '-uc', '-S'],
                                        name='debuild for ' + ubuntu_distribution,
                                        description=["debuild", "package"],
                                        descriptionDone=["debuilded", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                        haltOnFailure=True,
                                        workdir=code_dir))

    factory_deb.addStep(steps.ShellCommand(command=['debsign.sh', project_name + "_deb"],
                                        name='debsign for ' + ubuntu_distribution,
                                        description=["debsign", "package"],
                                        descriptionDone=["debsigned", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                        haltOnFailure=True))
    # upload to launchpad
    factory_deb.addStep(steps.ShellCommand(command=['/bin/bash','-c',
                                        'dput ppa:nextgis/ppa ' +  deb_name + '*' + ubuntu_distribution + '1_source.changes'],
                                        name='dput for ' + ubuntu_distribution,
                                        description=["dput", "package"],
                                        descriptionDone=["dputed", "package"],
                                        env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                        haltOnFailure=True))

# store changelog
factory_deb.addStep(steps.ShellCommand(command=['dch.py', '-n', project_ver, '-a', deb_name, '-p', 'store', '-f', code_dir_last,'-o', 'changelog'],
                                 name='log last comments',
                                 description=["log", "last comments"],
                                 descriptionDone=["logged", "last comments"],
                                 env={'DEBEMAIL': deb_email, 'DEBFULLNAME': deb_fullname},
                                 haltOnFailure=True))

builder_deb = util.BuilderConfig(name = project_name + '_deb', slavenames = ['build-nix'], factory = factory_deb)

c['builders'] = [builder_deb] # TODO: builder_win,

# NOTIFIER
mn = reporters.MailNotifier(
    fromaddr='buildbot@nextgis.com',
    sendToInterestedUsers=True,
    builders=[builder_deb.name],
    mode=('all'),
    extraRecipients=[deb_email],
    relayhost='192.168.255.1',
    useTls=True
)

c['services'] = [mn]

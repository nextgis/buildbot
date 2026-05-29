"""Custom Buildbot steps for interacting with RepkaSDK service."""

import json
import os
import sys
import shlex
import subprocess

from buildbot.process import buildstep
from buildbot.process.results import FAILURE, SUCCESS
from twisted.internet import defer


VENV_DIR_PROPERTY_NAME = 'venv_dir'


class VenvMixin:
    def __init__(self, venv_dir="venv", **kwargs):
        self.__venv_dir = venv_dir
        super().__init__(**kwargs)

    def set_venv_dir(self, venv_dir) -> None:
        self.__venv_dir = venv_dir

    def get_venv_dir(self) -> str:
        """Returns path to venv directory"""
        return self.__venv_dir

    def get_venv_exec_path(self, executable='python'):
        """Returns path to executable inside the venv for current OS."""
        if sys.platform == 'win32':
            return os.path.join(self.__venv_dir, 'Scripts', executable)
        else:
            return os.path.join(self.__venv_dir, 'bin', executable)

    def get_activate_command(self):
        return self.get_venv_exec_path('activate')


class ComplexCommandMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def make_command(self, args_list: list[str]) -> str:            
        shell_operators = {'&&', '||', ';', '|', '>', '>>', '<', '&'}
        
        result_parts = []
        current_subcommand = []
        
        for item in args_list:
            if item in shell_operators:
                if current_subcommand:
                    if sys.platform == 'win32':
                        result_parts.append(subprocess.list2cmdline(current_subcommand))
                    else:
                        result_parts.append(shlex.join(current_subcommand))
                    current_subcommand = []
                result_parts.append(item)
            else:
                current_subcommand.append(item)
                
        if current_subcommand:
            if sys.platform == 'win32':
                result_parts.append(subprocess.list2cmdline(current_subcommand))
            else:
                result_parts.append(shlex.join(current_subcommand))
        
        return " ".join(result_parts)

    def make_complex_command(self, command: list[str]):
        if sys.platform == 'win32':
            cmd_list = ["cmd.exe", "/c"]
        else:
            cmd_list = ["/bin/sh", "-c"]
        return cmd_list + [self.make_command(command)]


class RepkaEnsureSdk(VenvMixin, ComplexCommandMixin, buildstep.ShellMixin, buildstep.BuildStep):
    """Ensure Repka CLI is available and optionally authenticated.

    Behavior:
    - Ensure repka-sdk exists by running ``command``.
    - If the installation failed, the step fails immediately.
    - If both ``username`` and ``password`` are provided, authenticate against
      the Repka server using ``repka auth login ... dotenv``, which stores
      credentials in a ``.env`` file on the worker.
    - On success, the step description is set to ``["repka-ensure-sdk", "ok"]``.

    :param username: Repka username for authentication (optional).
    :type username: str or None
    :param password: Repka password for authentication (optional).
    :type password: str or None
    :param server_url: Repka server URL.
    :type server_url: str
    """

    def __init__(self, username=None, password=None, server_url="https://rm.staging.nextgis.com", venv_dir=".venv", **kwargs):
        self.username = username
        self.password = password
        self.server_url = server_url
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(venv_dir=venv_dir, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        cmd = yield self.makeRemoteShellCommand(
            command=[sys.executable, '-m', 'venv', self.get_venv_dir()],  # python -m venv ./env
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(cmd)
        if cmd.didFail():
            defer.returnValue(FAILURE)

        cmd = yield self.makeRemoteShellCommand(
            command=self.make_complex_command([self.get_activate_command(), '&&', 'pip', 'install', 'repka-sdk']),
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(cmd)
        if cmd.didFail():
            defer.returnValue(FAILURE)


        if self.username is None or self.password is None:
            defer.returnValue(FAILURE)

        cmd = yield self.makeRemoteShellCommand(
            command=self.make_complex_command([
                self.get_activate_command(), 
                '&&',
                'repka', 
                'auth', 
                'login', 
                '-f', 
                '-u', self.username, 
                '-p', self.password, 
                '--url', self.server_url, 
                'dotenv'
            ]),
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(cmd)
        if cmd.didFail():
            defer.returnValue(FAILURE)

        self.setProperty(VENV_DIR_PROPERTY_NAME, self.get_venv_dir(), 'RepkaEnsureSdk')
        self.descriptionDone = ["repka-ensure-sdk", "ok"]
        defer.returnValue(SUCCESS)


class RepkaCreateRelease(VenvMixin, ComplexCommandMixin, buildstep.ShellMixin, buildstep.BuildStep):
    """Create a package and a release in Repka from local files.

    Behavior:
    - Construct a ``repka --json package create`` command with the given
      ``package`` identifier and upload each file from ``files``.
    - On success, extract the package ID from the JSON output and set the
      build property ``repka_package_id``.
    - Then run ``repka --json release create`` using the obtained package ID,
      release name, optional version tag and ``--latest`` flag.
    - On success, extract the release ID and set the build property
      ``repka_release_id``.
    - If any command fails or JSON parsing fails, the step fails and logs
      an error.
    - On success, the step description is set to
      ``["repka-release", "ok", <release_id>]``.

    :param package: Package identifier (e.g., project name).
    :type package: str
    :param release_name: Human-readable release name.
    :type release_name: str
    :param files: List of file paths to upload.
    :type files: list of str
    :param version_tag: Optional version tag for the release.
    :type version_tag: str or None
    :param mark_latest: If ``True``, add ``--latest`` flag to the release command.
    :type mark_latest: bool
    :param options: Additional CLI options.
    :type options: dict or None
    """

    def __init__(self, package, release_name, release_description, files, version_tag=None, mark_latest=False, tags=None, options=None, **kwargs):
        self.package = package
        self.release_name = release_name
        self.release_description = release_description
        self.files = files
        self.tags = tags or []
        self.version_tag = version_tag
        self.mark_latest = mark_latest
        self.options = options or {}
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.set_venv_dir(self.getProperty(VENV_DIR_PROPERTY_NAME))

        shell_cmd = yield self.makeRemoteShellCommand(
            command=self.make_complex_command([
                self.get_activate_command(),
                '&&',
                'repka', '--json', 
                'package', 'create', 
                '-r', self.package, 
                '-n', f'"package-{self.package}"'
            ]),
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(shell_cmd)

        if shell_cmd.didFail():
            self.descriptionDone = ["repka-release", "failed"]
            defer.returnValue(FAILURE)

        try:
            result = json.loads(shell_cmd.stdout)
            package_id = result['id']
            self.setProperty("repka_package_id", package_id, "RepkaCreateRelease")

            cmd = [
                'repka', '--json', 'release', 'create', 
                '-p', package_id, 
                '-n', self.release_name, 
                '-d', self.release_description
            ]
    
            for file in self.files:
                cmd.extend(['--file', file])
            for tag in self.tags:
                cmd.extend(['--tag', tag])
            for option in self.options:
                cmd.extend(['--option', option])

            if self.version_tag:
                cmd.extend(['--version-tag', self.version_tag])
            if self.mark_latest:
                cmd.append('--latest')

            shell_cmd = yield self.makeRemoteShellCommand(
                command=self.make_complex_command([
                    self.get_activate_command(),
                    '&&',
                    *cmd
                ]),
                collectStdout=True,
                logEnviron=False
            )
            yield self.runCommand(shell_cmd)

            if shell_cmd.didFail():
                self.descriptionDone = ["repka-release", "failed"]
                defer.returnValue(FAILURE)

            release_id = result['id']
            self.setProperty("repka_release_id", release_id, "RepkaCreateRelease")
            
            self.descriptionDone = ["repka-create-release", "ok", str(release_id)]
            defer.returnValue(SUCCESS)
        except Exception as e:
            self.addCompleteLog("repka-release-error", f"Failed to parse JSON: {e}")
            defer.returnValue(FAILURE)

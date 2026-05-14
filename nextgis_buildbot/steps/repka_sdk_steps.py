"""Custom Buildbot steps for interacting with RepkaSDK service."""

import json

from buildbot.process import buildstep
from buildbot.process.results import FAILURE, SUCCESS
from twisted.internet import defer

class RepkaEnsureSdk(buildstep.ShellMixin, buildstep.BuildStep):
    """Ensure Repka CLI is available and optionally authenticated.

    Behavior:
    - Check if the ``repka`` command exists by running ``command -v repka``.
    - If the command is not found, the step fails immediately.
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

    def __init__(self, username=None, password=None, server_url="https://rm.staging.nextgis.com", **kwargs):
        self.username = username
        self.password = password
        self.server_url = server_url
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        cmd = yield self.makeRemoteShellCommand(
            command=['command', '-v', 'repka'],
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(cmd)
        if cmd.didFail():
            defer.returnValue(FAILURE)
        elif self.username is not None and self.password is not None:
            cmd = yield self.makeRemoteShellCommand(
                command=['repka', 'auth', 'login', '-f', '-u', self.username, '-p', self.password, '--url', self.server_url, 'dotenv'],
                collectStdout=True,
                logEnviron=False
            )
            yield self.runCommand(cmd)

            if cmd.didFail():
                defer.returnValue(FAILURE)

            self.descriptionDone = ["repka-ensure-sdk", "ok"]
            defer.returnValue(SUCCESS)


class RepkaCreateRelease(buildstep.ShellMixin, buildstep.BuildStep):
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

    def __init__(self, package, release_name, files, version_tag=None, mark_latest=False, options=None, **kwargs):
        self.package = package
        self.release_name = release_name
        self.files = files
        self.version_tag = version_tag
        self.mark_latest = mark_latest
        self.options = options or {}
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        cmd = ['repka', '--json', 'package', 'create', '-r', self.package, '-n', f'"package-{self.package}"']
        
        shell_cmd = yield self.makeRemoteShellCommand(
            command=cmd,
            collectStdout=True,
            logEnviron=False
        )
        yield self.runCommand(shell_cmd)

        if shell_cmd.didFail():
            self.descriptionDone = ["repka-release", "failed"]
            defer.returnValue(FAILURE)
        else:
            try:
                result = json.loads(shell_cmd.stdout)
                package_id = result['id']
                self.setProperty("repka_package_id", package_id, "RepkaCreateRelease")

                cmd = ['repka', '--json', 'release', 'create', '-p', package_id, '-n', self.release_name]
        
                for f in self.files:
                    cmd.extend(['--file', f])

                if self.version_tag:
                    cmd.extend(['--version-tag', self.version_tag])
                if self.mark_latest:
                    cmd.append('--latest')

                shell_cmd = yield self.makeRemoteShellCommand(
                    command=cmd,
                    collectStdout=True,
                    logEnviron=False
                )
                yield self.runCommand(shell_cmd)

                if shell_cmd.didFail():
                    self.descriptionDone = ["repka-release", "failed"]
                    defer.returnValue(FAILURE)

                release_id = result['id']
                self.setProperty("repka_release_id", release_id, "RepkaCreateRelease")
                
                self.descriptionDone = ["repka-release", "ok", str(release_id)]
                defer.returnValue(SUCCESS)
            except Exception as e:
                self.addCompleteLog("repka-release-error", f"Failed to parse JSON: {e}")
                defer.returnValue(FAILURE)

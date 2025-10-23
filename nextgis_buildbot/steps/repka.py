"""Custom Buildbot steps for interacting with Repka service."""

import json
from typing import List, Optional, Union

from buildbot.plugins import util
from buildbot.process import buildstep
from buildbot.process.results import FAILURE, SUCCESS
from twisted.internet import defer

ENDPOINT = "https://rm.nextgis.com"
USERNAME = "buildbot"


class RepkaUpload(buildstep.ShellMixin, buildstep.BuildStep):
    """Upload files to Repka using curl from the worker.

    :param files: Single path or list of paths to files to upload. Paths must
        exist on the worker where this step executes.
    :type files: str | list[str]

    Behavior:
    - Execute curl on the worker and expect JSON response per file.
    - Parse each response and aggregate descriptors as
      ``{"upload_name": <uid>, "name": <name>}``.
    - Store the aggregated list into the build property
      ``repka_uploaded_files`` for subsequent steps.
    - Fail the step if any upload fails or JSON cannot be parsed.
    """

    def __init__(
        self,
        files: Union[str, List[str]],
        **kwargs,
    ) -> None:
        if isinstance(files, str):
            self._files = [files]
        else:
            self._files = list(files)

        kwargs = self.setupShellMixin(kwargs, prohibitArgs=["command"])
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        """Execute uploads sequentially and aggregate results.

        The step sets a build property named ``repka_uploaded_files`` containing
        a list of dictionaries with keys ``upload_name`` and ``name`` when at
        least one file is uploaded successfully.

        :returns: Build result code: ``SUCCESS`` on success, ``FAILURE`` if an
                  upload fails or the server returns invalid JSON.
        :rtype: buildbot.process.results.Results
        """

        uploaded: List[dict] = []
        api_url = f"{ENDPOINT.rstrip('/')}/api/upload"

        if not self._files:
            self.descriptionDone = ["repka-upload", "no-files"]
            defer.returnValue(FAILURE)

        assert self.build is not None
        credentials = yield self.build.render(
            util.Interpolate(f"{USERNAME}:%(secret:buildbot_password)s")
        )

        for file_path in self._files:
            # Build curl command for worker-side execution
            cmdline = [
                "curl",
                "-sS",  # silent but show errors
                "-fL",  # fail on HTTP errors, follow redirects
                "-k",  # allow self-signed TLS if needed (optional safety)
                "-u",
                credentials,
                "-H",
                "Accept: application/json",
                "-F",
                f"file=@{file_path}",
                api_url,
            ]

            cmd = yield self.makeRemoteShellCommand(
                command=cmdline,
                collectStdout=True,
                logEnviron=False,
            )
            yield self.runCommand(cmd)

            if cmd.didFail():
                # Stop on the first failure
                self.descriptionDone = [
                    "repka-upload",
                    "failed",
                    file_path,
                ]
                defer.returnValue(FAILURE)

            # Parse JSON from stdout
            try:
                # Access stdio log content
                stdout_text = cmd.stdout if cmd.stdout else ""
                response = json.loads(stdout_text.strip())
                file_uid = response["file"]
                file_name = response["name"]
                uploaded.append({"upload_name": file_uid, "name": file_name})
            except Exception as exc:  # JSON parse error or missing fields
                self.descriptionDone = [
                    "repka-upload",
                    "invalid-response",
                ]
                # Mark this step as failed due to invalid server response
                self.addCompleteLog(
                    "repka-upload-error",
                    f"Failed to parse response for {file_path}: {exc}\n",
                )
                defer.returnValue(FAILURE)

        # Save aggregated result for downstream steps
        try:
            self.setProperty("repka_uploaded_files", uploaded, "RepkaUpload")
        except Exception:
            self.descriptionDone = [
                "repka-upload",
                "cant-set-property",
            ]
            self.addCompleteLog(
                "repka-upload-error",
                "Failed to set property repka_uploaded_files\n",
            )
            defer.returnValue(FAILURE)

        self.descriptionDone = ["repka-upload", "ok", str(len(uploaded))]
        defer.returnValue(SUCCESS)


class RepkaCreateRelease(buildstep.ShellMixin, buildstep.BuildStep):
    """Create a Repka release using uploaded files from a previous step.

    Constructor arguments:
    - package: Packet identifier.
    - release_name: Release name to display.
    - release_description: Optional release description.
    - tags: Optional list of tags; may be empty. Use ``mark_latest`` flag to
      auto-append ``"latest"``.
    - distribution: Optional distribution option value.
    - os: Optional operating system option value.
    - channel: Optional release channel (e.g., stable, beta, dev).
    - mark_latest: If ``True``, ensure ``"latest"`` is present in tags.

    Behavior:
    - Read ``repka_uploaded_files`` property produced by :class:`RepkaUpload`.
    - Compose JSON payload and perform a POST request to ``/api/release``
      using ``curl`` on the worker.
    - On success, set build property ``repka_release_id`` with created ID.
    - Fail the step when inputs are invalid or server returned an error.
    """

    def __init__(
        self,
        package: int,
        release_name: str,
        release_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        distribution: Optional[str] = None,
        os: Optional[str] = None,
        channel: Optional[str] = None,
        mark_latest: bool = False,
        **kwargs,
    ) -> None:
        self._package = package
        self._release_name = release_name
        self._release_description = release_description
        self._tags = list(tags) if tags else []
        self._distribution = distribution
        self._os = os
        self._channel = channel
        self._mark_latest = mark_latest

        kwargs = self.setupShellMixin(kwargs, prohibitArgs=["command"])
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        """Create release in Repka using prepared uploads.

        :returns: Build result code.
        :rtype: buildbot.process.results.Results
        """

        # Validate files from previous RepkaUpload step
        uploaded_files = self.getProperty("repka_uploaded_files")
        if not uploaded_files or not isinstance(uploaded_files, list):
            self.descriptionDone = [
                "repka-release",
                "no-files",
            ]
            defer.returnValue(FAILURE)

        # Prepare packet id
        packet_id = self._package

        # Tags handling
        tags: List[str] = list(self._tags) if self._tags else []
        if self._mark_latest and "latest" not in tags:
            tags.append("latest")

        # Options mapping
        options: List[dict] = []
        if self._distribution is not None:
            options.append({"key": "dist", "value": str(self._distribution)})
        if self._os is not None:
            options.append({"key": "os", "value": str(self._os)})
        if self._channel is not None:
            options.append({"key": "type", "value": str(self._channel)})

        assert self.build is not None  # help type checkers

        release_name = yield self.build.render(self._release_name)

        payload = {
            "packet": packet_id,
            "name": release_name,
            "files": uploaded_files,
        }
        if self._release_description is not None:
            payload["description"] = self._release_description
        if tags:
            payload["tags"] = tags
        if options:
            payload["options"] = options

        api_url = f"{ENDPOINT.rstrip('/')}/api/release"

        credentials = yield self.build.render(
            util.Interpolate(f"{USERNAME}:%(secret:buildbot_password)s")
        )

        # Execute curl on worker to create release
        try:
            json_body = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to serialize payload: {exc}\n",
            )
            self.descriptionDone = ["repka-release", "bad-payload"]
            defer.returnValue(FAILURE)

        cmdline = [
            "curl",
            "-sS",
            "-fL",
            "-k",
            "-u",
            credentials,
            "-H",
            "Accept: application/json",
            "-H",
            "Content-Type: application/json",
            "-d",
            json_body,
            api_url,
        ]

        cmd = yield self.makeRemoteShellCommand(
            command=cmdline,
            collectStdout=True,
            logEnviron=False,
        )
        yield self.runCommand(cmd)

        if cmd.didFail():
            self.descriptionDone = ["repka-release", "failed"]
            defer.returnValue(FAILURE)

        # Parse response
        try:
            stdout_text = cmd.stdout if cmd.stdout else ""
            response = json.loads(stdout_text.strip())
            release_id = response["id"]
        except Exception as exc:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to parse response: {exc}\n",
            )
            self.descriptionDone = ["repka-release", "invalid-response"]
            defer.returnValue(FAILURE)

        # Save release id for downstream steps
        try:
            self.setProperty("repka_release_id", release_id, "RepkaCreateRelease")
        except Exception:
            self.addCompleteLog(
                "repka-release-error",
                "Failed to set property repka_release_id\n",
            )
            self.descriptionDone = [
                "repka-release",
                "cant-set-property",
            ]
            defer.returnValue(FAILURE)

        yield self.addURL("repka-package", f"{ENDPOINT.rstrip('/')}/packet/{packet_id}")

        self.descriptionDone = ["repka-release", "ok", str(release_id)]
        defer.returnValue(SUCCESS)

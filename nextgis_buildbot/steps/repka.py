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
    :param str username: Repka username used for Basic Auth.
    :param str password: Repka password used for Basic Auth.
    :type files: str | list[str]
    :param endpoint: Repka endpoint base URL. Defaults to
        ``"https://rm.nextgis.com"``.
    :type endpoint: str | None

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
                stdio_log = cmd.logs.get("stdio")
                stdout_text = stdio_log.getText() if stdio_log else ""
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
            # Non-fatal if property cannot be set
            pass

        self.descriptionDone = ["repka-upload", "ok", str(len(uploaded))]
        defer.returnValue(SUCCESS)

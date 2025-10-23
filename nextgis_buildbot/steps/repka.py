"""Custom Buildbot steps for interacting with Repka service."""

import json
from typing import Dict, List, Optional, Union

from buildbot.plugins import util
from buildbot.process import buildstep
from buildbot.process.results import FAILURE, SUCCESS
from twisted.internet import defer

from nextgis_buildbot.utils import human_readable_size

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
    - options: Dictionary containing optional parameters.

    Behavior:
    - Read ``repka_uploaded_files`` property produced by :class:`RepkaUpload`.
    - Compose JSON payload and perform a POST request to ``/api/release``
      using ``curl`` on the worker.
    - On success, set build property ``repka_release_id`` with created ID.
    - Fail the step when inputs are invalid or server returned an error.
    """

    def __init__(
        self,
        packet: int,
        release_name: str,
        release_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        options: Optional[Dict[str, str]] = None,
        mark_latest: bool = False,
        **kwargs,
    ) -> None:
        self._packet = packet
        self._release_name = release_name
        self._release_description = release_description
        self._tags = list(tags) if tags else []
        self._options = options or {}
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
            self.descriptionDone = ["repka-release", "no-files"]
            defer.returnValue(FAILURE)

        packet_id = self._packet

        try:
            json_body = yield self._build_release_payload(
                packet_id=packet_id, files=uploaded_files
            )
            credentials = yield self._get_credentials()

        except Exception as exc:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to prepare release request: {exc}\n",
            )
            self.descriptionDone = ["repka-release", "bad-payload"]
            defer.returnValue(FAILURE)

        try:
            release_id = yield self._post_release(credentials, json_body)

        except _CurlFailedError:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to create release for packet {packet_id}\n",
            )
            self.descriptionDone = ["repka-release", "failed"]
            defer.returnValue(FAILURE)

        except Exception as exc:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to parse response: {exc}\n",
            )
            self.descriptionDone = ["repka-release", "invalid-response"]
            defer.returnValue(FAILURE)

        # Save release id for downstream steps
        if not self._save_release_id(release_id):
            self.descriptionDone = ["repka-release", "cant-set-property"]
            defer.returnValue(FAILURE)

        # Add package page URL
        yield self._add_package_url(packet_id)

        # Fetch files and add download URLs
        try:
            files_array = yield self._fetch_release_files(credentials, release_id)
        except _CurlFailedError:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to fetch release info for packet {packet_id}\n",
            )
            self.descriptionDone = ["repka-release", "fetch-failed"]
            defer.returnValue(FAILURE)
        except Exception as exc:
            self.addCompleteLog(
                "repka-release-error",
                f"Failed to parse release files: {exc}\n",
            )
            self.descriptionDone = ["repka-release", "invalid-release-response"]
            defer.returnValue(FAILURE)

        yield self._add_file_urls(files_array)

        self.descriptionDone = ["repka-release", "ok", str(release_id)]
        defer.returnValue(SUCCESS)

    def _compute_tags(self) -> List[str]:
        """Compute final tags list based on init parameters.

        :returns: List of tags; adds "latest" when requested.
        :rtype: list[str]
        """

        tags: List[str] = list(self._tags) if self._tags else []
        if self._mark_latest and "latest" not in tags:
            tags.append("latest")
        return tags

    def _compute_options(self) -> List[Dict[str, str]]:
        """Convert options dict into Repka options array.

        :returns: Array of objects with keys ``key`` and ``value``.
        :rtype: list[dict]
        """

        return [{"key": k, "value": v} for k, v in self._options.items()]

    @defer.inlineCallbacks
    def _render_release_name(self):
        """Render the release name through Buildbot renderer.

        :returns: Rendered release name.
        :rtype: str
        """

        assert self.build is not None
        name = yield self.build.render(self._release_name)
        defer.returnValue(name)

    @defer.inlineCallbacks
    def _get_credentials(self):
        """Render credentials for curl basic auth.

        :returns: Credentials string in the form ``user:password``.
        :rtype: str
        """

        assert self.build is not None
        creds = yield self.build.render(
            util.Interpolate(f"{USERNAME}:%(secret:buildbot_password)s")
        )
        defer.returnValue(creds)

    @defer.inlineCallbacks
    def _build_release_payload(
        self,
        *,
        packet_id: int,
        files: List[Dict[str, str]],
    ):
        """Build the request payload for release creation.

        :returns: JSON-serialized payload.
        :rtype: str
        """
        release_name = yield self._render_release_name()
        tags = self._compute_tags()
        options = self._compute_options()

        payload = {
            "packet": packet_id,
            "name": release_name,
            "files": files,
        }
        if self._release_description is not None:
            payload["description"] = self._release_description
        if tags:
            payload["tags"] = tags
        if options:
            payload["options"] = options

        json_payload = json.dumps(payload, ensure_ascii=False)
        defer.returnValue(json_payload)

    @defer.inlineCallbacks
    def _post_release(self, credentials: str, json_body: str):
        """Perform POST /api/release and return created release id.

        :raises _CurlFailedError: When curl command fails.
        :raises Exception: When response cannot be parsed.
        :returns: Release identifier from server response.
        :rtype: int
        """

        api_url = f"{ENDPOINT.rstrip('/')}/api/release"
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
            command=cmdline, collectStdout=True, logEnviron=False
        )
        yield self.runCommand(cmd)

        if cmd.didFail():
            raise _CurlFailedError("curl POST /api/release failed")

        stdout_text = cmd.stdout if cmd.stdout else ""
        response = json.loads(stdout_text.strip())
        release_id = response["id"]
        defer.returnValue(release_id)

    def _save_release_id(self, release_id: int) -> bool:
        """Save release id into build property.

        :returns: True on success, False otherwise.
        :rtype: bool
        """

        try:
            self.setProperty("repka_release_id", release_id, "RepkaCreateRelease")
            return True
        except Exception:
            self.addCompleteLog(
                "repka-release-error",
                "Failed to set property repka_release_id\n",
            )
            return False

    @defer.inlineCallbacks
    def _add_package_url(self, packet_id: int):
        """Add a link to the Repka package page to the build summary."""

        yield self.addURL(
            "Package in Repka", f"{ENDPOINT.rstrip('/')}/packet/{packet_id}"
        )

    @defer.inlineCallbacks
    def _fetch_release_files(self, credentials: str, release_id: int):
        """Fetch release object and return its files array.

        :raises _CurlFailedError: When curl GET fails.
        :raises Exception: When response cannot be parsed or malformed.
        :returns: List of file descriptors from release object.
        :rtype: list[dict]
        """

        api_release_url = f"{ENDPOINT.rstrip('/')}/api/release/{release_id}"
        cmdline = [
            "curl",
            "-sS",
            "-fL",
            "-k",
            "-u",
            credentials,
            "-H",
            "Accept: application/json",
            api_release_url,
        ]

        cmd = yield self.makeRemoteShellCommand(
            command=cmdline, collectStdout=True, logEnviron=False
        )
        yield self.runCommand(cmd)

        if cmd.didFail():
            raise _CurlFailedError("curl GET /api/release/{id} failed")

        stdout_text = cmd.stdout if cmd.stdout else ""
        response = json.loads(stdout_text.strip())
        files_array = response.get("files", [])
        if not isinstance(files_array, list):
            raise ValueError("field 'files' is not a list")
        defer.returnValue(files_array)

    @defer.inlineCallbacks
    def _add_file_urls(self, files_array: List[dict]):
        """Add download URLs for each file in the release."""
        for file_obj in files_array:
            file_id = file_obj.get("id")
            file_name = file_obj.get("name")
            file_size = file_obj.get("size", 0)

            url_name = f"{file_name} ({human_readable_size(file_size)}) "

            if not file_id or not file_name:
                self.addCompleteLog(
                    "repka-release-error",
                    f"Skipping invalid file entry: {file_obj}\n",
                )
                continue

            download_url = f"{ENDPOINT.rstrip('/')}/api/asset/{file_id}/download"
            yield self.addURL(url_name, download_url)


class _CurlFailedError(Exception):
    """Internal exception indicating curl command failure."""

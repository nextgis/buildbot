"""
This module defines the Buildbot configuration for automating the creation of a Flathub sideload repository.

The process includes:
- Adding and configuring the Flathub remote repository.
- Downloading required Flatpak runtime dependencies.
- Creating and zipping a sideload repository.
- Adding a helper script for dependency installation.
- Uploading the repository and creating a release in Repka.

This configuration simplifies the deployment of Flatpak packages in offline environments.
"""

from typing import Any, Dict

from buildbot.plugins import schedulers, steps, util

from nextgis_buildbot import renderers
from nextgis_buildbot.steps.repka import RepkaCreateRelease, RepkaUpload

BUILDER_NAME = "flathub_sideload_repo"

RUNTIME_DEPENDENCIES = [
    "org.freedesktop.Platform.GL.default/x86_64/24.08",
    "org.freedesktop.Platform.GL.default/x86_64/24.08extra",
    # "org.freedesktop.Platform.openh264/x86_64/2.5.1",
    "org.kde.Platform/x86_64/5.15-24.08",
    "org.kde.Platform.Locale/x86_64/5.15-24.08",
    "org.kde.KStyle.Adwaita/x86_64/5.15-24.08",
    "org.gtk.Gtk3theme.Breeze/x86_64/3.22",
]

SIDELOAD_REPO_NAME = "flathub-sideload-repo"
SIDELOAD_SCRIPT_NAME = "install_dependencies.sh"
SIDELOAD_SCRIPT_CONTENT = """#!/usr/bin/env bash
set -euo pipefail

# Get absolute path to the directory containing this script
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse --user argument
user_arg=""
if [[ "$1" == "--user" ]]; then
    user_arg="--user"
fi

flatpak remote-add ${user_arg} --if-not-exists flathub "${REPO_DIR}/flathub.flatpakrepo"
flatpak remote-modify ${user_arg} --collection-id=org.flathub.Stable flathub

flatpak install ${user_arg} --assumeyes --sideload-repo="${REPO_DIR}/.ostree/repo/" flathub """
SIDELOAD_SCRIPT_CONTENT += " ".join(RUNTIME_DEPENDENCIES) + "\n"

PACKAGE_ID = 174


def make_sideload_repo_factory():
    """
    Create a BuildFactory for generating a Flathub sideload repository.

    Steps include:
    - Ensuring the Flathub repository is configured.
    - Creating a directory for the sideload repository.
    - Downloading runtime dependencies.
    - Adding a helper script for installing dependencies.
    - Zipping the repository for easy distribution.
    - Uploading the repository to Repka and creating a release.

    :returns: Configured BuildFactory for the sideload repository.
    :rtype: BuildFactory
    """

    factory = util.BuildFactory()

    # Ensure Flathub repo
    factory.addStep(
        steps.ShellSequence(
            name="Ensure Flathub repo",
            commands=[
                # Add the Flathub remote repository if it doesn't exist
                util.ShellArg(
                    command=[
                        "flatpak",
                        "remote-add",
                        "--user",
                        "--if-not-exists",
                        "flathub",
                        "https://flathub.org/repo/flathub.flatpakrepo",
                    ],
                ),
                # Modify the Flathub repository to set the collection ID
                util.ShellArg(
                    command=[
                        "flatpak",
                        "remote-modify",
                        "--user",
                        "--collection-id=org.flathub.Stable",
                        "flathub",
                    ],
                ),
            ],
        ),
    )

    # Make directory
    factory.addStep(
        steps.MakeDirectory(
            name="Make sideload repo directory", dir=f"build/{SIDELOAD_REPO_NAME}"
        )
    )

    # Download dependencies
    for dependency in RUNTIME_DEPENDENCIES:
        step_name = "Download "
        full_name_len = len(step_name + dependency)
        max_name_len = 50
        if full_name_len <= max_name_len:
            step_name += dependency
        else:
            stripped_dependency = "…" + dependency[full_name_len - max_name_len + 1 :]
            step_name += stripped_dependency

        factory.addStep(
            steps.ShellSequence(
                name=step_name,
                commands=[
                    util.ShellArg(
                        command=[
                            "flatpak",
                            "install",
                            "--assumeyes",
                            "--user",
                            "flathub",
                            dependency,
                        ],
                        logname="install",
                    ),
                    util.ShellArg(
                        command=[
                            "flatpak",
                            "create-usb",
                            "--user",
                            SIDELOAD_REPO_NAME,
                            dependency,
                        ],
                        logname="create-usb",
                    ),
                ],
                haltOnFailure=True,
            ),
        )

    # Download flathub link
    factory.addStep(
        steps.ShellCommand(
            name="Download flathub.flatpakrepo",
            command=[
                "curl",
                "-o",
                f"{SIDELOAD_REPO_NAME}/flathub.flatpakrepo",
                "https://dl.flathub.org/repo/flathub.flatpakrepo",
            ],
            haltOnFailure=True,
        )
    )

    # Add helper script
    factory.addStep(
        steps.StringDownload(
            SIDELOAD_SCRIPT_CONTENT,
            workerdest=f"{SIDELOAD_REPO_NAME}/{SIDELOAD_SCRIPT_NAME}",
            name="Add install script",
            haltOnFailure=True,
        )
    )

    # Set mode
    factory.addStep(
        steps.ShellCommand(
            name="Set script executable",
            command=[
                "chmod",
                "+x",
                f"{SIDELOAD_REPO_NAME}/{SIDELOAD_SCRIPT_NAME}",
            ],
            haltOnFailure=True,
        )
    )

    # Zip repo
    factory.addStep(
        steps.ShellCommand(
            name="Zip sideload repo",
            command=[
                "zip",
                "-r",
                "-9",
                f"{SIDELOAD_REPO_NAME}.zip",
                SIDELOAD_REPO_NAME,
            ],
            haltOnFailure=True,
        )
    )

    # Upload artifacts
    factory.addStep(
        RepkaUpload(
            name="Upload sideload repo to Repka",
            files=f"{SIDELOAD_REPO_NAME}.zip",
        )
    )

    # Create Repka release
    version = util.Interpolate(
        "%(kw:year)s.%(kw:month)s.%(kw:day)s",
        year=renderers.current_year,
        month=renderers.current_month,
        day=renderers.current_day,
    )
    factory.addStep(
        RepkaCreateRelease(
            name="Create Repka release for sideload repo",
            packet=PACKAGE_ID,
            release_name=version,
            release_description="Sideload repository for Flathub Flatpak packages.",
            tags=["sideload-repo", "flatpak"],
            mark_latest=True,
        )
    )

    return factory


def make_config() -> Dict[str, Any]:
    """
    Create the Buildbot configuration for the Flathub sideload repository.

    :returns: Configuration dictionary for Buildbot.
    :rtype: dict
    """

    builders = [
        util.BuilderConfig(
            name=BUILDER_NAME,
            workernames=["flatpak"],
            factory=make_sideload_repo_factory(),
            collapseRequests=True,
            description="Build sideload repo for flathub",
            tags=["linux", "flatpak"],
        )
    ]

    schedulers_list = [
        schedulers.ForceScheduler(
            name=f"{BUILDER_NAME}_force_scheduler",
            label="Build Flathub Sideload Repo",
            buttonName="Build Flathub Sideload Repo",
            builderNames=[BUILDER_NAME],
            codebases=[util.CodebaseParameter(codebase="", hide=True)],
        )
    ]

    return {
        "builders": builders,
        "schedulers": schedulers_list,
    }

"""
This module defines the Buildbot configuration for creating a Flathub sideload repository.

The process includes:
- Ensuring the Flathub remote repository is added and configured.
- Downloading runtime dependencies.
- Generating a sideload repository with the required Flatpak packages.
- Adding a helper script for installing dependencies.
- Zipping the repository for distribution.
"""

from buildbot.plugins import schedulers, steps, util

BUILDER_NAME = "flathub_sideload_repo"

RUNTIME_DEPENDENCIES = [
    "org.freedesktop.Platform.GL.default//24.08",
    "org.freedesktop.Platform.GL.default//24.08extra",
    # "org.freedesktop.Platform.openh264//2.5.1",
    "org.kde.KStyle.Adwaita//5.15-24.08",
    "org.kde.Platform.Locale//5.15-24.08",
    "org.kde.Platform//5.15-24.08",
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


def make_sideload_repo_factory():
    factory = util.BuildFactory()

    # Ensure Flathub repo
    factory.addStep(
        steps.ShellSequence(
            name="Ensure Flathub repo",
            commands=[
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
    factory.addStep(steps.MakeDirectory(dir=f"build/{SIDELOAD_REPO_NAME}"))

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
                            "pwd",
                        ],
                        logname="pwd",
                    ),
                    util.ShellArg(command=["ls", "-la"], logname="ls"),
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
                            # "--allow-partial",
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
    # TODO

    return factory


# -------------------------
# Builders
# -------------------------

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


# -------------------------
# Schedulers
# -------------------------

schedulers_list = [
    schedulers.ForceScheduler(
        name=f"{BUILDER_NAME}_force_scheduler",
        label="Build Flathub Sideload Repo",
        buttonName="Build Flathub Sideload Repo",
        builderNames=[BUILDER_NAME],
    )
]


# -------------------------
# Config
# -------------------------

c = {
    "builders": builders,
    "schedulers": schedulers_list,
}

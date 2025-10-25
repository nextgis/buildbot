from dataclasses import dataclass
from typing import Any, Dict, Optional

from buildbot.plugins import schedulers, steps, util

from nextgis_buildbot.steps.repka import RepkaCreateRelease, RepkaUpload


@dataclass
class FlatpakApplication:
    name: str
    app_id: str
    git: str
    repka_bundle_repository: int
    check_lib_updates: bool = False

    pre_build_step: Optional[Any] = None  # Optional[steps.BuildStep]

    @property
    def manifest_file(self) -> str:
        return f"{self.app_id}.yaml"

    @property
    def bundle_file(self) -> str:
        return f"{self.app_id}.flatpak"

    @property
    def short_name(self) -> str:
        return self.app_id.lower().split(".")[-1]


APPLICATIONS = [
    FlatpakApplication(
        name="NextGIS QGIS",
        app_id="com.nextgis.ngqgis",
        git="git@gitlab.com:nextgis/com.nextgis.ngqgis.git",
        repka_bundle_repository=173,
    ),
    FlatpakApplication(
        name="NextGIS Formbuilder",
        app_id="com.nextgis.Formbuilder",
        git="git@gitlab.com:nextgis/com.nextgis.Formbuilder.git",
        repka_bundle_repository=172,
    ),
]

RUNTIME_REPO = "https://flatpak.nextgis.com/repo/nextgis.flatpakrepo"


def make_build_factory(application: FlatpakApplication):
    factory = util.BuildFactory()

    # Add SSH host configuration for gitlab.com using ssh-keyscan
    factory.addStep(
        steps.ShellCommand(
            name="Add gitlab.com to known_hosts",
            command=[
                "bash",
                "-c",
                "ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts",
            ],
            haltOnFailure=False,
            logEnviron=False,
        )
    )

    # Fetch code
    factory.addStep(
        steps.Git(
            repourl=application.git,
            branch=util.Property("git_branch", default="master"),
            mode="full",
            shallow=True,
        )
    )

    # Initialize GPG for signing Flatpak bundles
    factory.addStep(
        steps.ShellSequence(
            name="Initialise GPG",
            commands=[
                util.ShellArg(command=["gpg", "--list-keys", "--with-keygrip"]),
                util.ShellArg(
                    command=[
                        "bash",
                        "-c",
                        "echo 'allow-preset-passphrase' >> /root/.gnupg/gpg-agent.conf",
                    ],
                ),
                util.ShellArg(
                    command=["gpg-connect-agent", "reloadagent", "/bye"],
                ),
                util.ShellArg(
                    command=[
                        "bash",
                        "-c",
                        util.Interpolate(
                            "cat '%(secret:flatpak_gpg_passphrase)s' | /usr/libexec/gpg-preset-passphrase --preset '%(prop:flatpak_gpg_key_grep)s'"
                        ),
                    ],
                ),
                util.ShellArg(
                    command=[
                        "gpg",
                        "--import",
                        "--batch",
                        util.Secret("gpg_private_key"),
                    ],
                ),
            ],
            haltOnFailure=True,
        )
    )

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

    # Build Flatpak
    factory.addStep(
        steps.ShellCommand(
            name="Build Flatpak",
            command=[
                "flatpak-builder",
                "build",
                "--user",
                "--install-deps-from=flathub",
                util.Interpolate("--gpg-sign=%(prop:flatpak_gpg_key_id)s"),
                "--disable-rofiles-fuse",
                "--disable-updates",
                "--force-clean",
                "--repo=repo",
                util.Interpolate("--branch=%(prop:flatpak_branch)s"),
                application.manifest_file,
            ],
        ),
    )

    # Build bundle
    factory.addStep(
        steps.ShellCommand(
            name="Bundle Flatpak",
            command=[
                "flatpak",
                "build-bundle",
                util.Interpolate("--gpg-sign=%(prop:flatpak_gpg_key_id)s"),
                "repo",
                application.bundle_file,
                f"--runtime-repo={RUNTIME_REPO}",
                application.app_id,
                util.Interpolate("%(prop:flatpak_branch)s"),
            ],
        )
    )

    # Upload bundle to Repka and create release
    short_name = application.app_id.lower().split(".")[-1]
    factory.addStep(
        RepkaUpload(
            name=f"Upload {short_name} Flatpak bundle to Repka",
            files=application.bundle_file,
        )
    )
    factory.addStep(
        RepkaCreateRelease(
            name=f"Create Repka release for {short_name} bundle",
            packet=application.repka_bundle_repository,
            release_name="test",
            release_description="test",
            tags=["flatpak", "bundle"],
            mark_latest=True,
        )
    )

    return factory


def build_config_name(application: FlatpakApplication) -> str:
    return f"flatpak_{application.short_name}_builder"


def make_config() -> Dict[str, Any]:
    """
    Create the Buildbot configuration.

    :returns: Configuration dictionary for Buildbot.
    :rtype: dict
    """
    builders = [
        util.BuilderConfig(
            name=build_config_name(application),
            workernames=["flatpak"],
            factory=make_build_factory(application),
            collapseRequests=True,
            description=f"{application.app_id} flatpak application builder",
            tags=["linux", "flatpak"],
        )
        for application in APPLICATIONS
    ]

    schedulers_list = [
        schedulers.ForceScheduler(
            name=f"flatpak_{application.short_name}_force_scheduler",
            label=f"Build {application.app_id} flatpak",
            buttonName=f"Build {application.app_id} flatpak",
            builderNames=[build_config_name(application)],
            properties=[
                util.StringParameter(
                    name="git_branch", label="git branch", default="master"
                ),
                util.ChoiceStringParameter(
                    name="flatpak_branch",
                    label="Flatpak branch",
                    choices=["stable", "dev"],
                    default="stable",
                ),
            ],
            codebases=[util.CodebaseParameter(codebase="", hide=True)],
        )
        for application in APPLICATIONS
    ]

    return {
        "builders": builders,
        "schedulers": schedulers_list,
    }

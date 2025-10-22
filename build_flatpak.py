from dataclasses import dataclass
from typing import Any, Optional

from buildbot.plugins import schedulers, steps, util


@dataclass
class FlatpakApplication:
    name: str
    app_id: str
    git: str
    check_lib_updates: bool = False

    pre_build_step: Optional[Any] = None  # Optional[steps.BuildStep]

    @property
    def manifest_file(self) -> str:
        return f"{self.app_id}.yaml"

    @property
    def bundle_file(self) -> str:
        return f"{self.app_id}.flatpak"

APPLICATIONS = [
    FlatpakApplication(
        name="NextGIS QGIS",
        app_id="com.nextgis.ngqgis",
        git="git@gitlab.com:nextgis/com.nextgis.ngqgis.git",
    ),
    FlatpakApplication(
        name="NextGIS Formbuilder",
        app_id="com.nextgis.Formbuilder",
        git="git@gitlab.com:nextgis/com.nextgis.Formbuilder.git",
    ),
]

RUNTIME_REPO = "https://flatpak.nextgis.com/repo/nextgis.flatpakrepo"

def make_build_factory(application: FlatpakApplication):
    factory = util.BuildFactory()

    # Fetch code
    factory.addStep(
        steps.Git(
            repourl=application.git,
            branch=util.Property("GIT_BRANCH", default="master"),
            mode="full",
            shallow=True,
        )
    )

    # Initialize GPG for signing Flatpak bundles
    factory.addStep(
        steps.ShellSequence(
            name="Initialise GPG",
            commands=[
                util.ShellArg(
                    command=["gpg", "--list-keys", "--with-keygrip"],
                ),
                util.ShellArg(
                    command=[
                        "bash",
                        "-c",
                        "echo 'allow-preset-passphrase' >> ~/.gnupg/gpg-agent.conf",
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
                            "cat '%(secret:flatpak_gpg_passphrase)s' | /usr/libexec/gpg-preset-passphrase --preset '%(secret:flatpak_gpg_key_grep)s'"
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

    # Build Flatpak
    factory.addStep(
        steps.ShellCommand(
            name="Build Flatpak",
            command=[
                "flatpak-builder",
                "build",
                "--user",
                "--disable-updates",
                "--disable-rofiles-fuse",
                "--force-clean",
                "--repo=repo",
                util.Interpolate("--gpg-sign=%(secret:flatpak_gpg_key_id)s"),
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
                util.Interpolate("--gpg-sign=%(secret:flatpak_gpg_key_id)s"),
                "repo",
                application.bundle_file,
                f"--runtime-repo={RUNTIME_REPO}",
                application.app_id,
                # branch
            ],
        )
    )

    return factory


# -------------------------
# Builders
# -------------------------
def builder_name(application: FlatpakApplication) -> str:
    return application.name + " Flatpak"


builders = [
    util.BuilderConfig(
        name=builder_name(application),
        workernames=["flatpak"],
        factory=make_build_factory(application),
        collapseRequests=True,
        description=f"Build {application.app_id} flatpak",
        tags=["flatpak", "linux"],
    )
    for application in APPLICATIONS
]


# -------------------------
# Schedulers
# -------------------------

schedulers_list = [
    schedulers.ForceScheduler(
        name="force",
        builderNames=[builder_name(application)],
        properties=[
            util.StringParameter(
                name="GIT_BRANCH", label="git branch", default="master"
            ),
            util.ChoiceStringParameter(
                name="FLATPAK_BRANCH",
                label="Flatpak branch",
                choices=["stable", "beta", "dev"],
                default="stable",
            ),
        ],
    )
    for application in APPLICATIONS
]


# -------------------------
# Config
# -------------------------
c = {
    "builders": builders,
    "schedulers": schedulers_list,
}

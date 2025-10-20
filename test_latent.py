# -*- python -*-
# ex: set syntax=python:

from buildbot.plugins import schedulers, steps, util

VM_CPU_COUNT = 6

MAC_OS_MIN_VERSION = "10.11"
MAC_OS_SDKS_PATH = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"

c = {}
c["change_source"] = []
c["schedulers"] = []
c["builders"] = []

platforms = [
    {"name": "nix", "worker": "build-nix"},
]

project_name = "test_latent"

builderNames = []
for platform in platforms:
    builderNames.append(project_name + "_" + platform["name"])


forceScheduler = schedulers.ForceScheduler(
    name=project_name + "_force",
    label="Force build",
    buttonName="Force build",
    builderNames=builderNames,
)
c["schedulers"].append(forceScheduler)
for platform in platforms:
    factory = util.BuildFactory()
    factory.addStep(
        steps.ShellCommand(command=["cmake", "--help"], name="help", haltOnFailure=True)
    )
    factory.addStep(
        steps.ShellCommand(
            command=["cmake", "--version"], name="version", haltOnFailure=True
        )
    )

    builder = util.BuilderConfig(
        name=project_name + "_" + platform["name"],
        workernames=[platform["worker"]],
        factory=factory,
        description="Make {} on {}".format(project_name, platform["name"]),
    )

    c["builders"].append(builder)

from enum import IntEnum
from typing import Iterable, List


class RepkaRepository(IntEnum):
    # Borsch repo
    BORSCH = 2

    # QGIS repos
    QGIS_MAIN = 1
    QGIS_DEV = 10

    # Installer
    WIN32 = 4
    WIN64 = 5
    MACOS = 6
    SOFTWARE = 14
    IMAGES = 15

    # Ubuntu
    DEBIAN = 11


# Common
VM_CPU_COUNT = 8


# MacOS settings
MAC_OS_MIN_VERSION = "10.14"
MAC_OS_SDKS_PATH = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"


def create_tags(identifiers: Iterable[str]) -> List[str]:
    UBUNTU_DISTROS = ("focal", "bullseye", "jammy")
    ASTRA_DISTROS = ("astra",)
    LINUX_DISTROS = (*UBUNTU_DISTROS, *ASTRA_DISTROS)

    tags = []

    # Add result type
    for product in ("installer", "borsch", "deb"):
        if product in identifiers:
            tags.append(product)

    if any("win" in identifier for identifier in identifiers):
        tags.append("windows")
    elif any("mac" in identifier for identifier in identifiers):
        tags.append("macos")
    else:
        for identifier in identifiers:
            if identifier not in LINUX_DISTROS:
                continue

            tags.append("linux")

            if identifier in UBUNTU_DISTROS:
                tags.extend(["ubuntu", identifier])
            elif identifier == "astra":
                tags.extend(["astra", "astra-17"])

            break

    if any("64" in identifier for identifier in identifiers):
        tags.append("x64")
    if any("static" in identifier for identifier in identifiers):
        tags.append("static")

    return tags

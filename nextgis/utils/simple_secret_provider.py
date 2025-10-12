from typing import Dict, Optional

from buildbot import config
from buildbot.secrets.providers.base import SecretProviderBase
from twisted.internet import defer


class SimpleSecretProvider(SecretProviderBase):
    """Provide secrets from an in-memory mapping.

    This provider returns secret values from a supplied dictionary rather
    than reading them from the filesystem.
    """

    name: Optional[str] = "SimpleSecretProvider"

    def checkConfig(self, secrets: Dict[str, str]) -> defer.Deferred[bool]:
        """
        Validate initial configuration arguments.

        :param secrets: Mapping of secret keys to their values.
        :type secrets: Dict[str, str]
        :raises buildbot.config.ConfigErrors: If the provided mapping is invalid.
        :return: Deferred indicating validation success.
        :rtype: Deferred[bool]
        """

        if not isinstance(secrets, dict):
            config.error("'secrets' must be a dict[str, str]")

        for key, value in secrets.items():
            if not isinstance(key, str):
                config.error("All secret keys must be of type 'str'")
            if not isinstance(value, str):
                config.error("All secret values must be of type 'str'")

        # Indicate successful validation.
        return defer.succeed(True)

    def reconfigService(self, secrets: Dict[str, str]) -> defer.Deferred[None]:
        """
        Apply configuration and make secrets available for retrieval.

        :param secrets: Mapping of secret keys to their values.
        :type secrets: Dict[str, str]
        :return: Deferred indicating reconfiguration completion.
        :rtype: Deferred[None]
        """

        # Keep an internal copy to avoid accidental external mutations.
        self.secrets = dict(secrets)

        # Indicate reconfiguration is complete.
        return defer.succeed(None)

    def get(self, entry: str):
        """
        Return a secret by key.

        :param entry: Secret key to look up.
        :type entry: str
        :return: Secret value if present, otherwise ``None``.
        :rtype: Optional[str]
        """
        return getattr(self, "secrets", {}).get(entry)


import os
from typing import Optional, Protocol


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> Optional[str]: ...


class EnvSecretProvider:
    """Secret provider that reads from environment variables."""

    def get_secret(self, name: str) -> Optional[str]:
        """Get secret value from environment variables.

        Args:
            name: Environment variable name

        Returns:
            Secret value or None if not found or empty
        """
        value = os.environ.get(name)
        if value is None or str(value).strip() == "":
            return None
        return value


_provider: SecretProvider = EnvSecretProvider()


def set_secret_provider(provider: SecretProvider) -> None:
    """Set the global secret provider for credential management.

    Args:
        provider: SecretProvider implementation to use for secret retrieval
    """
    global _provider
    _provider = provider


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return a secret with precedence: provider > default.

    Default provider reads from environment variables. Swap via set_secret_provider
    to integrate Vault/AWS/GCP secret managers without changing callers.
    """
    try:
        value = _provider.get_secret(name)
        if value is None or str(value).strip() == "":
            return default
        return value
    except Exception:
        return default

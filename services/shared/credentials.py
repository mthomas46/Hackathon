from __future__ import annotations

import os
from typing import Optional, Protocol


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> Optional[str]:
        ...


class EnvSecretProvider:
    def get_secret(self, name: str) -> Optional[str]:
        value = os.environ.get(name)
        if value is None or str(value).strip() == "":
            return None
        return value


_provider: SecretProvider = EnvSecretProvider()


def set_secret_provider(provider: SecretProvider) -> None:
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



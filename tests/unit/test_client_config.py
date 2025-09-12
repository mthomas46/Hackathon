"""Tests for ServiceClients env-configured timeouts/retries/circuit."""

import os
import pytest
from services.shared.clients import ServiceClients  # type: ignore


@pytest.mark.unit
def test_clients_env_overrides(monkeypatch):
    monkeypatch.setenv("HTTP_CLIENT_TIMEOUT", "15")
    monkeypatch.setenv("HTTP_RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("HTTP_RETRY_BASE_MS", "200")
    monkeypatch.setenv("HTTP_CIRCUIT_ENABLED", "true")
    c = ServiceClients(timeout=30)
    assert c.timeout == 15
    assert c.retry_attempts == 5
    assert c.retry_base_ms == 200
    assert c.circuit_enabled is True



from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from taiga.mcp_server import auth

# --- build_client -------------------------------------------------------------------------


@patch("taiga.mcp_server.auth.TaigaAPI")
def test_build_client_with_token(mock_taiga_api):
    credentials = auth.Credentials(host="https://example.com", token="tok", token_type="Bearer", tls_verify=False)

    result = auth.build_client(credentials)

    mock_taiga_api.assert_called_once_with(
        host="https://example.com", token="tok", token_type="Bearer", tls_verify=False
    )
    assert result is mock_taiga_api.return_value


@patch("taiga.mcp_server.auth.TaigaAPI")
def test_build_client_prefers_token_over_username_password(mock_taiga_api):
    credentials = auth.Credentials(token="tok", username="alice", password="secret")

    auth.build_client(credentials)

    mock_taiga_api.assert_called_once_with(
        host=auth.DEFAULT_HOST, token="tok", token_type=auth.DEFAULT_TOKEN_TYPE, tls_verify=True
    )
    mock_taiga_api.return_value.auth.assert_not_called()


@patch("taiga.mcp_server.auth.TaigaAPI")
def test_build_client_with_username_password(mock_taiga_api):
    mock_api = MagicMock()
    mock_taiga_api.return_value = mock_api
    credentials = auth.Credentials(host="https://example.com", username="alice", password="secret", tls_verify=True)

    result = auth.build_client(credentials)

    mock_taiga_api.assert_called_once_with(host="https://example.com", tls_verify=True)
    mock_api.auth.assert_called_once_with("alice", "secret")
    assert result is mock_api


def test_build_client_without_credentials_raises():
    credentials = auth.Credentials()

    with pytest.raises(auth.ConfigError, match="provide a token"):
        auth.build_client(credentials)


def test_build_client_with_only_username_raises():
    credentials = auth.Credentials(username="alice")

    with pytest.raises(auth.ConfigError, match="provide a token"):
        auth.build_client(credentials)


# --- configure ------------------------------------------------------------------------------


@patch("taiga.mcp_server.auth._client", "stale-client")
@patch("taiga.mcp_server.auth._credentials", None)
def test_configure_stores_credentials_and_resets_client():
    credentials = auth.Credentials(token="tok")

    auth.configure(credentials)

    assert auth._credentials is credentials
    assert auth._client is None


# --- get_client -----------------------------------------------------------------------------


@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials", None)
def test_get_client_without_configuration_raises():
    with pytest.raises(auth.ConfigError, match="not been configured"):
        auth.get_client()


@patch("taiga.mcp_server.auth.build_client")
@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials")
def test_get_client_builds_once_and_caches(mock_credentials, mock_build_client):
    mock_client = MagicMock()
    mock_build_client.return_value = mock_client

    first = auth.get_client()
    second = auth.get_client()

    assert first is mock_client
    assert second is mock_client
    mock_build_client.assert_called_once_with(mock_credentials)

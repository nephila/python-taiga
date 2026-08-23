from __future__ import annotations

import os
from unittest.mock import patch

from taiga.mcp_server import cli

# --- _env_bool ------------------------------------------------------------------------------


def test_env_bool_default_when_unset():
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("TAIGA_TLS_VERIFY", None)
        assert cli._env_bool("TAIGA_TLS_VERIFY", True) is True
        assert cli._env_bool("TAIGA_TLS_VERIFY", False) is False


def test_env_bool_falsy_values():
    for value in ("0", "false", "No", "OFF", " off "):
        with patch.dict("os.environ", {"TAIGA_TLS_VERIFY": value}):
            assert cli._env_bool("TAIGA_TLS_VERIFY", True) is False


def test_env_bool_truthy_values():
    for value in ("1", "true", "yes", "anything-else"):
        with patch.dict("os.environ", {"TAIGA_TLS_VERIFY": value}):
            assert cli._env_bool("TAIGA_TLS_VERIFY", False) is True


# --- main -----------------------------------------------------------------------------------


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_main_configures_from_token_argv(mock_configure, mock_mcp):
    exit_code = cli.main(["--host", "https://example.com", "--token", "tok", "--no-tls-verify"])

    assert exit_code == 0
    mock_configure.assert_called_once()
    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://example.com"
    assert credentials.token == "tok"
    assert credentials.tls_verify is False
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_main_configures_from_username_password_argv(mock_configure, mock_mcp):
    cli.main(["--username", "alice", "--password", "secret", "--tls-verify"])

    credentials = mock_configure.call_args.args[0]
    assert credentials.username == "alice"
    assert credentials.password == "secret"
    assert credentials.token is None
    assert credentials.tls_verify is True


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_main_reads_credentials_from_env(mock_configure, mock_mcp):
    env = {
        "TAIGA_HOST": "https://env.example.com",
        "TAIGA_TOKEN": "env-tok",
        "TAIGA_TOKEN_TYPE": "Basic",
    }
    with patch.dict("os.environ", env):
        cli.main([])

    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://env.example.com"
    assert credentials.token == "env-tok"
    assert credentials.token_type == "Basic"


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_main_falls_back_to_tls_verify_env_var(mock_configure, mock_mcp):
    with patch.dict("os.environ", {"TAIGA_TLS_VERIFY": "false"}):
        cli.main(["--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is False


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_main_defaults_tls_verify_true_without_env_or_flag(mock_configure, mock_mcp):
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("TAIGA_TLS_VERIFY", None)
        cli.main(["--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is True

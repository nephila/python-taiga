from __future__ import annotations

import os
from unittest.mock import patch

from typer.testing import CliRunner

from taiga.mcp_server import cli

runner = CliRunner()

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


# --- serve ------------------------------------------------------------------------------


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_configures_from_token_argv(mock_configure, mock_mcp):
    result = runner.invoke(cli.app, ["serve", "--host", "https://example.com", "--token", "tok", "--no-tls-verify"])

    assert result.exit_code == 0
    mock_configure.assert_called_once()
    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://example.com"
    assert credentials.token == "tok"
    assert credentials.tls_verify is False
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_configures_from_username_password_argv(mock_configure, mock_mcp):
    runner.invoke(cli.app, ["serve", "--username", "alice", "--password", "secret", "--tls-verify"])

    credentials = mock_configure.call_args.args[0]
    assert credentials.username == "alice"
    assert credentials.password == "secret"
    assert credentials.token is None
    assert credentials.tls_verify is True


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_reads_credentials_from_env(mock_configure, mock_mcp):
    env = {
        "TAIGA_HOST": "https://env.example.com",
        "TAIGA_TOKEN": "env-tok",
        "TAIGA_TOKEN_TYPE": "Basic",
    }
    with patch.dict("os.environ", env):
        result = runner.invoke(cli.app, ["serve"])

    assert result.exit_code == 0
    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://env.example.com"
    assert credentials.token == "env-tok"
    assert credentials.token_type == "Basic"


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_falls_back_to_tls_verify_env_var(mock_configure, mock_mcp):
    with patch.dict("os.environ", {"TAIGA_TLS_VERIFY": "false"}):
        runner.invoke(cli.app, ["serve", "--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is False


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_defaults_tls_verify_true_without_env_or_flag(mock_configure, mock_mcp):
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("TAIGA_TLS_VERIFY", None)
        runner.invoke(cli.app, ["serve", "--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is True


# --- list-tools ---------------------------------------------------------------------------


def test_list_tools_lists_all_tool_names():
    result = runner.invoke(cli.app, ["list-tools"])

    assert result.exit_code == 0
    assert "whoami" in result.output
    assert "list_user_stories" in result.output
    assert "create_issue" in result.output


def test_list_tools_default_excludes_schema():
    result = runner.invoke(cli.app, ["list-tools"])

    assert result.exit_code == 0
    assert '"properties"' not in result.output


def test_list_tools_verbose_includes_schema():
    result = runner.invoke(cli.app, ["list-tools", "--verbose"])

    assert result.exit_code == 0
    assert '"properties"' in result.output


# --- bare invocation (breaking change) ---------------------------------------------------


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_bare_invocation_no_longer_serves(mock_configure, mock_mcp):
    result = runner.invoke(cli.app, [])

    assert "serve" in result.output
    mock_configure.assert_not_called()
    mock_mcp.run.assert_not_called()


# --- --version --------------------------------------------------------------------------


def test_version_flag_prints_version_and_exits():
    from taiga import __version__

    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output

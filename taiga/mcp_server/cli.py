# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

import os

import typer

from .. import __version__
from .auth import DEFAULT_HOST, DEFAULT_TOKEN_TYPE, Credentials, configure

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Taiga MCP server & CLI.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"taiga-mcp-server (python-taiga {__version__})")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool | None = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show the version and exit."
    ),
) -> None:
    """Taiga MCP server & CLI."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def _resolve_credentials(
    host: str | None,
    token: str | None,
    token_type: str | None,
    username: str | None,
    password: str | None,
    tls_verify: bool | None,
) -> Credentials:
    return Credentials(
        host=host or os.environ.get("TAIGA_HOST", DEFAULT_HOST),
        tls_verify=_env_bool("TAIGA_TLS_VERIFY", True) if tls_verify is None else tls_verify,
        token=token or os.environ.get("TAIGA_TOKEN"),
        token_type=token_type or os.environ.get("TAIGA_TOKEN_TYPE", DEFAULT_TOKEN_TYPE),
        username=username or os.environ.get("TAIGA_USERNAME"),
        password=password or os.environ.get("TAIGA_PASSWORD"),
    )


HostOption = typer.Option(None, help="Taiga instance host (default: TAIGA_HOST env var, or https://api.taiga.io).")
TokenOption = typer.Option(None, help="Taiga auth token (default: TAIGA_TOKEN env var).")
TokenTypeOption = typer.Option(None, help="Type of the auth token (default: TAIGA_TOKEN_TYPE env var, or Bearer).")
UsernameOption = typer.Option(None, help="Taiga username (default: TAIGA_USERNAME env var).")
PasswordOption = typer.Option(None, help="Taiga password (default: TAIGA_PASSWORD env var).")
TlsVerifyOption = typer.Option(
    None,
    "--tls-verify/--no-tls-verify",
    help="Verify TLS certificates (default: TAIGA_TLS_VERIFY env var, or true).",
)


@app.command()
def serve(
    host: str | None = HostOption,
    token: str | None = TokenOption,
    token_type: str | None = TokenTypeOption,
    username: str | None = UsernameOption,
    password: str | None = PasswordOption,
    tls_verify: bool | None = TlsVerifyOption,
) -> None:
    """Run the MCP server over stdio.

    Credentials can be passed as flags or read from the TAIGA_HOST/TAIGA_TOKEN
    or TAIGA_HOST/TAIGA_USERNAME/TAIGA_PASSWORD environment variables. Passing
    --token/--password on the command line can expose them via the process
    list; prefer the environment variables where possible.
    """
    configure(_resolve_credentials(host, token, token_type, username, password, tls_verify))

    from .server import mcp

    mcp.run(transport="stdio")


def main() -> None:
    """Entry point for the ``taiga-mcp-server`` console script."""
    app()


if __name__ == "__main__":
    main()

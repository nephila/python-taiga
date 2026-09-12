# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

from dataclasses import dataclass

from ..client import TaigaAPI
from ..exceptions import TaigaException

DEFAULT_HOST = "https://api.taiga.io"
DEFAULT_TOKEN_TYPE = "Bearer"


class ConfigError(TaigaException):
    """Raised when there isn't enough information to authenticate, or the server wasn't configured."""


@dataclass
class Credentials:
    host: str = DEFAULT_HOST
    tls_verify: bool = True
    token: str | None = None
    token_type: str = DEFAULT_TOKEN_TYPE
    username: str | None = None
    password: str | None = None


def build_client(credentials: Credentials) -> TaigaAPI:
    """
    Build and authenticate a :class:`TaigaAPI` client from the given credentials.

    A token takes precedence over username/password if both are set.
    """
    if credentials.token:
        return TaigaAPI(
            host=credentials.host,
            token=credentials.token,
            token_type=credentials.token_type,
            tls_verify=credentials.tls_verify,
        )

    if credentials.username and credentials.password:
        api = TaigaAPI(host=credentials.host, tls_verify=credentials.tls_verify)
        api.auth(credentials.username, credentials.password)
        return api

    raise ConfigError("Missing Taiga credentials: provide a token, or both a username and a password.")


_credentials: Credentials | None = None
_client: TaigaAPI | None = None


def configure(credentials: Credentials) -> None:
    """Store the credentials used to lazily build the Taiga client on first use."""
    global _credentials, _client
    _credentials = credentials
    _client = None


def get_client() -> TaigaAPI:
    """Return a lazily-built, process-wide :class:`TaigaAPI` client."""
    global _client
    if _client is None:
        if _credentials is None:
            raise ConfigError("The Taiga MCP server has not been configured with any credentials.")
        _client = build_client(_credentials)
    return _client

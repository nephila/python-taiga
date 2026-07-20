# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

import argparse
import os
import sys

from .. import __version__
from .auth import DEFAULT_HOST, DEFAULT_TOKEN_TYPE, Credentials, configure


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``taiga-mcp-server`` console script."""
    parser = argparse.ArgumentParser(
        prog="taiga-mcp-server",
        description=(
            "Run a Model Context Protocol server exposing python-taiga over stdio. "
            "Credentials can be passed as arguments or read from the TAIGA_HOST/TAIGA_TOKEN or "
            "TAIGA_HOST/TAIGA_USERNAME/TAIGA_PASSWORD environment variables. "
            "Passing --token/--password on the command line can expose them via the process list; "
            "prefer the environment variables where possible."
        ),
    )
    parser.add_argument("--version", action="version", version=f"taiga-mcp-server (python-taiga {__version__})")
    parser.add_argument(
        "--host", default=os.environ.get("TAIGA_HOST", DEFAULT_HOST), help="Taiga instance host (default: %(default)s)"
    )
    parser.add_argument("--token", default=os.environ.get("TAIGA_TOKEN"), help="Taiga auth token")
    parser.add_argument(
        "--token-type",
        default=os.environ.get("TAIGA_TOKEN_TYPE", DEFAULT_TOKEN_TYPE),
        help="Type of the auth token (default: %(default)s)",
    )
    parser.add_argument("--username", default=os.environ.get("TAIGA_USERNAME"), help="Taiga username")
    parser.add_argument("--password", default=os.environ.get("TAIGA_PASSWORD"), help="Taiga password")
    tls_group = parser.add_mutually_exclusive_group()
    tls_group.add_argument(
        "--tls-verify", dest="tls_verify", action="store_true", default=None, help="Verify TLS certificates"
    )
    tls_group.add_argument(
        "--no-tls-verify", dest="tls_verify", action="store_false", help="Do not verify TLS certificates"
    )
    args = parser.parse_args(argv)

    tls_verify = _env_bool("TAIGA_TLS_VERIFY", True) if args.tls_verify is None else args.tls_verify

    configure(
        Credentials(
            host=args.host,
            tls_verify=tls_verify,
            token=args.token,
            token_type=args.token_type,
            username=args.username,
            password=args.password,
        )
    )

    from .server import mcp

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
